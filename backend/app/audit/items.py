"""Flatten the cached Dashboard into on-screen items, and pull source context for citations."""

import json
import re
from dataclasses import dataclass, field
from datetime import date

from app.db import connect
from app.digest.spans import find_span, fold
from app.schemas import Citation, Dashboard

MONTHS = {m: i + 1 for i, m in enumerate(
    ["january", "february", "march", "april", "may", "june", "july", "august",
     "september", "october", "november", "december"])}
MONTHS.update({k[:3]: v for k, v in list(MONTHS.items())})
MONTHS["sept"] = 9


@dataclass
class Item:
    id: str            # stable path, e.g. timeline[3]
    section: str       # headline | timeline | kpi | action | injury | treatment | recent | contact
    text: str          # what the screen says
    date: str | None
    citations: list[Citation] = field(default_factory=list)
    extra: dict = field(default_factory=dict)


def load_dashboard(matter_id: str) -> tuple[Dashboard, str]:
    with connect() as conn:
        row = conn.execute("SELECT payload_json, created_at FROM digests WHERE matter_id=? AND kind='dashboard'",
                           (matter_id,)).fetchone()
    if not row:
        raise LookupError("no cached dashboard")
    return Dashboard.model_validate_json(row["payload_json"]), row["created_at"]


def flatten(d: Dashboard) -> list[Item]:
    out: list[Item] = []
    h = d.headline
    out.append(Item("headline.status_line", "headline", f"[stage: {h.stage}] {h.status_line}", None,
                    [c for b in h.bullets for c in b.citations], {"no_own_citations": True}))
    for i, b in enumerate(h.bullets):
        out.append(Item(f"headline.bullets[{i}]", "headline", f"{b.label}: {b.value}", b.date, b.citations))
    for i, e in enumerate(d.timeline):
        out.append(Item(f"timeline[{i}]", "timeline",
                        f"{e.date} | {e.label} | kind={e.kind} | placed {'in the future' if e.is_future else 'before today'}"
                        f"{' | major' if e.major else ''}", e.date, e.citations,
                        {"label": e.label, "kind": e.kind, "is_future": e.is_future}))
    k = d.kpis
    for name, f in [("specials", k.specials), ("case_value", k.case_value), ("firm_spent", k.firm_spent)]:
        if f:
            out.append(Item(f"kpis.{name}", "kpi", f"{f.label}: {f.value}", f.date, f.citations, {"amount": f.amount}))
    for i, f in enumerate(k.coverage):
        out.append(Item(f"kpis.coverage[{i}]", "kpi", f"{f.label}: {f.value}", f.date, f.citations, {"amount": f.amount}))
    for i, f in enumerate(k.liens):
        out.append(Item(f"kpis.liens[{i}]", "kpi", f"{f.label}: {f.value} (amount {f.amount})", f.date, f.citations,
                        {"amount": f.amount}))
    for i, a in enumerate(d.actions):
        out.append(Item(f"actions[{i}]", "action",
                        f"[{a.status}] {a.title} | due {a.due_date} | owner {a.owner} | waiting on {a.waiting_on}",
                        a.due_date, a.citations, {"status": a.status}))
    if d.last_client_contact:
        f = d.last_client_contact
        out.append(Item("last_client_contact", "contact", f"{f.label}: {f.value} ({f.date})", f.date, f.citations))
    for i, f in enumerate(d.injuries):
        out.append(Item(f"injuries[{i}]", "injury", f"{f.label}: {f.value} (date {f.date})", f.date, f.citations))
    for i, t in enumerate(d.treatment):
        billed = t.billed.value if t.billed else None
        cits = list(t.citations) + (list(t.billed.citations) if t.billed else [])
        out.append(Item(f"treatment[{i}]", "treatment",
                        f"{t.provider}: first visit {t.first_visit}, last visit {t.last_visit}, "
                        f"visits {t.visit_count}, billed {billed}", None, cits,
                        {"provider": t.provider, "first": t.first_visit, "last": t.last_visit,
                         "billed": t.billed.amount if t.billed else None}))
    for i, f in enumerate(d.recent):
        out.append(Item(f"recent[{i}]", "recent", f"{f.label}: {f.value} ({f.date})", f.date, f.citations))
    return out


# ---------- source text ----------

_src_cache: dict[str, dict] = {}


def source(source_id: str) -> dict | None:
    if source_id not in _src_cache:
        with connect() as conn:
            r = conn.execute("SELECT id, kind, title, date, text, raw_json, page_count FROM sources WHERE id=?",
                             (source_id,)).fetchone()
            pages = {p["page_no"]: p["text"] or "" for p in conn.execute(
                "SELECT page_no, text FROM pages WHERE source_id=?", (source_id,))} if r else {}
        _src_cache[source_id] = {**dict(r), "pages": pages} if r else None
    return _src_cache[source_id]


def cited_text(c: Citation) -> str:
    s = source(c.source_id)
    if not s:
        return ""
    if c.page and s["pages"].get(c.page):
        return s["pages"][c.page]
    return s["text"] or ""


def span_check(c: Citation) -> tuple[bool, str]:
    """Does the quote occur verbatim (normalized) in the cited page/source?"""
    s = source(c.source_id)
    if not s:
        return False, "cited source not in DB"
    text = cited_text(c)
    if find_span(c.quote, text):
        fq, _ = fold(c.quote)
        ft, _ = fold(text)
        return True, "exact" if fq.strip(" .\"") in ft else "fuzzy"
    if c.page and find_span(c.quote, s["text"] or ""):
        return False, f"quote is in the document but not on cited page {c.page}"
    return False, "quote not found in source"


def context(c: Citation, width: int = 450) -> str:
    """Quote with surrounding source text, so the judge sees tense/negation/party."""
    text = cited_text(c)
    sp = find_span(c.quote, text)
    if not sp:
        return c.quote
    a, b = max(0, sp[0] - width), min(len(text), sp[1] + width)
    return ("…" if a else "") + text[a:sp[0]] + "⟦" + text[sp[0]:sp[1]] + "⟧" + text[sp[1]:b] + ("…" if b < len(text) else "")


# ---------- dates and amounts ----------

_D_ISO = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b")
_D_US = re.compile(r"\b(\d{1,2})/(\d{1,2})/(\d{2,4})\b")
_D_MY = re.compile(r"\b(\d{1,2})/(\d{4})\b")
_D_MDY = re.compile(r"\b(" + "|".join(sorted(MONTHS, key=len, reverse=True)) + r")\.?\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+(\d{4})\b", re.I)
_D_DMY = re.compile(r"\b(\d{1,2})(?:st|nd|rd|th)?\s+(?:day\s+of\s+)?(" + "|".join(sorted(MONTHS, key=len, reverse=True)) + r")\.?,?\s+(\d{4})\b", re.I)
_D_MONY = re.compile(r"\b(" + "|".join(sorted(MONTHS, key=len, reverse=True)) + r")\.?,?\s+(\d{4})\b", re.I)


def dates_in(text: str) -> set[tuple[int, int, int | None]]:
    """(year, month, day|None) for every date-like token."""
    t = re.sub(r"\s+", " ", text or "")
    out: set = set()
    for y, m, d in _D_ISO.findall(t):
        out.add((int(y), int(m), int(d)))
    for m, d, y in _D_US.findall(t):
        y = int(y) + (2000 if len(y) == 2 else 0)
        if 1 <= int(m) <= 12:
            out.add((y, int(m), int(d)))
    for m, y in _D_MY.findall(t):
        if 1 <= int(m) <= 12:
            out.add((int(y), int(m), None))
    for mo, d, y in _D_MDY.findall(t):
        out.add((int(y), MONTHS[mo.lower()], int(d)))
    for d, mo, y in _D_DMY.findall(t):
        out.add((int(y), MONTHS[mo.lower()], int(d)))
    for mo, y in _D_MONY.findall(t):
        out.add((int(y), MONTHS[mo.lower()], None))
    return out


def date_supported(want: tuple, have: set) -> bool:
    y, m, d = want
    return any(h[0] == y and h[1] == m and (d is None or h[2] is None or h[2] == d) for h in have)


_AMT = re.compile(r"\$\s?([\d,]+(?:\.\d{2})?)\s*(k|K|m|M)?")


def amounts_in(text: str) -> set[float]:
    out = set()
    for num, suf in _AMT.findall(text or ""):
        try:
            v = float(num.replace(",", ""))
        except ValueError:
            continue
        v *= {"k": 1e3, "m": 1e6}.get(suf.lower(), 1) if suf else 1
        out.add(round(v, 2))
    return out


def citation_dates(c: Citation) -> set:
    """Dates the citation can vouch for: its quote, plus the structured date of a Clio record
    (calendar/task/note/communication/expense dates are fields, not prose)."""
    have = dates_in(c.quote)
    if c.source_kind != "document" and c.date:
        have |= dates_in(c.date[:10])
    return have


def today() -> str:
    return date.today().isoformat()


def raw(source_id: str) -> dict:
    s = source(source_id)
    try:
        return json.loads(s["raw_json"] or "{}") if s else {}
    except Exception:
        return {}
