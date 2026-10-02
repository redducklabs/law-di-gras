"""Assemble the cached Dashboard: index → extract → map → brief.

Cache key = hash of every source content_hash for the matter + pipeline
version. Unchanged case → the stored Dashboard is returned without any call.
"""

import hashlib
import re
from datetime import date, datetime, timezone

from rapidfuzz import fuzz

from app.db import connect
from app.digest import structured as st
from app.digest.brief import write_brief
from app.digest.curate import mark_milestones, recent_activity
from app.digest.extract import PROMPT_VERSION, Extracted, extract_all, save_facts
from app.retrieval.embed import embed_matter
from app.retrieval.hyde import hyde_matter
from app.retrieval.search import warm
from app.schemas import (ActionItem, Dashboard, Fact, Kpis, MatterSummary, TimelineEvent, TreatmentLine)

PIPELINE_VERSION = f"d5-{PROMPT_VERSION}"


def input_hash(matter_id: str) -> str:
    with connect() as conn:
        rows = conn.execute("SELECT id, content_hash FROM sources WHERE matter_id = ? ORDER BY id",
                            (matter_id,)).fetchall()
    h = hashlib.sha256(PIPELINE_VERSION.encode())
    for r in rows:
        h.update(f"{r[0]}={r[1]};".encode())
    return h.hexdigest()


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


VALUE_LOW_X, VALUE_HIGH_X = 1.5, 3.0
_LIABILITY = re.compile(r"liabil|bodily|(?<![a-z])bi(?![a-z])", re.I)
_UNCAPPED = re.compile(r"self[- ]insured|no stated limit|unlimited", re.I)


def _round5k(x: float) -> float:
    return round(x / 5000) * 5000


def value_range(specials: Fact | None, coverage: list[Fact], liens: list[Fact]) -> Fact | None:
    """Draft range by a fixed, stated rule (no model): 1.5x-3x billed specials, capped by the sum of
    stated per-person liability limits only when every liability coverage has a stated limit."""
    if not specials or not specials.amount or not specials.verified:
        return None
    s_amt = specials.amount
    low, high = _round5k(VALUE_LOW_X * s_amt), _round5k(VALUE_HIGH_X * s_amt)
    liab = [c for c in coverage if c.verified and _LIABILITY.search(c.label)]
    uncapped = [c for c in liab if _UNCAPPED.search(c.value) or c.amount is None]
    notes = [f"Rule: {VALUE_LOW_X:g}x-{VALUE_HIGH_X:g}x billed specials (${s_amt:,.0f})"]
    if liab and not uncapped:
        cap = sum(c.amount for c in liab)
        if high > cap:
            high, low = cap, min(low, cap)
            notes.append(f"capped at stated liability limits (${cap:,.0f})")
    elif uncapped:
        notes.append(f"not capped: {uncapped[0].label.split(' · ')[0]} {uncapped[0].value.lower()}")
    lien_total = sum(l.amount or 0 for l in liens if l.verified)
    if lien_total:
        notes.append(f"before liens (${lien_total:,.0f})")
    used = [specials] + liab + [l for l in liens if l.verified and l.amount]
    return Fact(id="case_value", label="Case value (draft): " + "; ".join(notes) + ".",
                value=f"${low:,.0f} – ${high:,.0f}", amount=high,
                citations=[c for f in used for c in f.citations[:1]], verified=True)


def _future(d: str, today: date) -> bool:
    return date.fromisoformat(d) > today


def build(matter_id: str, force: bool = False) -> Dashboard:
    ih = input_hash(matter_id)
    if not force:
        with connect() as conn:
            row = conn.execute("SELECT input_hash, payload_json FROM digests WHERE matter_id = ? AND kind = 'dashboard'",
                               (matter_id,)).fetchone()
        if row and row["input_hash"] == ih:
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
                                     contact_id=cid[0] if cid and fuzz.token_set_ratio(name, cid[1]) >= 85 else None,
                                     citations=list(ch["citations"]))
                treatment.append(line)
            prev = line.billed.amount if line.billed and line.billed.id.startswith("charge-") else 0.0
            amt = round((prev or 0) + ch["amount"], 2)
            cits = (line.billed.citations if prev else []) + ch["citations"]
            line.billed = Fact(id=f"charge-{len(billed)}", label=f"Billed: {line.provider}", value=f"${amt:,.2f}",
                               amount=amt, citations=cits, verified=all(c.verified for c in cits))
            line.first_visit = line.first_visit or ch["first"]
            line.last_visit = line.last_visit or ch["last"]
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

    # Timeline
    timeline: list[TimelineEvent] = []
    dated_incident = [f for f in facts.get("incident", []) if f.date]
    inc = next((f for f in dated_incident if "date" in f.label.lower()), dated_incident[0] if dated_incident else None)
    if inc:
        timeline.append(TimelineEvent(date=inc.date, label=inc.value[:80], kind="incident",
                                      is_future=_future(inc.date, today), citations=inc.citations))
    for f in facts.get("key_dates", []):
        if f.date:
            fut = _future(f.date, today)
            timeline.append(TimelineEvent(date=f.date, label=f.label, kind="deadline" if fut else "legal",
                                          is_future=fut, citations=f.citations))
    for t in treatment:
        if t.first_visit:
            timeline.append(TimelineEvent(date=t.first_visit, label=f"Treatment starts: {t.provider}",
                                          kind="treatment", is_future=False, citations=t.citations))
    cal_events, cal_actions = st.calendar(matter_id, today)
    timeline.extend(cal_events)
    uniq: list[TimelineEvent] = []
    rank = {"incident": 0, "deadline": 1, "legal": 2, "treatment": 3, "communication": 4}
    for e in sorted(timeline, key=lambda e: (e.date, rank[e.kind])):
        same_day = [u for u in uniq if u.date == e.date]
        if any(u.kind == "incident" for u in same_day) and e.kind == "legal":
            continue  # "Date of incident" etc. duplicates the incident marker
        if any(fuzz.token_set_ratio(u.label, e.label) >= 80 for u in same_day):
            continue
        uniq.append(e)

    mark_milestones(matter_id, uniq, today)

    # Actions
    actions: list[ActionItem] = st.actions_from_tasks(matter_id, today) + cal_actions
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
    pool += billed + [f for f in (specials, spent, contact) if f]
    pool = [f for f in pool if f.verified]
    stage = st.clio_stage(matter_id)
    status = matter.status + (f"; Clio matter stage: {stage}" if stage else "")
    headline = write_brief(matter_id, pool, actions, status, today)
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
    with connect() as conn:
        conn.execute("INSERT OR REPLACE INTO digests (matter_id, kind, input_hash, payload_json, model, created_at)"
                     " VALUES (?, 'dashboard', ?, ?, ?, datetime('now'))",
                     (matter_id, ih, dash.model_dump_json(), ",".join(models)))
    return dash
