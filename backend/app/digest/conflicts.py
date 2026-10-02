"""Whole-record check for on-screen statements (adapted from S6's audit check 2b,
backend/app/audit/record_check.py).

For each statement, retrieve passages from the WHOLE case file (not just what it
cites), and have Sonnet decide: supported, partly, contradicted, qualified (a
passage adds a material caveat), or not_found. Every returned quote must be a
verbatim span (spans.locate) or the finding is dropped. Callers turn
`contradicted` into a visible "Conflict" with both citations, `qualified` into a
caveat, and `supported` into a re-cite instead of a drop.
"""

import hashlib
from typing import Literal

from pydantic import BaseModel

from app.db import connect
from app.digest.spans import locate
from app.llm import MODEL_SONNET, structured
from app.retrieval.fence import FENCE_RULE
from app.retrieval.search import search_hits
from app.schemas import Citation

VERSION = "k4"


class Verdict(BaseModel):
    n: int
    verdict: Literal["supported", "partly", "contradicted", "qualified", "not_found"]
    source_id: str      # best passage source_id, or ""
    quote: str          # verbatim span from that passage, or ""
    note: str           # <= 14 words: what the passage says (for a conflict/caveat, its own facts + who/when)


class Verdicts(BaseModel):
    verdicts: list[Verdict]


SYSTEM = (
    "You check statements from a personal-injury case dashboard against passages retrieved from the whole "
    "case file. For each numbered statement decide: supported (a passage states it), partly (some of it), "
    "contradicted (a passage says otherwise, e.g. a different amount, a document that exists, a party that "
    "differs), qualified (supported, but a passage adds a material caveat such as 'unreconciled', 'adds "
    "nothing', 'disputed', 'exhausted'), not_found. contradicted means a passage states something that "
    "CANNOT be true at the same time as the statement (a different amount or limit for the same thing, a "
    "document the statement says does not exist, an event the statement says did not happen). Extra detail, "
    "a fuller list, or the same fact in other words is NOT a contradiction. When a real contradiction exists "
    "anywhere, report it even if other passages support the statement. Give the source_id of "
    "the deciding passage and a short VERBATIM quote copied exactly from it. Tense matters (scheduled or "
    "recommended is not done). note: max 12 words, ONLY what that passage itself states, keeping its "
    "amounts and figures exactly, then its party and date in parentheses, e.g. '$100,000 per person / "
    "$300,000 per occurrence (Claims Service Bureau, 2026-09-08)'. No commentary, no 'conflicting with'. If the passage is an internal firm note, write "
    "'per firm note of <date>: <what it says>'. "
    + FENCE_RULE
)


def check_statements(matter_id: str, statements: list[tuple[str, list[Citation]]], k: int = 5,
                     purpose: str = "record_check") -> list[tuple[Verdict, Citation | None]]:
    """One (verdict, verified citation of the deciding passage) per statement."""
    if not statements:
        return []
    passages: list[list[tuple[str, int | None, str, str]]] = []  # per statement: (source_id, page, title, text)
    for text, cits in statements:
        ps = []
        seen = set()
        for c in cits[:3]:
            if c.verified and (c.source_id, c.page) not in seen:
                seen.add((c.source_id, c.page))
                ps.append((c.source_id, c.page, c.source_title, c.quote[:800]))
        for h in search_hits(matter_id, text, top_k=k):
            if (h.source_id, h.page_no) not in seen:
                seen.add((h.source_id, h.page_no))
                ps.append((h.source_id, h.page_no, h.title, h.text[:1500]))
        passages.append(ps)

    results: list[tuple[Verdict, Citation | None]] = []
    batch = 8
    for start in range(0, len(statements), batch):
        group = list(range(start, min(start + batch, len(statements))))
        blocks = []
        for n, i in enumerate(group):
            ps = "\n".join(f'  <passage source_id="{sid}" title="{(t or "")[:80]}">{txt}</passage>'
                           for sid, _, t, txt in passages[i])
            blocks.append(f'<statement n="{n}">{statements[i][0]}\n{ps}\n</statement>')
        content = "\n\n".join(blocks)
        key = "check:" + hashlib.sha256((VERSION + SYSTEM + content).encode()).hexdigest()[:24]
        with connect() as conn:
            row = conn.execute("SELECT payload_json FROM digests WHERE matter_id = ? AND kind = ?",
                               (matter_id, key)).fetchone()
        if row:
            out = Verdicts.model_validate_json(row["payload_json"])
        else:
            out = structured(MODEL_SONNET, Verdicts, SYSTEM, content, purpose=purpose, matter_id=matter_id,
                             effort="medium", max_tokens=6000)
            with connect() as conn:
                conn.execute("INSERT OR REPLACE INTO digests (matter_id, kind, input_hash, payload_json, model,"
                             " created_at) VALUES (?, ?, ?, ?, ?, datetime('now'))",
                             (matter_id, key, key, out.model_dump_json(), MODEL_SONNET))
        by_n = {v.n: v for v in out.verdicts}
        with connect() as conn:
            for n, i in enumerate(group):
                v = by_n.get(n) or Verdict(n=n, verdict="not_found", source_id="", quote="", note="")
                cit = None
                if v.source_id and v.quote:
                    page = next((p for sid, p, _, _ in passages[i] if sid == v.source_id), None)
                    c = locate(conn, v.source_id, v.quote, page)
                    cit = c if c and c.verified else None
                if v.verdict in ("contradicted", "qualified", "supported") and cit is None:
                    v = v.model_copy(update={"verdict": "not_found"})  # no verbatim evidence, no finding
                results.append((v, cit))
    return results
