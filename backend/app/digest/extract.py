"""Per-category fact extraction over retrieved evidence (Sonnet, schema-enforced).

Each category runs a few generic retrieval queries, fences the passages as data
(A8), and asks Sonnet for items that each carry verbatim quotes tied to a
passage id. spans.locate() then checks every quote against the source text, so
`verified` is decided by string matching, never by the model.

Nothing about any specific case lives here: queries and instructions are
generic PI vocabulary.
"""

import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field

from pydantic import BaseModel

from app.db import connect
from app.digest.spans import locate
from app.llm import MODEL_SONNET, structured
from app.retrieval.fence import FENCE_RULE, fence
from app.retrieval.search import Hit, search_hits
from app.schemas import Citation

PROMPT_VERSION = "x3"


class Evidence(BaseModel):
    passage_id: int
    quote: str  # copied character-for-character from the passage


class Item(BaseModel):
    label: str
    value: str
    amount: float | None = None
    date: str | None = None       # YYYY-MM-DD
    end_date: str | None = None   # YYYY-MM-DD
    party: str | None = None
    count: int | None = None
    status: str | None = None     # key dates: occurred | scheduled | adjourned | deadline | unknown
    evidence: list[Evidence]


class Extraction(BaseModel):
    items: list[Item]


@dataclass
class Category:
    key: str
    queries: list[str]
    instructions: str
    top_k: int = 8


CATEGORIES = [
    Category("incident", [
        "date and location of the accident or incident",
        "how the collision happened, mechanism of injury",
        "police report narrative and fault or liability",
        "defendant or at-fault party, other driver, vehicle",
    ], "Extract the incident: one item labeled 'Incident date' (date=the incident date, value=short "
       "description), one 'Location' item, one 'Mechanism' item (how it happened), and one 'Liability' item "
       "if fault or liability is discussed (party=at-fault party)."),
    Category("injuries", [
        "diagnosed injuries and diagnoses",
        "MRI X-ray imaging findings",
        "patient complaints of pain, symptoms",
        "surgery or injections recommended, prognosis, permanent impairment",
    ], "Extract each distinct injury or diagnosis as one item: label=short injury name (e.g. body part + "
       "condition), value=one-line clinical description, date=date first documented if stated. Merge "
       "duplicates of the same injury. Skip symptoms already covered by a diagnosis. Only the client's "
       "injuries as documented by treating providers, imaging or hospital records. Do NOT list findings or "
       "opinions from a defense / independent medical examination (IME) or defense expert as the client's "
       "injuries; if such an opinion disputes an injury, put it in that injury's value as 'Defense IME "
       "(<doctor>): <what they said, in their words>', scoped to the exact side and body part that opinion "
       "addresses (e.g. 'left knee'); never attach a one-sided opinion to a bilateral finding without saying "
       "which side. Never call something 'no injury' unless a quote says "
       "exactly that. The value must not add procedures, dates or findings that its quotes do not state.",
       top_k=10),
    Category("treatment", [
        "medical provider treatment visits and dates of service",
        "physical therapy chiropractic sessions number of visits",
        "medical bills total charges billed amount",
        "itemized billing statement balance owed",
        "hospital emergency room urgent care visit",
        "orthopedic pain management specialist referral",
    ], "Extract one item per treating medical provider (facility or practice): label=provider name, "
       "party=provider name, date=first date of service, end_date=last date of service, count=number of "
       "visits if stated or countable, amount=total billed by that provider if stated, value=one-line summary "
       "of the treatment. Only include amounts explicitly stated in the passages.", top_k=12),
    Category("coverage", [
        "insurance policy limits bodily injury liability coverage",
        "insurance adjuster claim number carrier",
        "uninsured underinsured motorist UM UIM coverage",
        "med pay PIP personal injury protection",
        "declarations page policy limits per person per accident",
    ], "Extract each insurance coverage. value is shown in large type on a tile, so it must be ONLY the "
       "limits, max ~30 characters: e.g. '$100,000 / $300,000', '$50,000 PIP', 'Self-insured; no stated limit', "
       "'Exhausted ($50,000)'. label=coverage type, carrier and whose policy, plus claim number when stated "
       "(e.g. 'BI liability · <carrier> · defendant · claim <no>'). party=carrier, amount=per-person limit in "
       "dollars if stated. Attribute each coverage to the party the quoted source itself names (its sender, "
       "claim or claim administrator); never assign one party's limits to another party. If sources state "
       "different limits for the same party, extract each as its own item."),
    Category("liens", [
        "medical lien letter of protection",
        "health insurance subrogation reimbursement claim",
        "Medicare Medicaid conditional payment lien",
        "lien amount asserted against settlement",
    ], "Extract each lien or reimbursement claim against the recovery: label=lienholder, party=lienholder, "
       "amount=lien amount if stated, value=type and status of the lien."),
    Category("key_dates", [
        "statute of limitations deadline",
        "demand letter sent date",
        "complaint filed lawsuit served",
        "deposition mediation trial hearing date scheduled",
        "important upcoming deadline",
    ], "Extract key legal and case dates: label=what the date is (e.g. 'Statute of limitations', 'Demand "
       "sent', 'Deposition'), date=the date, value=one-line description. Only dates that are explicitly "
       "stated. Skip the incident date itself, treatment visit dates, and routine internal task due dates. "
       "Set status from the quoted wording itself: 'occurred' only if the passage says it happened (was held, "
       "was taken, was filed, was sent, attended); 'scheduled' if the passage only schedules, notices, "
       "subpoenas, commands or sets it; 'adjourned' if it was adjourned, cancelled or postponed; 'unknown' "
       "otherwise. A notice or subpoena dated earlier that sets a later date is 'scheduled', never 'occurred'. "
       "Use 'deadline' for a limit or due date (statute of limitations, notice-of-claim period, discovery "
       "cutoff, response due), which neither occurs nor is scheduled. date must be the date of the event or "
       "the stated due date itself, never the date the document was written; if a due date is only relative "
       "(e.g. 'within 15 days'), skip the item."),
    Category("requests", [
        "waiting on records or bills from provider",
        "requested medical records and billing, follow up",
        "outstanding items needed from client",
        "awaiting response from insurance adjuster",
    ], "Extract open requests where the firm is waiting on someone else (records, bills, signatures, "
       "responses, documents). label=what is outstanding, party=who the firm is waiting on, date=date "
       "requested or follow-up due if stated, value=one-line status. Skip requests the passages show as "
       "fulfilled."),
    Category("stage", [
        "settlement demand offer negotiation",
        "treatment completed released maximum medical improvement",
        "litigation lawsuit filed discovery",
        "case status update next steps",
    ], "Extract signals of where the case stands (treatment ongoing/complete, demand prepared/sent, offers, "
       "negotiation, litigation). label=the signal (e.g. 'Demand sent', 'Offer received', 'Treatment "
       "ongoing'), date=when, amount=dollar amount if an offer or demand amount is stated, value=one-line "
       "description."),
]

SYSTEM = (
    "You extract facts from a personal-injury case file for the firm's attorneys and paralegals. "
    "Courtroom-grade accuracy: report only what the passages state. Every item needs at least one "
    "evidence quote copied character-for-character from the passage it came from (a short exact span, "
    "10-200 characters, no ellipses, no paraphrase), with that passage's id. If the passages do not "
    "support an item, leave it out. Dates are YYYY-MM-DD. Amounts are plain numbers in US dollars. "
    + FENCE_RULE
)


@dataclass
class Extracted:
    category: str
    label: str
    value: str
    amount: float | None
    date: str | None
    end_date: str | None
    party: str | None
    count: int | None
    citations: list[Citation] = field(default_factory=list)
    status: str | None = None
    value_ok: bool = True  # every date/amount/name/claim in value is in its own quotes

    @property
    def verified(self) -> bool:
        return self.value_ok and any(c.verified for c in self.citations)


def _always_evidence(matter_id: str) -> list[Hit]:
    """Custom fields and matter details are small and dense; give them to every category."""
    with connect() as conn:
        rows = conn.execute(
            "SELECT c.id, c.source_id, c.page_no, c.char_start, c.char_end, c.text, s.kind, s.title"
            " FROM chunks c JOIN sources s ON s.id = c.source_id"
            " WHERE s.matter_id = ? AND s.kind IN ('custom_field', 'matter')", (matter_id,)).fetchall()
    return [Hit(r["id"], r["source_id"], r["page_no"], r["char_start"], r["char_end"], r["text"],
                r["kind"], r["title"] or r["source_id"], 0.0) for r in rows]


def _gather(matter_id: str, cat: Category, base: list[Hit]) -> list[Hit]:
    seen: dict[int, Hit] = {h.chunk_id: h for h in base}
    for q in cat.queries:
        for h in search_hits(matter_id, q, top_k=cat.top_k):
            seen.setdefault(h.chunk_id, h)
    return list(seen.values())


def _source_dates(hits: list[Hit]) -> dict[str, str | None]:
    with connect() as conn:
        return {h.source_id: (conn.execute("SELECT date FROM sources WHERE id = ?", (h.source_id,)).fetchone()
                              or [None])[0] for h in hits}


def _run(matter_id: str, cat: Category, base: list[Hit]) -> list[Extracted]:
    hits = _gather(matter_id, cat, base)
    if not hits:
        return []
    dates = _source_dates(hits)
    passages = "\n\n".join(
        fence(i, f'kind="{h.kind}" title="{h.title[:120]}" date="{dates.get(h.source_id) or ""}"'
                 f'{f" page={chr(34)}{h.page_no}{chr(34)}" if h.page_no else ""}', h.text)
        for i, h in enumerate(hits))
    input_hash = hashlib.sha256((PROMPT_VERSION + cat.key + cat.instructions + passages).encode()).hexdigest()
    cache_key = f"extract:{cat.key}"
    with connect() as conn:
        row = conn.execute("SELECT input_hash, payload_json FROM digests WHERE matter_id = ? AND kind = ?",
                           (matter_id, cache_key)).fetchone()
    if row and row["input_hash"] == input_hash:
        out = Extraction.model_validate_json(row["payload_json"])
    else:
        content = (f"Task: {cat.instructions}\n\nPassages:\n\n{passages}\n\n"
                   f"Reminder: {cat.instructions}")
        out = structured(MODEL_SONNET, Extraction, SYSTEM, content, purpose=f"extract:{cat.key}",
                         matter_id=matter_id, effort="medium")
        with connect() as conn:
            conn.execute("INSERT OR REPLACE INTO digests (matter_id, kind, input_hash, payload_json, model,"
                         " created_at) VALUES (?, ?, ?, ?, ?, datetime('now'))",
                         (matter_id, cache_key, input_hash, out.model_dump_json(), MODEL_SONNET))
    results: list[Extracted] = []
    with connect() as conn:
        for it in out.items:
            cits = []
            for ev in it.evidence:
                if not 0 <= ev.passage_id < len(hits):
                    continue
                h = hits[ev.passage_id]
                c = locate(conn, h.source_id, ev.quote, h.page_no)
                if c:
                    cits.append(c)
            cits.sort(key=lambda c: (not c.verified, not c.rects))  # highlightable scans first
            results.append(Extracted(cat.key, it.label.strip(), it.value.strip(), it.amount, it.date,
                                     it.end_date, it.party, it.count, cits, (it.status or "").lower() or None))
    return results


class ExtractionFailed(RuntimeError):
    pass


def extract_all(matter_id: str, workers: int = 4) -> dict[str, list[Extracted]]:
    """All categories; raises ExtractionFailed so a partial digest is never cached."""
    base = _always_evidence(matter_id)

    def one(cat):
        for attempt in range(2):
            try:
                return cat.key, _run(matter_id, cat, base)
            except Exception as e:
                print(f"extract {cat.key} failed (attempt {attempt + 1}): {type(e).__name__}: {e}")
        return cat.key, None

    with ThreadPoolExecutor(workers) as ex:
        out = dict(ex.map(one, CATEGORIES))
    failed = [k for k, v in out.items() if v is None]
    if failed:
        raise ExtractionFailed(f"extraction failed for: {', '.join(failed)}")
    return out


def save_facts(matter_id: str, extracted: dict[str, list[Extracted]], input_hash: str) -> None:
    """Audit trail of every extracted fact in the facts table."""
    with connect() as conn:
        conn.execute("DELETE FROM facts WHERE matter_id = ?", (matter_id,))
        for cat, items in extracted.items():
            for i, x in enumerate(items):
                c = x.citations[0] if x.citations else None
                conn.execute(
                    "INSERT INTO facts (id, matter_id, category, label, value, amount, date, source_id, page_no,"
                    " quote, char_start, char_end, rects_json, verified, model, input_hash, created_at)"
                    " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))",
                    (f"{matter_id}:{cat}-{i}", matter_id, cat, x.label, x.value, x.amount, x.date,
                     c.source_id if c else None, c.page if c else None, c.quote if c else None,
                     c.char_start if c else None, c.char_end if c else None,
                     json.dumps([r.model_dump() for r in c.rects]) if c else None,
                     int(x.verified), MODEL_SONNET, input_hash))


def verify_values(matter_id: str, extracted: dict[str, list[Extracted]]) -> dict:
    """Audit every fact's value and date against its own verified quotes.

    Tokens (dates, amounts, codes, names) are checked deterministically; claims by one Sonnet judge
    call. Unsupported parts are stripped (judge's supported_text); if nothing safe remains the fact
    keeps its text but is marked unverified. A date not in the quotes is dropped.
    """
    from app.digest.verify import Corpus, check_tokens, judge_claims

    with connect() as conn:
        titles = [r[0] or "" for r in conn.execute("SELECT title FROM sources WHERE matter_id = ?", (matter_id,))]
    names = Corpus("\n".join(titles))
    todo: list[Extracted] = []
    for items in extracted.values():
        for x in items:
            quotes = [c.quote for c in x.citations if c.verified]
            if not quotes:
                continue
            corpus = Corpus("\n".join(quotes))
            if x.date and x.date not in corpus.dates:
                if x.category in ("key_dates", "incident") and not x.end_date:
                    x.value_ok = False  # the date is the fact; keep it visible but unverified
                else:
                    x.date = None
            if x.end_date and x.end_date not in corpus.dates:
                x.end_date = None
            todo.append(x)
    if not todo:
        return {"checked": 0}
    judged = judge_claims(matter_id, [(x.value, [c.quote for c in x.citations if c.verified]) for x in todo],
                          purpose="verify_facts")
    stripped = flagged = 0
    for x, j in zip(todo, judged):
        quotes = Corpus("\n".join(f"{c.source_title}\n{c.quote}" for c in x.citations if c.verified))
        bad = check_tokens(x.value, quotes, names) + list(j.unsupported)
        if not bad:
            continue
        safe = j.supported_text.strip()
        if safe and not check_tokens(safe, quotes, names):
            x.value = safe
            stripped += 1
        else:
            x.value_ok = False
            flagged += 1
    return {"checked": len(todo), "stripped": stripped, "flagged": flagged}
