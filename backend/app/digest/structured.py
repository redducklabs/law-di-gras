"""Deterministic mapping of structured Clio rows (tasks, calendar, expenses,
communications) into actions, timeline, firm spend and last client contact.

No LLM: these rows are already structured. Each item cites its own source row.
Field names follow Clio's v4 API; every read is defensive because S1 stores
the raw item JSON as-is.
"""

import json
import re
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


_BY_PARTY = re.compile(r"^\s*By\s+([^:]{2,60}):\s*(.+)$", re.I)


def waiting_party(title: str) -> str | None:
    """Clio task title convention "By <role>: <party> - <what>" → <party> (or <role> if no party)."""
    m = _BY_PARTY.match(title or "")
    if not m:
        return None
    rest = m.group(2)
    party = re.split(r"\s+[-–—]\s+", rest, maxsplit=1)
    return party[0].strip() if len(party) == 2 and party[0].strip() else m.group(1).strip()


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
            waiting_on = waiting_party(raw.get("name") or row["title"] or "")
            if waiting_on is None and isinstance(assignee, dict) and (assignee.get("type") or "").lower() == "contact":
                waiting_on = owner
            # status is a pure function of due date + who holds the ball: stable across digests
            if due and date.fromisoformat(due) < today:
                st = "overdue"
            elif waiting_on:
                st = "waiting"
            else:
                st = "upcoming"
            out.append(ActionItem(title=raw.get("name") or row["title"] or "Task", due_date=due, owner=owner,
                                  status=st, waiting_on=waiting_on, citations=[row_citation(conn, row)]))
    return out


_CAL_LEGAL_DATE = re.compile(r"(?<![a-z])(deadline|due|limitations?|trial|hearing|conference|deposition|ebt|"
                             r"mediation|arbitration|motion|filing|ime)(?![a-z])", re.I)
_CAL_CLINICAL = re.compile(r"(?<![a-z])(surgery|surgical|arthroscopy|operative|consultation|follow-up|therapy|"
                           r"treatment|chiropractic|physical therapy|injection|mri|x-ray|visit)(?![a-z])", re.I)


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
            if _CAL_LEGAL_DATE.search(label):
                kind = "deadline" if future else "legal"
            elif _CAL_CLINICAL.search(label):
                kind = "treatment"
            else:
                kind = "legal"
            # A past calendar entry is the firm's plan, not proof it happened.
            shown = label if future else f"Calendar: {label}"
            events.append(TimelineEvent(date=d, label=shown, kind=kind, is_future=future, citations=[cit]))
            if future and (date.fromisoformat(d) - today).days <= 45:
                upcoming.append(ActionItem(title=label, due_date=d, status="upcoming", citations=[cit]))
    return events, upcoming


# Expense entries mix true case costs with medical bills logged for tracking.
# Classified from the entry's own leading label + billable flag, never by name.
_W = r"(?<![a-z])({})(?![a-z])"
_MED_WORDS = re.compile(_W.format("medical|treatment|hospital|physician|therapy|chiropractic|radiology|"
                                  "surgical|surgery|clinic|ambulance|pharmacy|imaging"), re.I)
_BILL_WORDS = re.compile(_W.format("charges?|bills?|billed|services?|balance"), re.I)
_NOT_NAME = re.compile(r"\d|\.pdf|" + _W.format("payment|status|charges?|unknown"), re.I)
_DATE_RANGE = re.compile(r"(\d{4}-\d{2}-\d{2})(?:\s*(?:to|-|through)\s*(\d{4}-\d{2}-\d{2}))?")


def _amount(raw: dict) -> float | None:
    if raw.get("total") is not None:
        return float(raw["total"])
    if raw.get("price") is not None:
        return float(raw.get("price") or 0) * float(raw.get("quantity") or 1)
    return None


def _note(row, raw: dict) -> str:
    return (raw.get("note") or raw.get("activity_description") or row["title"] or "").strip()


def _lead_label(note: str) -> str:
    return re.split(r":|\s-\s|;", note, maxsplit=1)[0]


def is_medical_charge(row, raw: dict) -> bool:
    cat = raw.get("expense_category")
    cat = cat.get("name", "") if isinstance(cat, dict) else (cat or "")
    lead = f"{cat} {_lead_label(_note(row, raw))}"
    if _MED_WORDS.search(lead) and _BILL_WORDS.search(lead):
        return True
    return bool(raw.get("non_billable")) and bool(_MED_WORDS.search(lead))


def _provider_from_note(note: str) -> str | None:
    """The first ';'-separated segment that reads like a name (no digits, no status words, no file)."""
    for seg in [x.strip() for x in note.split(";")[1:]]:
        if seg and not _NOT_NAME.search(seg):
            return seg
    return None


def _expenses(matter_id: str):
    with connect() as conn:
        for row in _rows(conn, matter_id, "expense"):
            raw = _raw(row)
            if (raw.get("type") or "").lower() == "timeentry":
                continue
            amt = _amount(raw)
            if amt is not None:
                yield conn, row, raw, amt


def _amount_citation(conn, row, amt: float, extra_quote: str | None = None) -> list[Citation]:
    cits = []
    for q in (f"${amt:,.2f}", extra_quote):
        if q:
            c = locate(conn, row["id"], q)
            if c and c.verified:
                cits.append(c)
    return cits or [row_citation(conn, row)]


def medical_charges(matter_id: str) -> list[dict]:
    """Per-entry medical bills logged as non-billable expenses: provider, amount, service dates, citations."""
    out = []
    for conn, row, raw, amt in _expenses(matter_id):
        if not is_medical_charge(row, raw):
            continue
        note = _note(row, raw)
        provider = _provider_from_note(note)
        m = _DATE_RANGE.search(note.split(";", 2)[-1]) if ";" in note else None
        out.append({"provider": provider, "amount": amt,
                    "first": iso(m.group(1)) if m else iso(raw.get("date")),
                    "last": iso(m.group(2) or m.group(1)) if m else None,
                    "citations": _amount_citation(conn, row, amt, provider) + (
                        [c for c in [locate(conn, row["id"], m.group(0))] if c and c.verified] if m else [])})
    return out


def firm_spent(matter_id: str) -> Fact | None:
    """True case costs only (filing, records, experts...), excluding medical bills."""
    total, cits, n = 0.0, [], 0
    for conn, row, raw, amt in _expenses(matter_id):
        if is_medical_charge(row, raw):
            continue
        total += amt
        n += 1
        cits.append(row_citation(conn, row))
    if not n:
        return None
    return Fact(id="firm_spent", label="Firm costs advanced", value=f"${total:,.2f} across {n} cost entries",
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
