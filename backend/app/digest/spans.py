"""Quote → verbatim span → highlight rects (catalog A7, adapted from aurolegal).

A citation is `verified` only when its quote is found in the source text:
exact after normalization (case, whitespace, curly quotes, dashes), else a
rapidfuzz partial alignment ≥ 90. The stored quote is always the source's own
characters, never the model's copy.
"""

import json
import sqlite3
import unicodedata

from rapidfuzz import fuzz

from app.schemas import Citation, Rect

_CHAR_MAP = {
    "‘": "'", "’": "'", "‚": "'", "‛": "'", "′": "'",
    "“": '"', "”": '"', "„": '"', "″": '"',
    "‐": "-", "‑": "-", "‒": "-", "–": "-", "—": "-", "−": "-",
    " ": " ", "\f": " ",
}
FUZZY_MIN = 90


def fold(text: str) -> tuple[str, list[int]]:
    """Normalized text plus a map from each output char to its source index."""
    out: list[str] = []
    index_map: list[int] = []
    pending_space = False
    for i, ch in enumerate(text):
        ch = _CHAR_MAP.get(ch, ch)
        if ch.isspace():
            pending_space = bool(out)
            continue
        if pending_space:
            out.append(" ")
            index_map.append(i)
            pending_space = False
        for sub in unicodedata.normalize("NFKC", ch).casefold():
            out.append(sub)
            index_map.append(i)
    return "".join(out), index_map


def find_span(quote: str, text: str) -> tuple[int, int] | None:
    """[start, end) of `quote` inside `text`, or None."""
    if not quote or not text:
        return None
    fq, _ = fold(quote.strip().strip('"').strip("…").strip("."))
    if len(fq) < 3:
        return None
    ft, imap = fold(text)
    if not ft:
        return None
    pos = ft.find(fq)
    if pos != -1:
        return imap[pos], imap[pos + len(fq) - 1] + 1
    if len(fq) < 20:
        return None
    al = fuzz.partial_ratio_alignment(fq, ft, score_cutoff=FUZZY_MIN)
    if al is None or al.dest_end <= al.dest_start:
        return None
    s, e = imap[al.dest_start], imap[min(al.dest_end, len(imap)) - 1] + 1
    while s > 0 and text[s - 1].isalnum():  # snap a fuzzy hit out to whole words
        s -= 1
    while e < len(text) and text[e].isalnum():
        e += 1
    return s, e


def rects_for(lines_json: str | None, page_no: int, start: int, end: int) -> list[Rect]:
    """One rect per line overlapping [start, end), clipped by char proportion."""
    if not lines_json:
        return []
    try:
        lines = json.loads(lines_json)
    except ValueError:
        return []
    rects: list[Rect] = []
    for ln in lines:
        cs, ce = ln.get("char_start"), ln.get("char_end")
        if cs is None or ce is None or ce <= start or cs >= end:
            continue
        width = ln["x1"] - ln["x0"]
        n = max(ce - cs, 1)
        a = (max(start, cs) - cs) / n
        b = (min(end, ce) - cs) / n
        rects.append(Rect(page=page_no, x0=ln["x0"] + width * a, y0=ln["y0"],
                          x1=ln["x0"] + width * b, y1=ln["y1"]))
    return rects


def _meta(conn: sqlite3.Connection, source_id: str) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT id, kind, title, date, text FROM sources WHERE id = ?", (source_id,)
    ).fetchone()


def citation_for_range(conn: sqlite3.Connection, source_id: str, page_no: int | None,
                       start: int, end: int) -> Citation | None:
    """Citation for a known char range (e.g. a retrieved chunk). Always verified."""
    src = _meta(conn, source_id)
    if src is None:
        return None
    if page_no is not None:
        pg = conn.execute("SELECT text, lines_json FROM pages WHERE source_id = ? AND page_no = ?",
                          (source_id, page_no)).fetchone()
        text = pg["text"] if pg else ""
        rects = rects_for(pg["lines_json"], page_no, start, end) if pg else []
    else:
        text, rects = src["text"] or "", []
    return Citation(source_id=source_id, source_kind=src["kind"], source_title=src["title"] or source_id,
                    date=src["date"], page=page_no, quote=text[start:end], char_start=start,
                    char_end=end, rects=rects, verified=True)


def locate(conn: sqlite3.Connection, source_id: str, quote: str,
           page_hint: int | None = None) -> Citation | None:
    """Find `quote` in the source (hinted page first). Unfound → verified=False."""
    src = _meta(conn, source_id)
    if src is None:
        return None
    base = dict(source_id=source_id, source_kind=src["kind"], source_title=src["title"] or source_id,
                date=src["date"])
    pages = conn.execute("SELECT page_no, text, lines_json FROM pages WHERE source_id = ? ORDER BY page_no",
                         (source_id,)).fetchall()
    pages = sorted(pages, key=lambda p: p["page_no"] != page_hint)
    for pg in pages:
        span = find_span(quote, pg["text"] or "")
        if span:
            s, e = span
            return Citation(**base, page=pg["page_no"], quote=pg["text"][s:e], char_start=s, char_end=e,
                            rects=rects_for(pg["lines_json"], pg["page_no"], s, e), verified=True)
    text = src["text"] or ""
    span = find_span(quote, text)
    if span:
        s, e = span
        page = text[:s].count("\f") + 1 if pages else None
        return Citation(**base, page=page, quote=text[s:e],
                        char_start=None if pages else s, char_end=None if pages else e, verified=True)
    return Citation(**base, page=page_hint, quote=quote, verified=False)
