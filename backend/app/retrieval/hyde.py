"""HyDE: Haiku writes questions each chunk answers; they are embedded as kind=hyde.

Prompt shape adapted from aurolegal's hyde_service (HYDE_QUESTION_PROMPT),
retargeted at PI firm staff and treating providers. Questions are cached per
chunk content_hash in `digests` (kind='hyde:<hash>'), so re-syncs are free.
"""

import hashlib
import json
import sqlite3
import time
from concurrent.futures import ThreadPoolExecutor

from pydantic import BaseModel

from app.db import connect
from app.llm import MODEL_HAIKU, structured
from app.retrieval.embed import matter_chunks, store_vectors
from app.retrieval.fence import FENCE_RULE, fence

SYSTEM = (
    "You generate search questions for a retrieval system over a personal-injury case file. "
    + FENCE_RULE
)

PROMPT = """Write exactly 5 questions that an attorney, paralegal, case manager, or the
client's treating medical provider might ask that the passage below answers.
The questions should:
- Use the vocabulary these professionals use (treatment, bills, liens, policy limits,
  demand, deadlines, records requests, injuries, liability).
- Be specific enough to match this passage, naming the people, providers, dates or
  amounts it contains.
- Cover different aspects of what the passage says.

{passage}"""


class HydeQuestions(BaseModel):
    questions: list[str]


def _hash(chunk) -> str:
    return chunk["content_hash"] or hashlib.sha256((chunk["text"] or "").encode()).hexdigest()


def _questions(chunk, matter_id: str) -> list[str]:
    key = f"hyde:{_hash(chunk)}"
    with connect() as conn:
        row = conn.execute("SELECT payload_json FROM digests WHERE kind = ? LIMIT 1", (key,)).fetchone()
    if row:
        return json.loads(row["payload_json"])
    header = f'kind="{chunk["kind"]}" title="{(chunk["title"] or "")[:120]}"'
    out = structured(MODEL_HAIKU, HydeQuestions, SYSTEM,
                     PROMPT.format(passage=fence(chunk["id"], header, chunk["text"], cap=8000)),
                     purpose="hyde", matter_id=matter_id, max_tokens=1000)
    qs = [q.strip() for q in out.questions if q.strip()][:6]
    for attempt in range(5):  # other streams may hold the write lock during a sync
        try:
            with connect() as conn:
                conn.execute("INSERT OR REPLACE INTO digests (matter_id, kind, input_hash, payload_json, model, created_at)"
                             " VALUES (?, ?, ?, ?, ?, datetime('now'))",
                             (matter_id, key, _hash(chunk), json.dumps(qs), MODEL_HAIKU))
            break
        except sqlite3.OperationalError:
            time.sleep(2 * (attempt + 1))
    return qs


def hyde_matter(matter_id: str, workers: int = 8) -> dict:
    with connect() as conn:
        have = {r[0] for r in conn.execute("SELECT DISTINCT chunk_id FROM vectors WHERE kind = 'hyde'")}
        chunks = [c for c in matter_chunks(conn, matter_id)
                  if c["id"] not in have and len((c["text"] or "").strip()) > 40]

    def one(c):
        try:
            return c["id"], _questions(c, matter_id)
        except Exception as e:  # one bad chunk must not sink the digest
            print(f"hyde failed for chunk {c['id']}: {e}")
            return c["id"], []

    with ThreadPoolExecutor(workers) as ex:
        results = list(ex.map(one, chunks))
    rows = [(cid, "hyde", q) for cid, qs in results for q in qs]
    store_vectors(rows, matter_id)
    return {"chunks": len(chunks), "questions": len(rows)}
