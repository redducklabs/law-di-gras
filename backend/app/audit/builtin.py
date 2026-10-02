"""Built-in audit: every new dashboard digest or Blind spots review is audited once, in the background.

GET /api/matters/{id}/audit?target=dashboard|review -> AuditReport. One audit per payload hash, stored in
`digests` (kind 'audit:dashboard' / 'audit:review'); a new hash starts one background thread. Read-only
toward the dashboard/review caches and Clio. LLM cost is logged by app.llm and summed into cost_usd.
"""

import hashlib
import json
import re
import threading
import traceback
from datetime import datetime, timezone

from app.db import connect
from app.schemas import AuditFlag, AuditReport, Citation, Dashboard, RunProgress

KINDS = {"dashboard": "audit:dashboard", "review": "audit:review"}
VERSION = "a4"  # bump to re-audit everything when the checks change
_lock = threading.Lock()
_jobs: dict[tuple[str, str, str], AuditReport] = {}  # (matter, target, hash) -> in-flight/failed report


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def target_hash(matter_id: str, target: str) -> str | None:
    with connect() as conn:
        if target == "dashboard":
            row = conn.execute("SELECT input_hash FROM digests WHERE matter_id=? AND kind='dashboard'", (matter_id,)).fetchone()
            return f"{VERSION}:{row['input_hash']}" if row else None
        row = conn.execute("SELECT payload_json FROM digests WHERE matter_id=? AND kind='review'", (matter_id,)).fetchone()
        if not row:
            return None
        # hash the findings only, so a review that only changed its `run` progress is not re-audited
        findings = json.loads(row["payload_json"]).get("findings", [])
        return f"{VERSION}:" + hashlib.sha256(json.dumps(findings, sort_keys=True).encode()).hexdigest()


def _stored(matter_id: str, target: str) -> AuditReport | None:
    with connect() as conn:
        row = conn.execute("SELECT payload_json FROM digests WHERE matter_id=? AND kind=?",
                           (matter_id, KINDS[target])).fetchone()
    return AuditReport.model_validate_json(row["payload_json"]) if row else None


def _store(rep: AuditReport) -> None:
    with connect() as conn:
        conn.execute("INSERT OR REPLACE INTO digests (matter_id, kind, input_hash, payload_json, model, created_at)"
                     " VALUES (?,?,?,?,?,?)",
                     (rep.matter_id, KINDS[rep.target], rep.target_hash, rep.model_dump_json(), "claude-sonnet-5-5", _now()))


def _cost_since(matter_id: str, since: str, purposes: tuple[str, ...]) -> float:
    q = " OR ".join("purpose LIKE ?" for _ in purposes)
    with connect() as conn:
        row = conn.execute(f"SELECT COALESCE(SUM(cost_usd),0) FROM llm_usage WHERE matter_id=? AND created_at>=? AND ({q})",
                           (matter_id, since, *purposes)).fetchone()
    return round(float(row[0]), 4)


def get_report(matter_id: str, target: str, rerun: bool = False) -> AuditReport | None:
    """Stored report for the current payload, else the in-flight one (starting it if needed). None = nothing to audit.
    rerun=True recomputes even when a report for this payload is stored (one run at a time)."""
    h = target_hash(matter_id, target)
    if h is None:
        return None
    rep = _stored(matter_id, target)
    key = (matter_id, target, h)
    if rep and rep.target_hash == h and not (rerun and key not in _jobs):
        return rep
    with _lock:
        if key in _jobs and (_jobs[key].run.status in ("queued", "running") or
                             (_jobs[key].run.status == "done" and not rerun)):
            return _jobs[key]  # a failed job falls through and is retried
        job = AuditReport(matter_id=matter_id, target=target, target_hash=h,
                          run=RunProgress(status="queued", stage="Waiting to start", pct=0, started_at=_now()))
        _jobs[key] = job
    threading.Thread(target=_run, args=(job,), daemon=True, name=f"audit-{target}").start()
    return job


def _run(job: AuditReport) -> None:
    started = _now()
    job.run.status, job.run.stage, job.run.pct = "running", "Starting", 1

    def step(stage: str, pct: float) -> None:
        job.run.stage = stage
        job.run.pct = max(job.run.pct, min(99, int(pct)))

    try:
        if job.target == "dashboard":
            flags, n = audit_dashboard(job.matter_id, step)
            purposes = ("audit:%",)
        else:
            flags, n = audit_review(job.matter_id, step)
            purposes = ("audit:%", "review_verify")
        job.flags, job.items_checked = flags, n
        job.cost_usd = _cost_since(job.matter_id, started, purposes)
        job.run.status, job.run.stage, job.run.pct, job.run.finished_at = "done", "Audit complete", 100, _now()
        # store only if the payload did not change while we ran
        if target_hash(job.matter_id, job.target) == job.target_hash:
            _store(job)
    except Exception as e:  # keep the failure visible; a restart retries
        traceback.print_exc()
        job.run.status, job.run.error, job.run.finished_at = "failed", f"{type(e).__name__}: {e}"[:300], _now()


# ---------------------------------------------------------------- dashboard

SECTION = {"headline": "status", "kpi": "kpis", "timeline": "timeline", "action": "next-steps",
           "injury": "injuries", "treatment": "treatment", "recent": "recent", "contact": "next-steps"}
SEV_RANK = {"critical": 0, "major": 1, "minor": 2}


def _keys(d: Dashboard) -> dict[str, tuple[str, str]]:
    """Audit item path -> (item_id the UI can match, PageSection id)."""
    k: dict[str, tuple[str, str]] = {"headline.status_line": ("status_line", "status")}
    for i, b in enumerate(d.headline.bullets):
        k[f"headline.bullets[{i}]"] = (b.id, "status")
    for i, e in enumerate(d.timeline):
        k[f"timeline[{i}]"] = (f"timeline:{e.date[:10]}:{e.label}", "timeline")
    for name in ("specials", "case_value", "firm_spent"):
        f = getattr(d.kpis, name)
        if f:
            k[f"kpis.{name}"] = (f.id, "kpis")
    for i, f in enumerate(d.kpis.coverage):
        k[f"kpis.coverage[{i}]"] = (f.id, "kpis")
    for i, f in enumerate(d.kpis.liens):
        k[f"kpis.liens[{i}]"] = (f.id, "kpis")
    for i, a in enumerate(d.actions):
        k[f"actions[{i}]"] = (f"action:{a.title}", "next-steps")
    if d.last_client_contact:
        k["last_client_contact"] = (d.last_client_contact.id, "next-steps")
    for i, f in enumerate(d.injuries):
        k[f"injuries[{i}]"] = (f.id, "injuries")
    for i, f in enumerate(d.recent):
        k[f"recent[{i}]"] = (f.id, "recent")
    for i, t in enumerate(d.treatment):
        k[f"treatment[{i}]"] = (f"treatment:{t.provider}", "treatment")
        k[f"treatment:{t.provider}"] = (f"treatment:{t.provider}", "treatment")
    return k


CHECK_NAME = {"1-code": "fact-support", "1-judge": "fact-support", "2-record": "whole-record",
              "3-kpi": "kpi-reconcile", "5-timeline": "timeline", "6-provider": "provider-leak"}


def _plain(note: str) -> str:
    note = re.sub(r"^(partial|unsupported|misleading|tense_wrong|wrong_party|wrong_date|wrong_amount|contradicted):\s*", "", note)
    return note.split(" [claim:")[0].strip()[:400]


def audit_dashboard(matter_id: str, step) -> tuple[list[AuditFlag], int]:
    from app.audit import checks, record_check
    from app.audit.items import flatten, load_dashboard

    d, _ = load_dashboard(matter_id)
    items = flatten(d)
    keys = _keys(d)
    by_path = {it.id: it for it in items}
    step("Checking every quote, date and amount", 3)
    found = checks.fact_support_code(items, [d.kpis.specials, d.kpis.firm_spent, *d.kpis.liens])
    step("Reconciling KPIs", 6)
    kpi, _ = checks.kpi_reconcile(d, matter_id)
    found += kpi
    step("Checking timeline semantics", 8)
    found += checks.timeline_semantics(d)
    step("Checking provider views for leaks", 10)
    prov, _ = checks.provider_views(matter_id)
    found += [f for f in prov if f.severity in ("critical", "major")]  # minor provider notes are not page items
    step("Judging each fact against its sources", 12)
    judge = checks.fact_support_judge(items, matter_id,
                                      progress=lambda x: step(f"Judging each fact against its sources ({int(x * 100)}%)", 12 + 50 * x))
    # Sums are authoritative from the KPI reconcile (code); the judge mis-adds when only some charges are cited.
    sums_ok = not any(f.check == "3-kpi" and f.severity != "minor" for f in kpi)
    for f in judge:
        if sums_ok and f.extra.get("verdict") == "wrong_amount":
            continue
        f.severity = "minor" if f.severity in ("critical", "major") else f.severity  # judge-only: advisory
        found.append(f)
    for f in found:
        if f.check == "1-code" and "no citations of its own" in f.problem:
            f.severity = "minor"  # a design gap, not a wrong fact
    step("Checking claims against the whole record", 62)
    rec, _ = record_check.record_support(items, matter_id,
                                         progress=lambda x: step(f"Checking claims against the whole record ({int(x * 100)}%)", 62 + 35 * x))
    for f in rec:
        shown = by_path.get(f.item)
        if shown and "conflict" in shown.text.lower() and f.problem.startswith("Record contradicts"):
            continue  # the item already displays the conflict; that is the feature, not a flaw
        if f.problem.startswith("Supported in the record but not by the cited sources"):
            f.severity = "minor"
        elif f.severity == "critical":
            f.severity = "major"  # the whole-record judge is advisory too; surfaced conflicts read as contradictions
        found.append(f)

    flags: list[AuditFlag] = []
    seen: dict[tuple, int] = {}  # (item_id, check) -> index in flags; keep the most severe
    for f in found:
        if f.severity not in SEV_RANK:
            continue
        path = f.item if f.item in keys else (f.item.split(" ")[0] if f.item.split(" ")[0] in keys else None)
        if path:
            item_id, section = keys[path]
        elif f.check == "6-provider":
            item_id, section = f"provider:{f.item}", ""
        else:
            item_id, section = f.item, ("kpis" if f.check == "3-kpi" else "")
        note = _plain(f.problem)
        sig = (item_id, CHECK_NAME.get(f.check, f.check))
        if sig in seen:
            j = seen[sig]
            if SEV_RANK[f.severity] < SEV_RANK[flags[j].severity]:
                flags[j] = flags[j].model_copy(update={"severity": f.severity, "note": note})
            continue
        cits: list[Citation] = []
        it = by_path.get(path or "")
        if f.check == "2-record" and ":" in f.quote:
            cits = _evidence(f.quote)
        elif it:
            cits = it.citations[:3]
        seen[sig] = len(flags)
        flags.append(AuditFlag(target="dashboard", item_id=item_id, section=section, severity=f.severity,
                               check=CHECK_NAME.get(f.check, f.check), note=note, citations=cits))
    flags.sort(key=lambda a: (SEV_RANK[a.severity], a.section, a.item_id))
    return flags, len(items)


def _evidence(q: str) -> list[Citation]:
    from app.digest.spans import locate
    sid, _, quote = q.partition(": ")
    quote = quote.replace(" (quote not verbatim)", "").strip()
    if not sid or len(quote) < 8:
        return []
    with connect() as conn:
        c = locate(conn, sid.strip(), quote)
    return [c] if c and c.verified else []


# ---------------------------------------------------------------- review (Blind spots)

def audit_review(matter_id: str, step) -> tuple[list[AuditFlag], int]:
    from app.audit.items import span_check
    from app.review.agent import cached, unsourced_legal_cites
    from app.review.checks import overreach, record_cites, same_source

    rv = cached(matter_id)
    flags: list[AuditFlag] = []
    fs = rv.findings if rv else []
    for i, f in enumerate(fs):
        base = 5 + 90 * i / max(1, len(fs))
        step(f"Verifying finding {i + 1} of {len(fs)}", base)
        texts = [f.title, f.why_it_matters, f.suggested_next_step]
        quotes = "\n".join(c.quote for c in f.citations)

        def add(sev, check, note, cits=None):
            flags.append(AuditFlag(target="review", item_id=f.id, section="blind-spots", severity=sev,
                                   check=check, note=note[:400], citations=cits or []))

        for c in f.citations:
            ok, how = span_check(c)
            if not ok:
                add("critical", "fact-support", f"Quote not found in the cited source ({how}): \"{c.quote[:100]}\"", [c])
        blob = " ".join(texts)
        quoted = " ".join(a or b for a, b in re.findall(r'"([^"]{3,})"|“([^”]{3,})”', blob)).lower()
        words_seen: set[str] = set()
        for p in overreach(texts, quotes, f.citations):
            m = re.match(r'"([^"]+)"', p)
            word = (m.group(1) if m else p).lower()
            if word in words_seen or (word and word in quoted):
                continue  # one flag per word; a word inside a quoted string is the record's, not ours
            words_seen.add(word)
            # Major only where the word changes the claim: exclusivity about witnesses, absolutes, certainty.
            strong = (word == "only" and re.search(r"\bonly\b(?:\s+\S+){0,3}?\s+(?:non-party\s+)?(?:eye)?witness", blob, re.I)) \
                or word == "neither" or word.startswith(("without", "will", "has ", "not a", "no "))
            add("major" if strong else "minor", "overreach", f"Overstates the record: {p}")
        for cite in unsourced_legal_cites(texts, f.citations):
            add("major", "legal-cite", f"Legal citation \"{cite}\" is not inside any cited quote, so the highlight does not show it.")
        if f.category in ("conflict", "inconsistency"):
            step(f"Re-reading the cited sources for finding {i + 1}", base + 3)
            p = same_source(matter_id, f"{f.title}. {f.why_it_matters}", f.citations)
            if p:
                add("major", "same-source", p)
        if f.category in ("conflict", "inconsistency"):
            continue  # contradicting evidence IS the finding; same-source above covers false conflicts
        step(f"Checking finding {i + 1} against the whole record", base + 6)
        extra, problems = record_cites(matter_id, [f.title, f.why_it_matters], f.citations)
        for p in problems:
            add("major", "whole-record", p, extra[:1])
    flags.sort(key=lambda a: (SEV_RANK[a.severity], a.item_id))
    return flags, len(fs)
