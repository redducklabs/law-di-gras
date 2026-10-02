"""Assemble the cached Dashboard: index → extract → map → brief.

Cache key = hash of every source content_hash for the matter + pipeline
version. Unchanged case → the stored Dashboard is returned without any call.
"""

import hashlib
import re
from datetime import date, datetime, timezone

from rapidfuzz import fuzz

from app.config import CASE_VALUE_MULTIPLIER_HIGH, CASE_VALUE_MULTIPLIER_LOW
from app.db import connect
from app.digest import structured as st
from app.digest.spans import locate
from app.digest.brief import write_brief
from app.digest.curate import mark_milestones, recent_activity
from app.digest.conflicts import check_statements
from app.digest.extract import PROMPT_VERSION, Extracted, extract_all, save_facts, verify_values
from app.digest.verify import _MONEY, _money_val
from app.retrieval.embed import embed_matter
from app.retrieval.hyde import hyde_matter
from app.retrieval.search import warm
from app.schemas import (ActionItem, Dashboard, Fact, Kpis, MatterSummary, TimelineEvent, TreatmentLine)

# Bump PIPELINE_REV on every change that alters the Dashboard. A server never overwrites a dashboard
# cached by a newer rev (a stale server that missed a pull serves it as-is instead).
PIPELINE_REV = 21
PIPELINE_VERSION = f"r{PIPELINE_REV}-{PROMPT_VERSION}"


def _rev_of(input_hash: str | None) -> int:
    m = re.match(r"r(\d+):", input_hash or "")
    return int(m.group(1)) if m else 0


def _cached_row(matter_id: str):
    with connect() as conn:
        return conn.execute("SELECT input_hash, payload_json FROM digests WHERE matter_id = ? AND kind = 'dashboard'",
                            (matter_id,)).fetchone()


def input_hash(matter_id: str) -> str:
    with connect() as conn:
        rows = conn.execute("SELECT id, content_hash FROM sources WHERE matter_id = ? ORDER BY id",
                            (matter_id,)).fetchall()
    h = hashlib.sha256(f"{PIPELINE_VERSION}|value:{VALUE_LOW_X:g}-{VALUE_HIGH_X:g}".encode())
    for r in rows:
        h.update(f"{r[0]}={r[1]};".encode())
    return f"r{PIPELINE_REV}:{h.hexdigest()}"


def matter_summary(matter_id: str) -> MatterSummary | None:
    with connect() as conn:
        m = conn.execute("SELECT * FROM matters WHERE id = ?", (matter_id,)).fetchone()
    if not m:
        return None
    return MatterSummary(id=m["id"], display_number=m["display_number"] or "",
                         title=m["description"] or m["display_number"] or "", client_name=m["client_name"] or "",
                         client_photo_url=m["client_photo_url"], status=m["status"] or "",
                         opened_date=st.iso(m["opened_date"]))


def cached(matter_id: str) -> Dashboard | None:
    with connect() as conn:
        row = conn.execute("SELECT payload_json FROM digests WHERE matter_id = ? AND kind = 'dashboard'",
                           (matter_id,)).fetchone()
    return Dashboard.model_validate_json(row["payload_json"]) if row else None


def _fact(x: Extracted, fid: str) -> Fact:
    return Fact(id=fid, label=x.label, value=x.value, amount=x.amount, date=st.iso(x.date),
                citations=x.citations, verified=x.verified)


def _name_sim(a: str, b: str) -> float:
    a, b = a.replace("/", " "), b.replace("/", " ")
    return max(fuzz.token_set_ratio(a, b), fuzz.partial_ratio(a.lower(), b.lower()))


VALUE_LOW_X, VALUE_HIGH_X = CASE_VALUE_MULTIPLIER_LOW, CASE_VALUE_MULTIPLIER_HIGH  # firm setting (.env)
_LIABILITY = re.compile(r"liabil|bodily|(?<![a-z])bi(?![a-z])", re.I)
_UNCAPPED = re.compile(r"self[- ]insured|no stated limit|unlimited", re.I)


def _round5k(x: float) -> float:
    return round(x / 5000) * 5000


_LIMITATIONS = re.compile(r"limitation", re.I)
_FILED = re.compile(r"complaint|summons|action commenced|commenced|suit filed|lawsuit|filed|index no", re.I)


def _suit_filed_before(ex: dict[str, list[Extracted]], deadline: str) -> Extracted | None:
    """The earliest verified filing/commencement event on or before the deadline, if the record shows one."""
    hits = [x for cat in ("key_dates", "stage") for x in ex.get(cat, [])
            if x.date and x.verified and x.date <= deadline and (x.status in (None, "occurred"))
            and _FILED.search(f"{x.label} {x.value}") and not _LIMITATIONS.search(x.label)]
    return min(hits, key=lambda x: x.date) if hits else None


_FILED_STAMP = re.compile(r"FILED:?[^\n]{0,40}?(\d{1,2}/\d{1,2}/\d{4})")
_PERSON = re.compile(r"(?:Dr\.?\s+)?([A-Z][a-z]+(?:\s+[A-Z]\.)?\s+([A-Z][a-z]{2,}))")


def _filed_before(matter_id: str, e: TimelineEvent):
    """(filed date, citation of the stamp) for a filed document naming this event's person, stamped
    before the event's calendar date; None otherwise."""
    from app.retrieval.search import search_hits
    m = _PERSON.search(e.label.removeprefix("Calendar: ").split(",", 1)[-1])
    if not m:
        return None
    surname = m.group(2)
    with connect() as conn:
        for h in search_hits(matter_id, e.label.removeprefix("Calendar: "), top_k=6):
            if h.kind != "document" or surname.lower() not in (h.title + " " + h.text).lower():
                continue
            s = _FILED_STAMP.search(h.text)
            if not s:
                continue
            mm, dd, yy = s.group(1).split("/")
            filed = f"{yy}-{int(mm):02d}-{int(dd):02d}"
            if filed < e.date:
                c = locate(conn, h.source_id, s.group(0), h.page_no)
                if c and c.verified:
                    return filed, c
    return None


def _apply_finding(f: Fact, v, cit, injury: bool = False, bullet: bool = False) -> None:
    """Make a whole-record conflict or caveat visible on the fact, citing the other source too."""
    if cit is None or v.verdict not in ("contradicted", "qualified"):
        return
    note = v.note.strip().rstrip(".")
    if cit.model_dump() not in [c.model_dump() for c in f.citations]:
        f.citations = list(f.citations) + [cit]
    if v.verdict == "contradicted":
        if bullet:
            if "conflict" not in f.value.lower():  # the bullet may already state the conflict itself
                f.value = f"{f.value} (Conflict: {note})"
        elif injury:
            f.label = f"Disputed: {f.label}"
            f.value = f"{f.value} Disputed: {note}."
        else:
            f.value = f"Conflict: {f.value} vs {note}"
    elif not bullet:  # caveats go after the value, never in the (short) label
        f.value = f"{f.value} · Note: {note}"


def _usd(x: float) -> str:
    return f"${x:,.2f}".removesuffix(".00")


def value_range(specials: Fact | None, coverage: list[Fact], liens: list[Fact]) -> Fact | None:
    """Draft range by a fixed, stated rule (no model): 1.5x-3x billed specials, capped by the sum of
    stated per-person liability limits only when every liability coverage has a stated limit."""
    if not specials or not specials.amount or not specials.verified:
        return None
    s_amt = specials.amount
    low, high = round(VALUE_LOW_X * s_amt, 2), round(VALUE_HIGH_X * s_amt, 2)  # exact, no rounding
    liab = [c for c in coverage if c.verified and _LIABILITY.search(c.label)]
    conflicted = [c for c in liab if c.value.startswith("Conflict:")]
    uncapped = [c for c in liab if c not in conflicted and (_UNCAPPED.search(c.value) or c.amount is None)]
    capped = [c for c in liab if c not in uncapped and c not in conflicted and c.amount]
    notes = [f"Firm rule (configurable): {VALUE_LOW_X:g}x–{VALUE_HIGH_X:g}x billed specials (${s_amt:,.2f})"]
    if conflicted:
        c = conflicted[0]
        other = c.value.split(" vs ", 1)[-1]
        amounts = [v for tok in _MONEY.findall(other) if (v := _money_val(tok))]
        notes.append(f"conflicting limits ({c.value.removeprefix('Conflict: ')})")
        if amounts:
            notes.append(f"capped at {_usd(amounts[0])} per person if those limits apply")
    elif liab and not uncapped:
        cap = sum(c.amount for c in liab)
        if high > cap:
            high, low = cap, min(low, cap)
            notes.append(f"capped at stated liability limits (${cap:,.0f})")
    elif uncapped:
        who = uncapped[0].label.split(" · ")
        party = who[1] if len(who) > 1 else who[0]
        notes.append(f"no cap only while {party} ({uncapped[0].value.lower()}) remains liable")
        if capped:
            notes.append(f"otherwise stated limits total ${sum(c.amount for c in capped):,.0f}")
    lien_total = sum(l.amount or 0 for l in liens if l.verified)
    if lien_total:
        notes.append(f"before liens (${lien_total:,.0f})")
    used = [specials] + liab + [l for l in liens if l.verified and l.amount]
    return Fact(id="case_value", label="Case value (draft): " + "; ".join(notes) + ".",
                value=f"{_usd(low)} – {_usd(high)}", amount=high,
                citations=[c for f in used for c in f.citations[:1]], verified=True)


def _future(d: str, today: date) -> bool:
    return date.fromisoformat(d) > today


def build(matter_id: str, force: bool = False, store: bool = True) -> Dashboard:
    """store=False builds a preview without touching the cached dashboard (e.g. while it is audited)."""
    ih = input_hash(matter_id)
    row = _cached_row(matter_id)
    if store and row and _rev_of(row["input_hash"]) > PIPELINE_REV:
        print(f"dashboard cached by pipeline r{_rev_of(row['input_hash'])} > this server's r{PIPELINE_REV}:"
              " serving it as-is; restart this server to pick up the newer code")
        return Dashboard.model_validate_json(row["payload_json"])
    if store and not force and row and row["input_hash"] == ih:
        return Dashboard.model_validate_json(row["payload_json"])

    matter = matter_summary(matter_id)
    if matter is None:
        raise LookupError(f"matter {matter_id} not synced")
    started = datetime.now(timezone.utc).isoformat()
    today = date.today()

    warm()
    embed_matter(matter_id)
    hyde_matter(matter_id)
    ex = extract_all(matter_id)
    vstats = verify_values(matter_id, ex)
    print(f"fact values verified: {vstats}")
    if store:
        save_facts(matter_id, ex, ih)

    facts: dict[str, list[Fact]] = {cat: [_fact(x, f"{cat}-{i}") for i, x in enumerate(items)]
                                    for cat, items in ex.items()}

    # Treatment lines + specials (sum of stated per-provider bills)
    contacts = st.provider_contact_ids(matter_id)
    treatment: list[TreatmentLine] = []
    billed: list[Fact] = []
    for i, x in enumerate(ex.get("treatment", [])):
        name = x.party or x.label
        cid = max(contacts, key=lambda c: fuzz.token_set_ratio(name, c[1]), default=None)
        if cid and fuzz.token_set_ratio(name, cid[1]) < 85:
            cid = None
        bill = None
        if x.amount:
            bill = Fact(id=f"billed-{i}", label=f"Billed: {name}", value=f"${x.amount:,.2f}", amount=x.amount,
                        citations=x.citations, verified=x.verified)
            billed.append(bill)
        treatment.append(TreatmentLine(provider=name, contact_id=cid[0] if cid else None,
                                       first_visit=st.iso(x.date), last_visit=st.iso(x.end_date),
                                       last_visit_basis="records" if x.end_date else None,
                                       visit_count=x.count, billed=bill, citations=x.citations))
    # Medical bills logged in Clio as expense entries are the authoritative per-provider specials.
    charges = st.medical_charges(matter_id)
    if charges:
        billed = []
        for ch in charges:
            name = ch["provider"] or "Medical provider"
            line = max(treatment, key=lambda t: _name_sim(name, t.provider), default=None)
            if line is None or _name_sim(name, line.provider) < 85:
                cid = max(contacts, key=lambda c: fuzz.token_set_ratio(name, c[1]), default=None)
                line = TreatmentLine(provider=name, first_visit=ch["first"], last_visit=ch["last"],
                                     last_visit_basis="billed_through" if ch["last"] else None,
                                     contact_id=cid[0] if cid and fuzz.token_set_ratio(name, cid[1]) >= 85 else None,
                                     citations=list(ch["citations"]))
                treatment.append(line)
            prev = line.billed.amount if line.billed and line.billed.id.startswith("charge-") else 0.0
            amt = round((prev or 0) + ch["amount"], 2)
            cits = (line.billed.citations if prev else []) + ch["citations"]
            line.billed = Fact(id=f"charge-{len(billed)}", label=f"Billed: {line.provider}", value=f"${amt:,.2f}",
                               amount=amt, citations=cits, verified=all(c.verified for c in cits))
            if not line.first_visit and ch["first"]:  # the date now comes from this entry: cite it
                line.first_visit = ch["first"]
                line.citations = [c for c in ch["citations"] if ch["first"] in c.quote] + list(line.citations)
            if not line.last_visit and ch["last"]:
                line.last_visit, line.last_visit_basis = ch["last"], "billed_through"
        for t in treatment:  # LLM-read amounts give way to the Clio entries
            if t.billed and not t.billed.id.startswith("charge-"):
                t.billed = None
        billed = [t.billed for t in treatment if t.billed]
    specials = None
    if billed:
        total = sum(b.amount or 0 for b in billed)
        specials = Fact(id="specials", label="Medical specials (billed)",
                        value=f"${total:,.2f} billed across {len(billed)} provider{'s' if len(billed) > 1 else ''}",
                        amount=round(total, 2), citations=[c for b in billed for c in b.citations[:1]],
                        verified=all(b.verified for b in billed))

    # Whole-record check: conflicts and caveats elsewhere in the file become visible, with both citations.
    checked = [f for f in facts.get("coverage", []) + facts.get("liens", []) + facts.get("injuries", [])
               if f.verified] + ([specials] if specials else [])
    for f, (v, cit) in zip(checked, check_statements(matter_id, [(f"{f.label}: {f.value}", f.citations)
                                                                 for f in checked], purpose="record_check_facts")):
        _apply_finding(f, v, cit, injury=f in facts.get("injuries", []))
    # A coverage line restating limits already shown inside another line's Conflict, from the same
    # source, is a duplicate (readers would add it as a second policy): drop it.
    cov = facts.get("coverage", [])
    for f2 in list(cov):  # the same coverage extracted twice (same value, near-identical label)
        twin = next((f1 for f1 in cov if f1 is not f2 and f1.value == f2.value
                     and fuzz.token_set_ratio(f1.label, f2.label) >= 85), None)
        if twin and len(f2.citations) <= len(twin.citations) and f2 in cov:
            cov.remove(f2)
    for f2 in list(cov):
        if f2.value.startswith("Conflict:"):
            continue
        src2 = {c.source_id for c in f2.citations}
        amts2 = {v for tok in _MONEY.findall(f2.value) if (v := _money_val(tok))}
        for f1 in cov:
            if f1 is f2 or not f1.value.startswith("Conflict:"):
                continue
            amts1 = {v for tok in _MONEY.findall(f1.value) if (v := _money_val(tok))}
            if amts2 and amts2 <= amts1 and src2 & {c.source_id for c in f1.citations}:
                cov.remove(f2)
                break

    # Timeline
    timeline: list[TimelineEvent] = []
    dated_incident = [f for f in facts.get("incident", []) if f.date]
    inc = next((f for f in dated_incident if "date" in f.label.lower()), dated_incident[0] if dated_incident else None)
    if inc:
        timeline.append(TimelineEvent(date=inc.date, label=inc.value[:80], kind="incident",
                                      is_future=_future(inc.date, today), citations=inc.citations))
    unconfirmed: set[int] = set()  # id() of past events the record only scheduled
    for x, f in zip(ex.get("key_dates", []), facts.get("key_dates", [])):
        if not f.date:
            continue
        fut = _future(f.date, today)
        status = x.status or "unknown"
        label = f.label
        if status == "deadline":
            label = f.label
            if not fut and _LIMITATIONS.search(f.label):
                filed = _suit_filed_before(ex, f.date)
                if filed:
                    label = f"{f.label}: {f.date} (suit filed {filed.date[:4]}, satisfied)"
                    f.citations = list(f.citations) + [c for c in filed.citations if c.verified][:1]  # cite the filing
        elif status == "adjourned":
            label = f"Adjourned: {f.label}"
        elif status in ("scheduled", "unknown") and fut:
            label = f"Scheduled: {f.label}" if status == "scheduled" else f.label
        elif status in ("scheduled", "unknown"):
            # a notice/subpoena set this date; nothing in the record says it happened
            label = f"Scheduled: {f.label} (no record it occurred)"
        ev = TimelineEvent(date=f.date, label=label, kind="deadline" if fut else "legal", is_future=fut,
                           citations=f.citations)
        if status == "adjourned" or (status not in ("occurred", "deadline") and not fut):
            unconfirmed.add(id(ev))
        timeline.append(ev)
    for t in treatment:
        if t.first_visit:
            one_day = t.last_visit == t.first_visit
            timeline.append(TimelineEvent(date=t.first_visit,
                                          label=f"{'Treatment (one day)' if one_day else 'Treatment starts'}: {t.provider}",
                                          kind="treatment", is_future=False, citations=t.citations))
    cal_events, cal_actions = st.calendar(matter_id, today)
    # Past calendar entries are only the firm's plan: surface records that put the event on another date.
    past_cal = [e for e in cal_events if not e.is_future and e.kind in ("legal", "deadline")]
    for e in past_cal:  # deterministic first: a filed report about the same person stamped BEFORE the date
        stamp = _filed_before(matter_id, e)
        if stamp:
            filed, cit = stamp
            e.label = f"{e.label} (Conflict: report filed {filed}, before this calendar date)"
            e.citations = list(e.citations) + [cit]
            unconfirmed.add(id(e))
    rest_cal = [e for e in past_cal if "Conflict" not in e.label]
    for e, (v, cit) in zip(rest_cal, check_statements(
            matter_id, [(f"{e.label.removeprefix('Calendar: ')} took place on {e.date}", e.citations) for e in rest_cal],
            purpose="record_check_calendar")):
        if v.verdict == "contradicted" and cit is not None:
            e.label = f"{e.label} (Conflict: {v.note.strip().rstrip('.')})"
            e.citations = list(e.citations) + [cit]
            unconfirmed.add(id(e))  # conflicting date: keep it off the compact strip
    timeline.extend(cal_events)
    for t in treatment:  # treatment still scheduled with this provider → treatment is ongoing
        nxt = [e.date for e in cal_events if e.is_future and e.kind == "treatment"
               and fuzz.token_set_ratio(t.provider, e.label) >= 90]
        t.next_visit = min(nxt) if nxt else None
    uniq: list[TimelineEvent] = []
    rank = {"incident": 0, "deadline": 1, "legal": 2, "treatment": 3, "communication": 4}
    for e in sorted(timeline, key=lambda e: (e.date, rank[e.kind])):
        same_day = [u for u in uniq if u.date == e.date]
        if any(u.kind == "incident" for u in same_day) and e.kind == "legal":
            continue  # "Date of incident" etc. duplicates the incident marker
        if any(fuzz.token_set_ratio(u.label, e.label) >= 80 for u in same_day):
            continue
        words = {w for w in re.findall(r"[a-z]{6,}", e.label.lower())}
        if e.kind in ("legal", "deadline") and any(
                u.kind in ("legal", "deadline") and words & set(re.findall(r"[a-z]{6,}", u.label.lower()))
                for u in same_day):
            continue  # same-day legal events sharing a key word (e.g. a limitations date logged twice)
        uniq.append(e)

    mark_milestones(matter_id, uniq, today)
    for e in uniq:
        if id(e) in unconfirmed:
            e.major = False  # never put an unconfirmed past event on the compact strip

    # Actions
    actions: list[ActionItem] = st.actions_from_tasks(matter_id, today)
    for ca in cal_actions:  # a calendar reminder for the same ask on the same day as a task is a duplicate
        cw = set(re.findall(r"[a-z]{5,}", ca.title.lower()))
        if any(a.due_date == ca.due_date and len(cw & set(re.findall(r"[a-z]{5,}", a.title.lower()))) >= 2
               for a in actions):
            continue
        actions.append(ca)
    for x, f in zip(ex.get("requests", []), facts.get("requests", [])):
        if any(fuzz.token_set_ratio(a.title, f.label) >= 70 for a in actions):
            continue  # already tracked as a Clio task
        if x.party and any(a.waiting_on and _name_sim(a.waiting_on, x.party) >= 85 for a in actions):
            continue  # a Clio task already waits on this party; the task is the record of truth
        actions.append(ActionItem(title=f.label, due_date=f.date, status="waiting", waiting_on=x.party,
                                  citations=f.citations))
    order = {"overdue": 0, "upcoming": 1, "waiting": 2}
    actions.sort(key=lambda a: (order[a.status], a.due_date or "9999"))

    spent = st.firm_spent(matter_id)
    contact = st.last_client_contact(matter_id)

    pool: list[Fact] = [f for cat in ("incident", "injuries", "coverage", "liens", "key_dates", "stage")
                        for f in facts.get(cat, [])]
    adverse = st.adverse_parties(matter_id)
    pool += billed + [f for f in (specials, spent, contact, adverse) if f]
    pool = [f for f in pool if f.verified]
    stage = st.clio_stage(matter_id)
    status = matter.status + (f"; Clio matter stage: {stage}" if stage else "")
    headline = write_brief(matter_id, pool, actions, status, today)
    if adverse and len(headline.status_line.split()) < 4:  # verifier stripped it: grounded fallback
        names = [p.split(" (")[0] for p in adverse.value.split("; ")]
        headline.status_line = f"{headline.stage or 'Open'}: case against {' and '.join(names)}."
        headline.status_citations = list(headline.status_citations) + adverse.citations
    status_fact = Fact(id="status", label="Status", value=headline.status_line, citations=headline.status_citations)
    hl = [status_fact] + headline.bullets
    for f, (v, cit) in zip(hl, check_statements(matter_id, [(f.value, f.citations) for f in hl],
                                                purpose="record_check_headline")):
        _apply_finding(f, v, cit, bullet=True)
    if adverse:  # a status line naming one adverse party must name all of them
        names = [p.split(" (")[0] for p in adverse.value.split("; ")]
        def _named(n: str) -> bool:
            keys = [w for w in re.findall(r"[A-Za-z][A-Za-z-]{3,}", n) if w.lower() not in ("commuter", "railroad", "company")]
            return any(k.lower() in status_fact.value.lower() for k in keys[-1:] + keys[:1])
        named = [n for n in names if _named(n)]
        if named and len(named) < len(names):
            status_fact.value = f"{status_fact.value.rstrip('.')} (adverse parties: {'; '.join(names)})."
            status_fact.citations = list(status_fact.citations) + adverse.citations
    headline.status_line, headline.status_citations = status_fact.value, status_fact.citations
    case_value = value_range(specials, facts.get("coverage", []), facts.get("liens", []))

    with connect() as conn:
        run_cost = conn.execute("SELECT COALESCE(SUM(cost_usd), 0) FROM llm_usage WHERE matter_id = ?"
                                " AND created_at >= ?", (matter_id, started)).fetchone()[0]
        models = [r[0] for r in conn.execute("SELECT DISTINCT model FROM llm_usage WHERE matter_id = ?",
                                             (matter_id,))]

    dash = Dashboard(
        matter=matter,
        generated_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        cost_usd=round(float(run_cost), 4),
        models=models,
        headline=headline,
        timeline=uniq,
        kpis=Kpis(specials=specials, coverage=facts.get("coverage", []), case_value=case_value,
                  firm_spent=spent, liens=facts.get("liens", [])),
        actions=actions,
        last_client_contact=contact,
        injuries=facts.get("injuries", []),
        treatment=treatment,
        recent=recent_activity(matter_id, today),
    )
    if not store:
        return dash
    with connect() as conn:
        cur = conn.execute("SELECT input_hash, payload_json FROM digests WHERE matter_id = ? AND kind = 'dashboard'",
                           (matter_id,)).fetchone()
        if cur and _rev_of(cur["input_hash"]) > PIPELINE_REV:  # a newer server wrote while we were building
            return Dashboard.model_validate_json(cur["payload_json"])
        conn.execute("INSERT OR REPLACE INTO digests (matter_id, kind, input_hash, payload_json, model, created_at)"
                     " VALUES (?, 'dashboard', ?, ?, ?, datetime('now'))",
                     (matter_id, ih, dash.model_dump_json(), ",".join(models)))
    return dash
