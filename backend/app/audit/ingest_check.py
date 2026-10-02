"""Check 4: ingestion vs Clio (GET only) and PDF/OCR quality."""

import base64
import json
import re
from difflib import SequenceMatcher

from pydantic import BaseModel

from app import config, llm
from app.audit.checks import Finding
from app.audit.items import dates_in
from app.db import connect

ENTITY = re.compile(r"&(amp|quot|apos|lt|gt|nbsp|#\d+|#x[0-9a-f]+);", re.I)


def clio_compare(matter_id: str) -> tuple[list[Finding], list[dict]]:
    from app.clio.client import client
    from app.clio.sync import ENDPOINTS, render

    out: list[Finding] = []
    table: list[dict] = []
    c = client()
    with connect() as conn:
        db = {r["id"]: dict(r) for r in conn.execute(
            "SELECT id, kind, title, date, text FROM sources WHERE matter_id=?", (matter_id,))}
    for kind, (ep, fields, extra) in ENDPOINTS.items():
        recs = list(c.paginate(ep, {"matter_id": matter_id, "fields": fields, **extra}))
        mine = {k for k, v in db.items() if v["kind"] == kind}
        theirs = {f"{kind}:{r['id']}" for r in recs}
        table.append({"kind": kind, "clio": len(recs), "db": len(mine),
                      "missing_in_db": len(theirs - mine), "extra_in_db": len(mine - theirs)})
        for sid in sorted(theirs - mine):
            out.append(Finding("4-ingest", "major", sid, "", "", f"In Clio but not ingested ({kind}).", "S4"))
        for sid in sorted(mine - theirs):
            out.append(Finding("4-ingest", "major", sid, db[sid]["title"] or "", "",
                               f"In our DB but no longer in Clio ({kind}); stale source still citable.", "S4"))
        if kind == "document":
            continue
        for r in recs:
            sid = f"{kind}:{r['id']}"
            if sid not in db:
                continue
            title, date, _, text = render(kind, r)
            if (db[sid]["text"] or "") != text:
                ratio = SequenceMatcher(None, db[sid]["text"] or "", text).ratio()
                out.append(Finding("4-ingest", "major" if ratio < 0.98 else "minor", sid, db[sid]["title"] or "", "",
                                   f"Stored text differs from Clio's current text (similarity {ratio:.3f}); re-sync needed.", "S4"))
            if (db[sid]["date"] or "") != (date or ""):
                out.append(Finding("4-ingest", "major", sid, db[sid]["title"] or "", "",
                                   f"Stored date {db[sid]['date']} vs Clio {date}.", "S4"))
    return out, table


def local_checks(matter_id: str) -> tuple[list[Finding], list[dict]]:
    out: list[Finding] = []
    doc_rows: list[dict] = []
    with connect() as conn:
        srcs = conn.execute("SELECT id, kind, title, date, text, content_hash, page_count, raw_json FROM sources "
                            "WHERE matter_id=?", (matter_id,)).fetchall()
        pages = conn.execute("SELECT p.source_id, p.page_no, p.text, p.ocr FROM pages p JOIN sources s ON s.id=p.source_id "
                             "WHERE s.matter_id=?", (matter_id,)).fetchall()
    for s in srcs:
        for fld in ("title", "text"):
            m = ENTITY.search(s[fld] or "")
            if m:
                out.append(Finding("4-ingest", "minor", s["id"], s["title"] or "", m.group(0),
                                   f"HTML entity left in {fld}.", "S4"))
    for p in pages:
        if len((p["text"] or "").strip()) < 20:
            out.append(Finding("4-ingest", "major", f"{p['source_id']} p{p['page_no']}", "", "",
                               f"Page has no usable text ({len((p['text'] or '').strip())} chars, ocr={p['ocr']}); "
                               "uncitable and unsearchable.", "S4"))
    # duplicates
    by_hash: dict[str, list] = {}
    by_text: dict[str, list] = {}
    for s in srcs:
        if s["kind"] == "document":
            by_text.setdefault(re.sub(r"\s+", " ", (s["text"] or "")[:3000]).strip(), []).append(s)
    for k, group in by_text.items():
        if len(group) > 1 and k:
            out.append(Finding("4-ingest", "minor", ", ".join(g["id"] for g in group), " | ".join(g["title"] for g in group), "",
                               "Duplicate document text.", "S4"))
    # document dates: Clio date (shown in the source header) vs the document's own date
    for s in srcs:
        if s["kind"] != "document":
            continue
        clio = (s["date"] or "")[:10]
        fname = re.search(r"(\d{4}-\d{2}-\d{2})", s["title"] or "")
        first_page = (s["text"] or "").split("\f")[0][:2500]
        own = sorted(dates_in(first_page), key=lambda d: (d[0], d[1], d[2] or 0))
        rj = json.loads(s["raw_json"] or "{}")
        row = {"id": s["id"], "title": s["title"], "clio_date": clio, "created_at": (rj.get("created_at") or "")[:10],
               "received_at": (rj.get("received_at") or "")[:10], "filename_date": fname.group(1) if fname else "",
               "page1_dates": ", ".join(f"{y}-{m:02d}" + (f"-{d:02d}" if d else "") for y, m, d in own[-4:])}
        doc_rows.append(row)
        full = [d for d in own if d[2]]
        latest = max(full) if full else None
        if latest and clio and f"{latest[0]}-{latest[1]:02d}-{latest[2]:02d}" > clio:
            out.append(Finding("4-ingest", "major", s["id"], f"{s['title']} — header date {clio}", row["page1_dates"],
                               f"Clio date {clio} (shown as the document date) is earlier than dates written on page 1 "
                               f"(latest {latest[0]}-{latest[1]:02d}-{latest[2]:02d}); the header date is a Clio "
                               "filing/received date, not the document's own date.", "S4"))
    return out, doc_rows


class Transcript(BaseModel):
    text: str


def ocr_quality(matter_id: str, limit: int = 10) -> tuple[list[Finding], list[dict]]:
    """Compare stored OCR text of each scanned page with a Claude vision transcription (word error rate)."""
    import fitz

    out: list[Finding] = []
    rows: list[dict] = []
    with connect() as conn:
        pages = conn.execute(
            "SELECT p.source_id, p.page_no, p.text, s.title, s.file_path FROM pages p JOIN sources s ON s.id=p.source_id "
            "WHERE s.matter_id=? AND p.ocr=1 ORDER BY p.source_id, p.page_no LIMIT ?", (matter_id, limit)).fetchall()
    for p in pages:
        doc = fitz.open(str(config.FILES_DIR / p["file_path"]))
        png = doc[p["page_no"] - 1].get_pixmap(dpi=130).tobytes("png")
        tr = llm.structured(llm.MODEL_SONNET, Transcript,
                            "Transcribe all text on this scanned page exactly, in reading order. No commentary.",
                            [{"type": "image", "source": {"type": "base64", "media_type": "image/png",
                                                          "data": base64.b64encode(png).decode()}},
                             {"type": "text", "text": "Transcribe this page."}],
                            purpose="audit:ocr_transcribe", matter_id=matter_id, effort="low", max_tokens=6000)
        ref = re.findall(r"\w+", tr.text.lower())
        hyp = re.findall(r"\w+", (p["text"] or "").lower())
        sm = SequenceMatcher(None, ref, hyp, autojunk=False)
        matched = sum(b.size for b in sm.get_matching_blocks())
        wer = 1 - matched / max(1, len(ref))
        nums_ref = set(re.findall(r"\d[\d,./-]*\d|\d", tr.text))
        nums_hyp = set(re.findall(r"\d[\d,./-]*\d|\d", p["text"] or ""))
        lost = sorted(nums_ref - nums_hyp)[:8]
        rows.append({"page": f"{p['title']} p{p['page_no']}", "ref_words": len(ref), "ocr_words": len(hyp),
                     "word_error": round(wer, 3), "numbers_missing_in_ocr": ", ".join(lost)})
        if wer > 0.15 or lost:
            out.append(Finding("4-ocr", "major" if (wer > 0.3 or len(lost) > 2) else "minor",
                               f"{p['source_id']} p{p['page_no']}", p["title"], "",
                               f"OCR word error ≈{wer:.0%} vs vision transcription; numbers missing/garbled: {', '.join(lost) or 'none'}.",
                               "S4"))
    return out, rows
