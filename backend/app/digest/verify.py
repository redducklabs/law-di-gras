"""Deterministic token verification shared by facts, headline, recent activity and drafts.

Every date, $ amount, code/claim number and person/org name in generated text must appear in
the evidence it cites. Names may also come from a separate names corpus (contacts, titles).
"""

import re
from datetime import date, datetime

from rapidfuzz import fuzz

from app.digest.spans import fold



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


def check_tokens(text: str, corpus: Corpus, names: Corpus | None = None) -> list[str]:
    """Tokens in `text` the corpus does not support. `names` (contacts, source titles) may also
    support person/org names, never dates or amounts."""
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
        if names is not None and (names.has(name) or fuzz.partial_ratio(fold(name)[0], names.folded) >= 92):
            continue
        bad.append(name)
    return list(dict.fromkeys(bad))


# --- claim-level check (beyond tokens) -------------------------------------

import hashlib  # noqa: E402

from pydantic import BaseModel  # noqa: E402

from app.db import connect  # noqa: E402
from app.llm import MODEL_SONNET, structured  # noqa: E402
from app.retrieval.fence import FENCE_RULE  # noqa: E402


class Judged(BaseModel):
    index: int
    unsupported: list[str]   # clauses/characterizations not stated in the quotes
    supported_text: str      # the statement with unsupported parts removed; "" if nothing remains


class JudgeOut(BaseModel):
    results: list[Judged]


JUDGE_SYSTEM = (
    "You are a strict fact-checker for a litigation team. A statement is supported only by what its "
    "quotes say. Same meaning in other words is fine; any added detail, count, date, name, cause, "
    "characterization, attribution (who said or wanted what) or conclusion is unsupported. "
    "Each quote is prefixed with its [source title]; an attribution such as 'Defense IME (Dr. X):' is "
    "supported when that source title or text identifies the source. In supported_text NEVER drop an "
    "attribution while keeping what it attributes: keep both, or remove both, so one party's opinion "
    "is never presented as another's. "
    + FENCE_RULE
)

JUDGE_PROMPT = """For each statement, list the unsupported parts (short phrases copied from the statement),
and give supported_text: the statement rewritten to keep ONLY what its quotes support, adding nothing
(use the statement's own words where possible; "" if nothing is supported).

{items}"""


def judge_claims(matter_id: str, items: list[tuple[str, list[str]]], purpose: str) -> list[Judged]:
    """One Sonnet call for all statements, cached by content."""
    blocks = []
    for i, (text, quotes) in enumerate(items):
        q = "\n".join(f"  - {x}" for x in quotes) or "  (no quotes)"
        blocks.append(f'<case_record id="{i}">\nSTATEMENT: {text}\nQUOTES:\n{q}\n</case_record>')
    prompt = JUDGE_PROMPT.format(items="\n\n".join(blocks))
    key = "judge:" + hashlib.sha256((JUDGE_SYSTEM + prompt).encode()).hexdigest()[:24]
    with connect() as conn:
        row = conn.execute("SELECT payload_json FROM digests WHERE matter_id = ? AND kind = ?", (matter_id, key)).fetchone()
    if row:
        out = JudgeOut.model_validate_json(row["payload_json"])
    else:
        out = structured(MODEL_SONNET, JudgeOut, JUDGE_SYSTEM, prompt, purpose=purpose, matter_id=matter_id,
                         effort="medium", max_tokens=6000)
        with connect() as conn:
            conn.execute("INSERT OR REPLACE INTO digests (matter_id, kind, input_hash, payload_json, model, created_at)"
                         " VALUES (?, ?, ?, ?, ?, datetime('now'))", (matter_id, key, key, out.model_dump_json(), MODEL_SONNET))
    by = {r.index: r for r in out.results}
    return [by.get(i) or Judged(index=i, unsupported=[], supported_text=t) for i, (t, _) in enumerate(items)]
