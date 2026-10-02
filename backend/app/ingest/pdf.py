"""PDF -> per-page text with line boxes (normalized 0..1, top-left origin).

Text pages use PyMuPDF line geometry. Pages with almost no text (scans) are
rasterized and run through RapidOCR. pages.text is built by joining lines with
"\n", so each line's char_start/char_end index straight into it.
"""

import logging
from dataclasses import dataclass, field

import fitz  # PyMuPDF
import numpy as np

log = logging.getLogger("ingest.pdf")

MIN_TEXT_CHARS = 50
OCR_ZOOM = 2.5  # ~180 dpi

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
    # Group lines that share a baseline band, then left-to-right.
    raw.sort(key=lambda r: (round(r[2] * 200), r[1]))
    parts, lines, pos = [], [], 0
    for text, x0, y0, x1, y1 in raw:
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


def _ocr_lines(page: fitz.Page) -> list[tuple]:
    pix = page.get_pixmap(matrix=fitz.Matrix(OCR_ZOOM, OCR_ZOOM), colorspace=fitz.csRGB, alpha=False)
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
