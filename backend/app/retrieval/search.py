"""Hybrid search: FTS5 BM25 + cosine over body and HyDE vectors → RRF → Cohere rerank.

Falls back to RRF order when COHERE_API_KEY is missing or the rerank call fails.
"""

import re
from dataclasses import dataclass

import numpy as np

from app.config import COHERE_API_KEY
from app.db import connect
from app.digest.spans import citation_for_range
from app.llm import PRICES, log_usage
from app.retrieval.embed import embed_query
from app.schemas import Passage

RERANK_MODEL = "rerank-v3.5"
PRICES.setdefault(RERANK_MODEL, (2000.0, 0.0))  # $2 per 1k searches; logged as 1 "token" per search
RRF_K = 60

_STOP = set("a an and are as at be by for from has have how i in is it of on or that the this to was "
            "were what when where which who why will with does did do any all about".split())


@dataclass
class Hit:
    chunk_id: int
    source_id: str
    page_no: int | None
    char_start: int | None
    char_end: int | None
    text: str
    kind: str
    title: str
    score: float


_vec_cache: dict[str, tuple[int, np.ndarray, np.ndarray]] = {}


def _vectors(conn, matter_id: str) -> tuple[np.ndarray, np.ndarray]:
    """(chunk_ids, matrix) for every body + hyde vector of the matter, cached by row count."""
    n = conn.execute("SELECT COUNT(*), COALESCE(MAX(v.id), 0) FROM vectors v JOIN chunks c ON c.id = v.chunk_id"
                     " JOIN sources s ON s.id = c.source_id WHERE s.matter_id = ?", (matter_id,)).fetchone()
    stamp = n[0] * 1_000_003 + n[1]
    hit = _vec_cache.get(matter_id)
    if hit and hit[0] == stamp:
        return hit[1], hit[2]
    rows = conn.execute("SELECT v.chunk_id, v.embedding FROM vectors v JOIN chunks c ON c.id = v.chunk_id"
                        " JOIN sources s ON s.id = c.source_id WHERE s.matter_id = ?", (matter_id,)).fetchall()
    ids = np.asarray([r[0] for r in rows], dtype=np.int64)
    mat = np.vstack([np.frombuffer(r[1], dtype="<f4") for r in rows]) if rows else np.zeros((0, 1), np.float32)
    _vec_cache[matter_id] = (stamp, ids, mat)
    return ids, mat


def _fts_query(q: str) -> str:
    words = [w for w in re.findall(r"[A-Za-z0-9]+", q.lower()) if w not in _STOP and len(w) > 1]
    return " OR ".join(f'"{w}"' for w in words[:20])


def _bm25(conn, matter_id: str, q: str, limit: int) -> list[int]:
    fq = _fts_query(q)
    if not fq:
        return []
    try:
        rows = conn.execute(
            "SELECT c.id FROM chunks_fts f JOIN chunks c ON c.id = f.rowid JOIN sources s ON s.id = c.source_id"
            " WHERE chunks_fts MATCH ? AND s.matter_id = ? ORDER BY bm25(chunks_fts) LIMIT ?",
            (fq, matter_id, limit)).fetchall()
    except Exception as e:
        print(f"fts failed: {e}")
        return []
    return [r[0] for r in rows]


def _dense(conn, matter_id: str, q: str, limit: int) -> list[int]:
    ids, mat = _vectors(conn, matter_id)
    if not len(ids):
        return []
    sims = mat @ embed_query(q, matter_id)
    best: dict[int, float] = {}
    for cid, s in zip(ids.tolist(), sims.tolist()):  # max over a chunk's body + hyde vectors
        if s > best.get(cid, -2):
            best[cid] = s
    return sorted(best, key=best.get, reverse=True)[:limit]


def _rerank(q: str, hits: list[Hit], top_k: int, matter_id: str) -> list[Hit] | None:
    if not COHERE_API_KEY or not hits:
        return None
    try:
        import cohere
        co = cohere.ClientV2(api_key=COHERE_API_KEY)
        resp = co.rerank(model=RERANK_MODEL, query=q, documents=[f"{h.title}\n{h.text}"[:4000] for h in hits],
                         top_n=min(top_k, len(hits)))
        log_usage(RERANK_MODEL, "rerank", 1, 0, matter_id)
    except Exception as e:
        print(f"rerank failed, using RRF order: {e}")
        return None
    out = []
    for r in resp.results:
        h = hits[r.index]
        h.score = float(r.relevance_score)
        out.append(h)
    return out


def search_hits(matter_id: str, q: str, top_k: int = 8, pool: int = 40,
                kinds: set[str] | None = None) -> list[Hit]:
    with connect() as conn:
        lists = [_bm25(conn, matter_id, q, pool), _dense(conn, matter_id, q, pool)]
        scores: dict[int, float] = {}
        for lst in lists:
            for rank, cid in enumerate(lst):
                scores[cid] = scores.get(cid, 0.0) + 1.0 / (RRF_K + rank + 1)
        order = sorted(scores, key=scores.get, reverse=True)
        hits: list[Hit] = []
        for cid in order:
            r = conn.execute(
                "SELECT c.id, c.source_id, c.page_no, c.char_start, c.char_end, c.text, s.kind, s.title"
                " FROM chunks c JOIN sources s ON s.id = c.source_id WHERE c.id = ?", (cid,)).fetchone()
            if r is None or (kinds and r["kind"] not in kinds):
                continue
            hits.append(Hit(r["id"], r["source_id"], r["page_no"], r["char_start"], r["char_end"], r["text"],
                            r["kind"], r["title"] or r["source_id"], scores[cid]))
            if len(hits) >= pool:
                break
    return _rerank(q, hits, top_k, matter_id) or hits[:top_k]


def _snippet(text: str, q: str, width: int = 280) -> str:
    words = [w for w in re.findall(r"[A-Za-z0-9]+", q.lower()) if w not in _STOP and len(w) > 2]
    low = text.lower()
    pos = min([p for p in (low.find(w) for w in words) if p >= 0], default=0)
    start = max(0, pos - width // 3)
    s = text[start:start + width].strip()
    return ("…" if start else "") + s + ("…" if start + width < len(text) else "")


def to_passage(hit: Hit, q: str) -> Passage | None:
    with connect() as conn:
        if hit.char_start is not None and hit.char_end is not None:
            cit = citation_for_range(conn, hit.source_id, hit.page_no, hit.char_start, hit.char_end)
        else:
            cit = None
        if cit is None:
            from app.digest.spans import locate
            cit = locate(conn, hit.source_id, hit.text[:400], hit.page_no)
    if cit is None:
        return None
    return Passage(citation=cit, score=hit.score, snippet=_snippet(hit.text, q))


def search(matter_id: str, q: str, top_k: int = 8) -> list[Passage]:
    return [p for h in search_hits(matter_id, q, top_k) if (p := to_passage(h, q))]
