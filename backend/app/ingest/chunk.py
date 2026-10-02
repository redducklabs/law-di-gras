"""Chunk text into ~800-token windows with char offsets; keep chunks_fts in sync."""

import hashlib
import sqlite3

CHUNK_CHARS = 3200  # ~800 tokens
OVERLAP_CHARS = 400


def spans(text: str) -> list[tuple[int, int]]:
    """Char ranges covering text, cut at newline/space boundaries, with overlap."""
    n = len(text)
    if not text.strip():
        return []
    out, start = [], 0
    while start < n:
        end = min(start + CHUNK_CHARS, n)
        if end < n:
            cut = text.rfind("\n", start + CHUNK_CHARS // 2, end)
            if cut == -1:
                cut = text.rfind(" ", start + CHUNK_CHARS // 2, end)
            if cut != -1:
                end = cut
        out.append((start, end))
        if end >= n:
            break
        nxt = max(end - OVERLAP_CHARS, start + 1)
        sp = text.find(" ", nxt, end)
        start = sp + 1 if sp != -1 else nxt
    return out


def delete_chunks(conn: sqlite3.Connection, source_id: str) -> None:
    ids = [r[0] for r in conn.execute("SELECT id FROM chunks WHERE source_id=?", (source_id,))]
    if not ids:
        return
    q = ",".join("?" * len(ids))
    conn.execute(f"DELETE FROM vectors WHERE chunk_id IN ({q})", ids)  # stale embeddings
    conn.execute("DELETE FROM chunks WHERE source_id=?", (source_id,))


def chunk_source(conn: sqlite3.Connection, source_id: str, text: str, page_no: int | None = None) -> int:
    """Insert chunks for one text (a PDF page or a whole non-PDF source)."""
    count = 0
    for a, b in spans(text):
        body = text[a:b]
        conn.execute(
            "INSERT INTO chunks(source_id, page_no, char_start, char_end, text, content_hash) VALUES (?,?,?,?,?,?)",
            (source_id, page_no, a, b, body, hashlib.sha256(body.encode()).hexdigest()),
        )
        count += 1
    return count


def rebuild_fts(conn: sqlite3.Connection) -> None:
    conn.execute("INSERT INTO chunks_fts(chunks_fts) VALUES('rebuild')")
