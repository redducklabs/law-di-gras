"""PDF -> per-page text with line boxes (normalized 0..1, top-left origin).

Text pages use PyMuPDF line geometry. Pages with almost no text (scans) are
rasterized and OCR'd: Windows' built-in OCR engine first (winocr; ~0.3 s/page,
correct word spacing), RapidOCR as the cross-platform fallback (~12 s/page,
tends to drop spaces). pages.text is built by joining lines with
"\n", so each line's char_start/char_end index straight into it.
"""

import logging
from dataclasses import dataclass, field

import fitz  # PyMuPDF
import numpy as np

log = logging.getLogger("ingest.pdf")

MIN_TEXT_CHARS = 50
PARSER_VERSION = 2  # bump to force re-extraction of every document on next sync
OCR_ZOOM = 2.5  # RapidOCR fallback, ~180 dpi
WIN_OCR_ZOOM = 2.0  # ~144 dpi, close to typical scan resolution; reads best

_ocr = None


def _ocr_engine():
    global _ocr
    if _ocr is None:
        from rapidocr_onnxruntime import RapidOCR
        _ocr = RapidOCR()
    return _ocr


@dataclass
class Page:
    page_no: int
    width: float
    height: float
    text: str = ""
    ocr: bool = False
    lines: list[dict] = field(default_factory=list)


def _assemble(raw: list[tuple[str, float, float, float, float]]) -> tuple[str, list[dict]]:
    """raw = [(text, x0, y0, x1, y1)] normalized. Sort to reading order and join."""
    raw = [r for r in raw if r[0].strip()]
    # Rows: lines whose vertical centers fall inside the row's first line, then left-to-right.
    raw.sort(key=lambda r: (r[2] + r[4]) / 2)
    rows: list[list[tuple]] = []
    for r in raw:
        cy = (r[2] + r[4]) / 2
        if rows and rows[-1][0][2] <= cy <= rows[-1][0][4]:
            rows[-1].append(r)
        else:
            rows.append([r])
    ordered = [r for row in rows for r in sorted(row, key=lambda r: r[1])]
    parts, lines, pos = [], [], 0
    for text, x0, y0, x1, y1 in ordered:
        text = " ".join(text.split())
        lines.append({"text": text, "char_start": pos, "char_end": pos + len(text),
                      "x0": round(x0, 5), "y0": round(y0, 5), "x1": round(x1, 5), "y1": round(y1, 5)})
        parts.append(text)
        pos += len(text) + 1
    return "\n".join(parts), lines


def _text_lines(page: fitz.Page) -> list[tuple]:
    W, H = page.rect.width, page.rect.height
    out = []
    for block in page.get_text("dict").get("blocks", []):
        for line in block.get("lines", []):
            text = "".join(s.get("text", "") for s in line.get("spans", []))
            x0, y0, x1, y1 = line["bbox"]
            out.append((text, x0 / W, y0 / H, x1 / W, y1 / H))
    return out


def _render(page: fitz.Page, zoom: float) -> fitz.Pixmap:
    return page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), colorspace=fitz.csRGB, alpha=False)


def _win_ocr_lines(page: fitz.Page) -> list[tuple]:
    """Windows built-in OCR (fast, keeps word spacing). Line box = union of word boxes."""
    import winocr
    from PIL import Image

    pix = _render(page, WIN_OCR_ZOOM)
    img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    out = []
    for line in winocr.recognize_pil_sync(img, "en-US").get("lines", []):
        rects = [w["bounding_rect"] for w in line.get("words", [])]
        if not rects:
            continue
        x0 = min(r["x"] for r in rects)
        y0 = min(r["y"] for r in rects)
        x1 = max(r["x"] + r["width"] for r in rects)
        y1 = max(r["y"] + r["height"] for r in rects)
        out.append((line["text"], x0 / pix.width, y0 / pix.height, x1 / pix.width, y1 / pix.height))
    return out


def _ocr_lines(page: fitz.Page) -> list[tuple]:
    try:
        return _win_ocr_lines(page)
    except Exception:
        log.warning("Windows OCR unavailable; falling back to RapidOCR", exc_info=True)
    pix = _render(page, OCR_ZOOM)
    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, 3)
    result, _ = _ocr_engine()(img)
    out = []
    for box, text, _score in result or []:
        xs = [p[0] for p in box]
        ys = [p[1] for p in box]
        out.append((text, min(xs) / pix.width, min(ys) / pix.height, max(xs) / pix.width, max(ys) / pix.height))
    return out


def extract(path: str) -> list[Page]:
    pages = []
    with fitz.open(path) as doc:
        for i, page in enumerate(doc):
            p = Page(page_no=i + 1, width=page.rect.width, height=page.rect.height)
            raw = _text_lines(page)
            if sum(len(r[0].strip()) for r in raw) < MIN_TEXT_CHARS:
                try:
                    raw = _ocr_lines(page) or raw
                    p.ocr = True
                except Exception:
                    log.exception("OCR failed on %s p.%d", path, p.page_no)
            p.text, p.lines = _assemble(raw)
            pages.append(p)
    return pages


def to_pdf(data: bytes, filetype: str) -> bytes:
    """Convert an image (or other PyMuPDF-openable file) to PDF bytes."""
    with fitz.open(stream=data, filetype=filetype) as doc:
        return doc.convert_to_pdf()
