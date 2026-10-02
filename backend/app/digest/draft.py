"""Grounded drafts for a next step (email/letter text the attorney reviews; never sent).

Sonnet writes segments over the step's own citations + top retrieved passages.
Then deterministic checks:
  1. every `fact` segment's quote must span-match its source (spans.locate);
  2. every date, $ amount, code/claim number and person/org name in ANY segment
     must appear in the evidence text or the matter's contacts.
One regenerate with the failures listed; anything still failing is replaced by
"[verify: …]" and the segment is marked verified=false.
"""

import hashlib
import re
from datetime import date, datetime

from pydantic import BaseModel
from rapidfuzz import fuzz

from app.db import connect
from app.digest import dashboard as dash
from app.digest.spans import fold, locate
from app.llm import MODEL_SONNET, structured
from app.retrieval.fence import FENCE_RULE, fence
from app.retrieval.search import search_hits
from app.schemas import ActionItem, Citation, Draft, DraftSegment

VERSION = "dr2"


class Ev(BaseModel):
    passage_id: int
    quote: str


class Seg(BaseModel):
    text: str
    kind: str  # fact | ask | courtesy
    evidence: list[Ev]


class DraftOut(BaseModel):
    subject: str
    segments: list[Seg]


SYSTEM = (
    "You draft short professional correspondence for a personal-injury firm, for attorney review "
    "before anything is sent. Write as the firm. Split the message into segments: 'fact' segments "
    "state something from the record and MUST carry evidence quotes copied character-for-character "
    "from the numbered passages; 'ask' segments make the request; 'courtesy' segments are greetings "
    "and sign-off without any facts. Use only names, dates, amounts and reference numbers that appear "
    "in the passages. Never invent a date, deadline, amount, claim number or name. "
    + FENCE_RULE
)

PROMPT = """Today is {today}. Next step to move forward:
<case_record id="step">
{step}
</case_record>

Passages (the only record you may rely on):

{passages}

Write a concise message (subject + 3-7 segments) addressed to {recipient} that moves this step
forward. Plain, courteous, specific. Sign off as "the firm" (no invented staff names).{retry}"""


# --- token checks ------------------------------------------------------------

_MONTHS = "january february march april may june july august september october november december".split()
_MON = r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\.?"
_DATE_PATTERNS = [
    re.compile(r"\b\d{4}-\d{2}-\d{2}\b"),
    re.compile(r"\b\d{1,2}/\d{1,2}/\d{2,4}\b"),
    re.compile(rf"\b{_MON}\s+\d{{1,2}}(?:st|nd|rd|th)?,?\s+\d{{4}}\b"),
    re.compile(rf"\b\d{{1,2}}\s+{_MON}\s+\d{{4}}\b"),
]
_MONEY = re.compile(r"\$\s?\d[\d,]*(?:\.\d{2})?(?:\s?(?:k|K|million|M)\b)?")
_CODE = re.compile(r"\b(?=[A-Za-z0-9-]*\d)(?=[A-Za-z0-9-]*[A-Za-z])[A-Za-z0-9][A-Za-z0-9-]{3,}\b|\b\d{5,}\b")
_NAME = re.compile(r"\b(?:Dr\.\s+)?[A-Z][a-zA-Z'&.-]+(?:\s+(?:of|and|&|the|de|van)?\s*[A-Z][a-zA-Z'&.,-]+){1,5}")
_COMMON = set("""on in at for by from to with dear hi hello thank thanks please regards best sincerely kind re subject the a an we our
this that as per following attached regarding hope following could would can let i you your
monday tuesday wednesday thursday friday saturday sunday january february march april may june july
august september october november december firm counsel""".split())


def _to_iso(tok: str) -> str | None:
    t = tok.strip().replace(",", " ")
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y"):
        try:
            return datetime.strptime(tok.strip(), fmt).date().isoformat()
        except ValueError:
            pass
    parts = re.findall(r"[A-Za-z]+|\d+", t)
    try:
        if parts[0].isalpha():
            mon, day, yr = parts[0], int(parts[1]), int(parts[-1])
        else:
            day, mon, yr = int(parts[0]), parts[1], int(parts[-1])
        m = next(i for i, name in enumerate(_MONTHS, 1) if name.startswith(mon.lower()[:3]))
        return date(yr, m, day).isoformat()
    except (StopIteration, ValueError, IndexError):
        return None


def _money_val(tok: str) -> float | None:
    m = re.search(r"\d[\d,]*(?:\.\d+)?", tok)
    if not m:
        return None
    v = float(m.group(0).replace(",", ""))
    if re.search(r"(k|K)\b", tok):
        v *= 1000
    elif re.search(r"million|M\b", tok):
        v *= 1_000_000
    return v


class Corpus:
    def __init__(self, text: str):
        self.text = text
        self.folded = fold(text)[0]
        self.dates = {d for p in _DATE_PATTERNS for tok in p.findall(text) if (d := _to_iso(tok))}
        self.money = {v for tok in _MONEY.findall(text) if (v := _money_val(tok)) is not None}
        # bare numbers like "Rate: 3,475.00" count as amounts too
        self.money |= {float(x.replace(",", "")) for x in re.findall(r"\b\d{1,3}(?:,\d{3})+(?:\.\d{2})?\b", text)}

    def has(self, tok: str) -> bool:
        return fold(tok)[0] in self.folded


def _names(text: str) -> list[str]:
    out = []
    for m in _NAME.finditer(text):
        words = m.group(0).strip(" ,.").split()
        while words and words[0].lower().strip(".,") in _COMMON:
            words = words[1:]
        if len(words) >= 2 and not all(w.lower().strip(".,") in _COMMON for w in words):
            out.append(" ".join(words))
    return out


def check_tokens(text: str, corpus: Corpus) -> list[str]:
    """Tokens in `text` the corpus does not support."""
    bad: list[str] = []
    for p in _DATE_PATTERNS:
        for tok in p.findall(text):
            iso = _to_iso(tok)
            if not (iso and iso in corpus.dates) and not corpus.has(tok):
                bad.append(tok)
    for tok in _MONEY.findall(text):
        v = _money_val(tok)
        if v is None or not any(abs(v - x) < 0.01 for x in corpus.money):
            bad.append(tok.strip())
    for tok in _CODE.findall(text):
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", tok) or re.fullmatch(r"(19|20)\d{2}", tok):
            continue
        if any(tok in b for b in bad) or corpus.has(tok):
            continue
        bad.append(tok)
    for name in _names(text):
        if corpus.has(name) or fuzz.partial_ratio(fold(name)[0], corpus.folded) >= 92:
            continue
        bad.append(name)
    return list(dict.fromkeys(bad))


# --- evidence ---------------------------------------------------------------

def _source_text(conn, source_id: str, page: int | None) -> str:
    if page:
        r = conn.execute("SELECT text FROM pages WHERE source_id = ? AND page_no = ?", (source_id, page)).fetchone()
        if r:
            return r["text"] or ""
    r = conn.execute("SELECT text FROM sources WHERE id = ?", (source_id,)).fetchone()
    return (r["text"] or "") if r else ""


def _evidence(matter_id: str, action: ActionItem) -> list[dict]:
    ev: list[dict] = []
    seen = set()
    with connect() as conn:
        for c in action.citations:
            key = (c.source_id, c.page)
            if key in seen:
                continue
            seen.add(key)
            ev.append({"source_id": c.source_id, "page": c.page, "title": c.source_title, "date": c.date,
                       "text": _source_text(conn, c.source_id, c.page)[:5000]})
    q = f"{action.title} {action.waiting_on or ''}".strip()
    for h in search_hits(matter_id, q, top_k=6):
        key = (h.source_id, h.page_no)
        if key in seen:
            continue
        seen.add(key)
        ev.append({"source_id": h.source_id, "page": h.page_no, "title": h.title, "date": None, "text": h.text})
    return ev


def _contacts(matter_id: str) -> str:
    with connect() as conn:
        rows = conn.execute("SELECT title FROM sources WHERE matter_id = ? AND kind = 'contact'", (matter_id,)).fetchall()
        m = conn.execute("SELECT client_name FROM matters WHERE id = ?", (matter_id,)).fetchone()
    return "\n".join([r[0] or "" for r in rows] + [m[0] if m and m[0] else ""])


def _pick_action(matter_id: str, action_index: int | None, title: str | None) -> ActionItem:
    d = dash.cached(matter_id)
    if d is None:
        raise LookupError("no dashboard yet; POST /digest first")
    if action_index is not None and 0 <= action_index < len(d.actions):
        return d.actions[action_index]
    if title:
        best = max(d.actions, key=lambda a: fuzz.token_set_ratio(title, a.title), default=None)
        if best and fuzz.token_set_ratio(title, best.title) >= 70:
            return best
    raise LookupError("action not found")


# --- main -------------------------------------------------------------------

def _verify(out: DraftOut, ev: list[dict], contacts: str, conn) -> tuple[list[DraftSegment], dict[int, list[str]]]:
    all_corpus = Corpus("\n".join(e["text"] for e in ev) + "\n" + contacts)
    segs: list[DraftSegment] = []
    failures: dict[int, list[str]] = {}
    for i, s in enumerate(out.segments):
        kind = s.kind if s.kind in ("fact", "ask", "courtesy") else "ask"
        cits: list[Citation] = []
        for e in s.evidence:
            if 0 <= e.passage_id < len(ev):
                c = locate(conn, ev[e.passage_id]["source_id"], e.quote, ev[e.passage_id]["page"])
                if c:
                    cits.append(c)
        fails = []
        if kind == "fact" and not any(c.verified for c in cits):
            fails.append("fact segment has no verbatim quote from the passages")
        if kind == "fact" and any(c.verified for c in cits):
            cited = "\n".join(_source_text(conn, c.source_id, c.page) for c in cits if c.verified)
            corpus = Corpus(cited + "\n" + contacts)
        else:
            corpus = all_corpus
        fails += check_tokens(s.text, corpus)
        if fails:
            failures[i] = fails
        segs.append(DraftSegment(text=s.text.strip(), kind=kind, citations=[c for c in cits if c.verified],
                                 verified=not fails))
    return segs, failures


def draft(matter_id: str, action_index: int | None = None, title: str | None = None) -> Draft:
    action = _pick_action(matter_id, action_index, title)
    ev = _evidence(matter_id, action)
    contacts = _contacts(matter_id)
    step = action.model_dump_json(include={"title", "due_date", "owner", "status", "waiting_on"})
    passages = "\n\n".join(fence(i, f'title="{(e["title"] or "")[:120]}" date="{e["date"] or ""}"', e["text"], cap=5000)
                           for i, e in enumerate(ev))
    ih = hashlib.sha256((VERSION + step + passages + contacts).encode()).hexdigest()
    key = f"draft:{ih[:24]}"
    with connect() as conn:
        row = conn.execute("SELECT payload_json FROM digests WHERE matter_id = ? AND kind = ?", (matter_id, key)).fetchone()
    if row:
        return Draft.model_validate_json(row["payload_json"])

    recipient = action.waiting_on or "the appropriate party named in the record"
    base = dict(today=date.today().isoformat(), step=step, passages=passages, recipient=recipient)
    out = structured(MODEL_SONNET, DraftOut, SYSTEM, PROMPT.format(**base, retry=""), purpose="draft",
                     matter_id=matter_id, effort="medium", max_tokens=4000)
    with connect() as conn:
        segs, failures = _verify(out, ev, contacts, conn)
        if failures:
            listed = "\n".join(f"- segment {i + 1} (\"{out.segments[i].text[:80]}\"): {', '.join(f)}"
                               for i, f in failures.items())
            retry = ("\n\nYour previous draft failed verification. Fix or remove these; every fact needs a "
                     f"verbatim quote, and every name/date/amount/number must be in the passages:\n{listed}")
            out = structured(MODEL_SONNET, DraftOut, SYSTEM, PROMPT.format(**base, retry=retry),
                             purpose="draft_retry", matter_id=matter_id, effort="medium", max_tokens=4000)
            segs, failures = _verify(out, ev, contacts, conn)

    unverified: list[str] = []
    for i, f in failures.items():
        seg = segs[i]
        for tok in f:
            if tok.startswith("fact segment"):
                unverified.append(f"Unsupported statement: {seg.text[:120]}")
            elif tok in seg.text:
                seg.text = seg.text.replace(tok, f"[verify: {tok}]")
                unverified.append(tok)
        seg.verified = False
    subject = out.subject.strip()
    for tok in check_tokens(subject, Corpus("\n".join(e["text"] for e in ev) + "\n" + contacts)):
        subject = subject.replace(tok, f"[verify: {tok}]")
        unverified.append(tok)
    result = Draft(subject=subject, segments=segs, unverified=list(dict.fromkeys(unverified)))
    with connect() as conn:
        conn.execute("INSERT OR REPLACE INTO digests (matter_id, kind, input_hash, payload_json, model, created_at)"
                     " VALUES (?, ?, ?, ?, ?, datetime('now'))", (matter_id, key, ih, result.model_dump_json(), MODEL_SONNET))
    return result
