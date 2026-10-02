"""Deterministic mapping of structured Clio rows (tasks, calendar, expenses,
communications) into actions, timeline, firm spend and last client contact.

No LLM: these rows are already structured. Each item cites its own source row.
Field names follow Clio's v4 API; every read is defensive because S1 stores
the raw item JSON as-is.
"""

import json
from datetime import date

from rapidfuzz import fuzz

from app.db import connect
from app.digest.spans import locate
from app.schemas import ActionItem, Citation, Fact, TimelineEvent


def iso(d) -> str | None:
    if not d:
        return None
    s = str(d)[:10]
    try:
        date.fromisoformat(s)
        return s
    except ValueError:
        return None


def _raw(row) -> dict:
    try:
        return json.loads(row["raw_json"] or "{}") or {}
    except ValueError:
        return {}


def row_citation(conn, row, quote: str | None = None) -> Citation:
    """Cite a Clio row by its own text; the row itself is the record."""
    q = (quote or row["title"] or "").strip()
    c = locate(conn, row["id"], q) if q else None
    if c and c.verified:
        return c
    return Citation(source_id=row["id"], source_kind=row["kind"], source_title=row["title"] or row["id"],
                    date=iso(row["date"]), quote=q or (row["text"] or "")[:200], verified=True)


def _rows(conn, matter_id: str, kind: str):
    return conn.execute("SELECT * FROM sources WHERE matter_id = ? AND kind = ? ORDER BY date",
                        (matter_id, kind)).fetchall()


def actions_from_tasks(matter_id: str, today: date) -> list[ActionItem]:
    out: list[ActionItem] = []
    with connect() as conn:
        for row in _rows(conn, matter_id, "task"):
            raw = _raw(row)
            status = (raw.get("status") or "").lower()
            if status in ("complete", "completed", "done") or raw.get("completed_at"):
                continue
            due = iso(raw.get("due_at") or raw.get("due_date") or row["date"])
            assignee = raw.get("assignee") or {}
            owner = assignee.get("name") if isinstance(assignee, dict) else None
            if isinstance(assignee, dict) and (assignee.get("type") or "").lower() == "contact":
                st, waiting_on = "waiting", owner
            elif due and date.fromisoformat(due) < today:
                st, waiting_on = "overdue", None
            else:
                st, waiting_on = "upcoming", None
            out.append(ActionItem(title=raw.get("name") or row["title"] or "Task", due_date=due, owner=owner,
                                  status=st, waiting_on=waiting_on, citations=[row_citation(conn, row)]))
    return out


def calendar(matter_id: str, today: date) -> tuple[list[TimelineEvent], list[ActionItem]]:
    events: list[TimelineEvent] = []
    upcoming: list[ActionItem] = []
    with connect() as conn:
        for row in _rows(conn, matter_id, "calendar_entry"):
            raw = _raw(row)
            d = iso(raw.get("start_at") or raw.get("start_date") or row["date"])
            if not d:
                continue
            label = raw.get("summary") or row["title"] or "Calendar entry"
            future = date.fromisoformat(d) >= today
            cit = row_citation(conn, row, label)
            events.append(TimelineEvent(date=d, label=label, kind="deadline" if future else "legal",
                                        is_future=future, citations=[cit]))
            if future and (date.fromisoformat(d) - today).days <= 45:
                upcoming.append(ActionItem(title=label, due_date=d, status="upcoming", citations=[cit]))
    return events, upcoming


def firm_spent(matter_id: str) -> Fact | None:
    total, cits, n = 0.0, [], 0
    with connect() as conn:
        for row in _rows(conn, matter_id, "expense"):
            raw = _raw(row)
            if (raw.get("type") or "").lower() == "timeentry":
                continue
            amt = raw.get("total")
            if amt is None and raw.get("price") is not None:
                amt = float(raw.get("price") or 0) * float(raw.get("quantity") or 1)
            if amt is None:
                continue
            total += float(amt)
            n += 1
            cits.append(row_citation(conn, row))
    if not n:
        return None
    return Fact(id="firm_spent", label="Firm costs advanced", value=f"${total:,.2f} across {n} expense entries",
                amount=round(total, 2), citations=cits, verified=True)


def last_client_contact(matter_id: str) -> Fact | None:
    with connect() as conn:
        m = conn.execute("SELECT client_name, raw_json FROM matters WHERE id = ?", (matter_id,)).fetchone()
        if not m:
            return None
        client = (_raw(m).get("client") or {}) if m["raw_json"] else {}
        client_id = client.get("id") if isinstance(client, dict) else None
        name = (m["client_name"] or "").strip()
        rows = conn.execute("SELECT * FROM sources WHERE matter_id = ? AND kind = 'communication'"
                            " ORDER BY date DESC", (matter_id,)).fetchall()
        for row in rows:
            raw = _raw(row)
            people = (raw.get("senders") or []) + (raw.get("receivers") or [])
            hit = any(isinstance(p, dict) and ((client_id and p.get("id") == client_id) or
                                               (name and fuzz.token_set_ratio(name, p.get("name") or "") >= 90))
                      for p in people)
            if hit:
                d = iso(raw.get("date") or raw.get("received_at") or row["date"])
                typ = (raw.get("type") or "").replace("Communication", "").strip() or "Contact"
                subj = raw.get("subject") or row["title"] or ""
                return Fact(id="last_client_contact", label="Last client contact",
                            value=f"{typ}: {subj}".strip(": "), date=d,
                            citations=[row_citation(conn, row, subj)], verified=True)
    return None


def recent_activity(matter_id: str, limit: int = 6) -> list[Fact]:
    out: list[Fact] = []
    with connect() as conn:
        rows = conn.execute("SELECT * FROM sources WHERE matter_id = ? AND kind IN ('note', 'communication')"
                            " AND date IS NOT NULL ORDER BY date DESC LIMIT ?", (matter_id, limit)).fetchall()
        for i, row in enumerate(rows):
            out.append(Fact(id=f"recent-{i}", label=row["kind"].capitalize(), value=row["title"] or "",
                            date=iso(row["date"]), citations=[row_citation(conn, row)], verified=True))
    return out


def provider_contact_ids(matter_id: str) -> list[tuple[str, str]]:
    """(contact_id, name) for every contact source, used to link treatment lines."""
    with connect() as conn:
        rows = conn.execute("SELECT id, title FROM sources WHERE matter_id = ? AND kind = 'contact'",
                            (matter_id,)).fetchall()
    return [(r["id"].split(":", 1)[-1], r["title"] or "") for r in rows]


def clio_stage(matter_id: str) -> str | None:
    with connect() as conn:
        m = conn.execute("SELECT raw_json FROM matters WHERE id = ?", (matter_id,)).fetchone()
    stage = (_raw(m).get("matter_stage") or {}) if m else {}
    return stage.get("name") if isinstance(stage, dict) else None
