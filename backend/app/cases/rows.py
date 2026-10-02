"""Cases landing page rows: every Clio matter (cached Dashboard fields) + labeled samples.

attention_score is deliberately simple and shown with its reasons:
    3 x overdue items
  + 1 x items waiting on others
  + 2 if the next deadline is within 30 days
  + 1 if the last client contact is 30+ days ago (or none on file)
"""

import json
import logging
import time
from datetime import date, timedelta
from pathlib import Path

from app.db import connect
from app.schemas import CaseRow, Dashboard, Fact, NextDeadline

log = logging.getLogger("cases")

SAMPLES_PATH = Path(__file__).with_name("samples.json")
DEADLINE_SOON_DAYS = 30
CONTACT_STALE_DAYS = 30
_CLIO_TTL = 300
_clio_cache: tuple[float, list[dict]] | None = None


def score(row: CaseRow, today: date | None = None) -> CaseRow:
    today = today or date.today()
    s, why = 0.0, []
    if row.overdue_count:
        s += 3 * row.overdue_count
        why.append(f"{row.overdue_count} overdue")
    if row.waiting_count:
        s += row.waiting_count
        why.append(f"{row.waiting_count} waiting on others")
    if row.next_deadline:
        try:
            days = (date.fromisoformat(row.next_deadline.date[:10]) - today).days
        except ValueError:
            days = None
        if days is not None and 0 <= days <= DEADLINE_SOON_DAYS:
            s += 2
            why.append(f"deadline in {days} day{'' if days == 1 else 's'}")
    contact_days = None
    if row.last_client_contact:
        try:
            contact_days = (today - date.fromisoformat(row.last_client_contact[:10])).days
        except ValueError:
            pass
    if contact_days is None or contact_days >= CONTACT_STALE_DAYS:
        s += 1
        why.append("no client contact on file" if contact_days is None else f"no client contact in {contact_days} days")
    return row.model_copy(update={"attention_score": s, "attention_reasons": why})


# ---------- real matters ----------

def _clio_matters() -> list[dict]:
    """Matter list from Clio (GET only), cached briefly; falls back to our synced table."""
    global _clio_cache
    if _clio_cache and time.time() - _clio_cache[0] < _CLIO_TTL:
        return _clio_cache[1]
    try:
        from app.clio.client import client
        rows = list(client().paginate("matters.json", {"fields": "id,display_number,description,status,client{name}"}))
        _clio_cache = (time.time(), rows)
        return rows
    except Exception:
        log.warning("Clio matter list unavailable; using synced matters", exc_info=True)
    with connect() as conn:
        return [{"id": r["id"], "display_number": r["display_number"], "description": r["description"],
                 "status": r["status"], "client": {"name": r["client_name"]}}
                for r in conn.execute("SELECT * FROM matters")]


def _dashboard(matter_id: str) -> Dashboard | None:
    with connect() as conn:
        row = conn.execute("SELECT payload_json FROM digests WHERE matter_id=? AND kind='dashboard'",
                           (matter_id,)).fetchone()
    if not row:
        return None
    try:
        return Dashboard.model_validate_json(row["payload_json"])
    except Exception:
        log.warning("cached dashboard for %s does not parse", matter_id, exc_info=True)
        return None


def _real_row(m: dict, today: date) -> CaseRow:
    mid = str(m["id"])
    d = _dashboard(mid)
    row = CaseRow(
        id=mid,
        display_number=m.get("display_number") or mid,
        title=m.get("description") or m.get("display_number") or mid,
        client_name=(m.get("client") or {}).get("name") or "",
        stage=m.get("status"),
    )
    if not d:
        return row
    future = sorted((e for e in d.timeline if e.is_future and e.date[:10] >= today.isoformat()), key=lambda e: e.date)
    # A real deadline (deadline/legal kinds) beats treatment appointments and calls.
    upcoming = [e for e in future if e.kind in ("deadline", "legal")] or future
    lcc = d.last_client_contact
    return row.model_copy(update={
        "title": d.matter.title or row.title,
        "client_name": d.matter.client_name or row.client_name,
        "stage": d.headline.stage or row.stage,
        "digested": True,
        "overdue_count": sum(a.status == "overdue" for a in d.actions),
        "waiting_count": sum(a.status == "waiting" for a in d.actions),
        "next_deadline": NextDeadline(date=upcoming[0].date[:10], label=upcoming[0].label) if upcoming else None,
        "last_client_contact": (lcc.date or None) if lcc else None,
        "specials": d.kpis.specials,
        "coverage": d.kpis.coverage,
        "case_value": d.kpis.case_value,
        "firm_spent": d.kpis.firm_spent,
    })


# ---------- samples (fictional demo filler) ----------

def _fact(i: int, key: str, label: str, value: str | None) -> Fact | None:
    return Fact(id=f"sample:{i}:{key}", label=label, value=value, verified=False) if value else None


def _sample_rows(today: date) -> list[CaseRow]:
    try:
        data = json.loads(SAMPLES_PATH.read_text(encoding="utf-8"))
    except Exception:
        log.warning("samples.json unreadable", exc_info=True)
        return []
    out = []
    for i, s in enumerate(data.get("rows", []), 1):
        dl = s.get("deadline_in_days")
        lc = s.get("last_client_contact_days_ago")
        out.append(CaseRow(
            id=f"sample:{i}",
            display_number=s["display_number"],
            title=s["title"],
            client_name=s["client_name"],
            stage=s.get("stage"),
            sample=True,
            digested=False,
            overdue_count=s.get("overdue_count", 0),
            waiting_count=s.get("waiting_count", 0),
            next_deadline=NextDeadline(date=(today + timedelta(days=dl)).isoformat(), label=s.get("deadline_label") or "Deadline")
            if dl is not None else None,
            last_client_contact=(today - timedelta(days=lc)).isoformat() if lc is not None else None,
            specials=_fact(i, "specials", "Specials (sample)", s.get("specials")),
            coverage=[f for j, v in enumerate(s.get("coverage") or []) if (f := _fact(i, f"coverage{j}", "Coverage (sample)", v))],
            case_value=_fact(i, "case_value", "Case value (sample)", s.get("case_value")),
            firm_spent=_fact(i, "firm_spent", "Firm spent (sample)", s.get("firm_spent")),
        ))
    return out


def case_rows(include_samples: bool = True) -> list[CaseRow]:
    today = date.today()
    rows = [_real_row(m, today) for m in _clio_matters()]
    if include_samples:
        rows += _sample_rows(today)
    rows = [score(r, today) for r in rows]
    # Highest attention first; real matters win ties over samples.
    return sorted(rows, key=lambda r: (-r.attention_score, r.sample, r.display_number))
