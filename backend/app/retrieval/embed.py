"""OpenAI embeddings for chunks (kind=body) and HyDE questions (kind=hyde).

Unchanged text is never re-embedded: an existing vector with identical text and
kind is reused, so a re-sync that rebuilds chunks costs nothing here.
"""

from functools import lru_cache

import numpy as np
from openai import OpenAI

from app.config import OPENAI_API_KEY
from app.db import connect
from app.llm import log_usage

EMBED_MODEL = "text-embedding-3-large"
BATCH = 96

_client: OpenAI | None = None


def _openai() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=OPENAI_API_KEY)
    return _client


def embed_texts(texts: list[str], matter_id: str | None = None, purpose: str = "embed") -> np.ndarray:
    """Unit-normalized float32 matrix, one row per text."""
    out: list[list[float]] = []
    tokens = 0
    for i in range(0, len(texts), BATCH):
        batch = [t[:24000] or " " for t in texts[i:i + BATCH]]
        resp = _openai().embeddings.create(model=EMBED_MODEL, input=batch)
        out.extend(d.embedding for d in resp.data)
        tokens += resp.usage.total_tokens
    if tokens:
        log_usage(EMBED_MODEL, purpose, tokens, 0, matter_id)
    arr = np.asarray(out, dtype=np.float32)
    if arr.size:
        arr /= np.linalg.norm(arr, axis=1, keepdims=True) + 1e-9
    return arr


@lru_cache(maxsize=512)
def embed_query(q: str, matter_id: str | None = None) -> np.ndarray:
    return embed_texts([q], matter_id, purpose="embed_query")[0]


def store_vectors(rows: list[tuple[int, str, str]], matter_id: str) -> int:
    """rows = [(chunk_id, kind, text)]. Reuses identical (kind, text) embeddings."""
    if not rows:
        return 0
    with connect() as conn:
        cached = {}
        for cid, kind, text in rows:
            r = conn.execute("SELECT embedding FROM vectors WHERE kind = ? AND text = ? LIMIT 1",
                             (kind, text)).fetchone()
            if r:
                cached[(kind, text)] = r["embedding"]
    todo = list({(k, t) for _, k, t in rows if (k, t) not in cached})
    if todo:
        mat = embed_texts([t for _, t in todo], matter_id)
        for (k, t), vec in zip(todo, mat):
            cached[(k, t)] = vec.astype("<f4").tobytes()
    with connect() as conn:
        conn.executemany("INSERT INTO vectors (chunk_id, kind, text, embedding) VALUES (?, ?, ?, ?)",
                         [(cid, k, t, cached[(k, t)]) for cid, k, t in rows])
    return len(todo)


def matter_chunks(conn, matter_id: str):
    return conn.execute(
        "SELECT c.id, c.source_id, c.page_no, c.text, c.content_hash, s.kind, s.title"
        " FROM chunks c JOIN sources s ON s.id = c.source_id WHERE s.matter_id = ?",
        (matter_id,),
    ).fetchall()


def embed_matter(matter_id: str) -> dict:
    """Embed every chunk of the matter that has no body vector yet."""
    with connect() as conn:
        conn.execute("DELETE FROM vectors WHERE chunk_id NOT IN (SELECT id FROM chunks)")
        have = {r[0] for r in conn.execute("SELECT DISTINCT chunk_id FROM vectors WHERE kind = 'body'")}
        chunks = [c for c in matter_chunks(conn, matter_id) if c["id"] not in have]
    rows = [(c["id"], "body", c["text"]) for c in chunks if (c["text"] or "").strip()]
    new = store_vectors(rows, matter_id)
    return {"chunks": len(rows), "embedded": new}
