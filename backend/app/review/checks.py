"""Extra verifier checks for Blind spots findings (from S6's audit of the first cached set).

(a) overreach: exclusivity/superlative words ("only", "never", "nobody") must be in the quotes, and
    upcoming/scheduled events must be backed by a future calendar entry/task or a quote that says so.
(b) same_source: a claimed conflict must survive a read of the full text of the sources it cites
    (the same document may state the matching fact elsewhere).
(c) record_cites: each fact is checked against the whole record; supporting passages are attached
    as extra citations, and a contradiction rejects the finding.
"""

import re
from datetime import date

from pydantic import BaseModel

from app.db import connect
from app.digest.conflicts import check_statements
from app.digest.spans import locate
from app.llm import MODEL_SONNET, structured
from app.retrieval.fence import FENCE_RULE, fence
from app.schemas import Citation

# Words that overstate the record unless a quote uses them: exclusivity, absolutes, intent.
_EXCLUSIVE = re.compile(r"\b(only|never|sole|solely|nobody|no one|always|entirely|neither|nor any|"
                        r"planned|plans to|intends?|intended|decided)\b", re.I)
# Absolute absence and certainty about changes the record does not show.
_ABSOLUTE = re.compile(r"\b(?:without (?:any|a single)|not (?:a single|once)|no (?:analysis|attempt|effort|one has)|"
                       r"will (?:also )?have (?:grown|increased|risen|changed|expired|lapsed)|"
                       r"has (?:since )?(?:grown|increased|risen))\b", re.I)
_FUTURE = re.compile(r"\b(upcoming|forthcoming|scheduled|set for|next (?:week|month)'s|pending (?:conference|hearing|motion))\b", re.I)
_SCHEDULED_IN_QUOTE = re.compile(r"schedul|set for|adjourned to|will be held|is calendared|on calendar", re.I)


def overreach(texts: list[str], quotes: str, cits: list[Citation]) -> list[str]:
    problems = []
    low = quotes.lower()
    for t in texts:
        scrub = re.sub(r"no record found of", "", t, flags=re.I)
        for m in _EXCLUSIVE.finditer(scrub):
            if not re.search(rf"\b{re.escape(m.group(1).lower())}\b", low):
                problems.append(f'"{m.group(0)}" (exclusivity/superlative not stated in your quotes; soften or quote it)')
        for m in _ABSOLUTE.finditer(scrub):
            if m.group(0).lower() not in low:
                problems.append(f'"{m.group(0)}" (absolute or certain claim the quotes do not state; say what the record '
                                f'shows, or "No record found of ..." after a search)')
    today = date.today().isoformat()
    future_cite = any(c.source_kind in ("calendar_entry", "task") and (c.date or "")[:10] >= today for c in cits)
    if not future_cite and not _SCHEDULED_IN_QUOTE.search(quotes):
        for t in texts:
            for m in _FUTURE.finditer(t):
                problems.append(f'"{m.group(0)}" (no cited calendar entry, task or quote shows this is scheduled)')
    return list(dict.fromkeys(problems))


class SameSource(BaseModel):
    reconciled: bool      # another passage in the same source(s) shows the claimed conflict is not real
    quote: str            # that passage, verbatim, or ""
    explanation: str      # <= 25 words


SAME_SOURCE_SYSTEM = (
    "You check a claimed conflict or inconsistency in a personal-injury case file. You get the claim and "
    "the FULL text of every source it cites. Decide whether another passage in those same sources shows "
    "the claim is not real: the same document states the matching fact elsewhere, the two statements are "
    "different but compatible descriptions of the same place, date, amount or event, or the source "
    "explains the difference. reconciled=true only when a passage clearly does this; then copy that "
    "passage verbatim (10-300 characters) into quote. Otherwise reconciled=false and quote=\"\". "
    + FENCE_RULE
)


def same_source(matter_id: str, claim: str, cits: list[Citation]) -> str | None:
    """A problem string when the cited sources themselves reconcile the claimed conflict."""
    ids = list(dict.fromkeys(c.source_id for c in cits))
    with connect() as conn:
        rows = [conn.execute("SELECT id, title, text FROM sources WHERE id = ?", (i,)).fetchone() for i in ids]
    blocks = [fence(r["id"], f'title="{r["title"]}"', r["text"] or "", 40000) for r in rows if r]
    out = structured(MODEL_SONNET, SameSource, SAME_SOURCE_SYSTEM,
                     f"CLAIM:\n{claim}\n\nCITED SOURCES IN FULL:\n" + "\n\n".join(blocks),
                     purpose="review_verify", matter_id=matter_id, effort="medium", max_tokens=4000)
    if not out.reconciled or not out.quote:
        return None
    with connect() as conn:
        for i in ids:
            c = locate(conn, i, out.quote)
            if c and c.verified:
                return (f'the cited source itself reconciles this ("{c.quote[:160]}", {c.source_title}'
                        f'{f" p.{c.page}" if c.page else ""}): {out.explanation}. Drop or narrow the conflict.')
    return None  # unverifiable counter-quote: no evidence, no rejection


def record_cites(matter_id: str, facts: list[str], cits: list[Citation],
                 max_extra: int = 3) -> tuple[list[Citation], list[str]]:
    """(supporting citations to add, problems) from a whole-record check of each fact."""
    extra: list[Citation] = []
    problems: list[str] = []
    have = {(c.source_id, c.page, c.char_start) for c in cits}
    for fact, (v, c) in zip(facts, check_statements(matter_id, [(f, cits) for f in facts], purpose="review_verify")):
        if v.verdict == "contradicted" and c is not None:
            problems.append(f'"{fact[:80]}" is contradicted elsewhere in the record: {v.note} '
                            f'("{c.quote[:120]}", {c.source_title}). Drop or reconcile it.')
        elif v.verdict in ("supported", "qualified") and c is not None and \
                (c.source_id, c.page, c.char_start) not in have and len(extra) < max_extra:
            have.add((c.source_id, c.page, c.char_start))
            extra.append(c)
    return extra, problems
