"""Matters, sync and source routes (S1). Reads our DB; /sync reads Clio (GET only)."""

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app import config
from app.clio.sync import sync_matter
from app.db import connect
from app.schemas import MatterSummary, SourceDetail, SourcePage

router = APIRouter()


@router.get("/api/matters", response_model=list[MatterSummary])
def list_matters() -> list[MatterSummary]:
    with connect() as conn:
        rows = conn.execute("SELECT * FROM matters ORDER BY opened_date DESC").fetchall()
    return [
        MatterSummary(
            id=r["id"], display_number=r["display_number"] or "", title=r["description"] or r["display_number"] or "",
            client_name=r["client_name"] or "", client_photo_url=r["client_photo_url"], status=r["status"] or "",
            opened_date=r["opened_date"],
        )
        for r in rows
    ]


@router.post("/api/matters/{matter_id}/sync")
def sync(matter_id: str) -> dict:
    """Pull the matter from Clio into our DB. Pass a Clio matter id, or any
    non-numeric id (e.g. "default") to resolve MATTER_QUERY."""
    try:
        return sync_matter(matter_id)
    except LookupError as e:
        raise HTTPException(404, str(e))


@router.get("/api/sources/{source_id}", response_model=SourceDetail)
def get_source(source_id: str) -> SourceDetail:
    with connect() as conn:
        s = conn.execute("SELECT * FROM sources WHERE id=?", (source_id,)).fetchone()
        if not s:
            raise HTTPException(404, "source not found")
        pages = conn.execute(
            "SELECT page_no, width, height, ocr FROM pages WHERE source_id=? ORDER BY page_no", (source_id,)
        ).fetchall()
    return SourceDetail(
        id=s["id"], kind=s["kind"], title=s["title"] or "", date=s["date"], author=s["author"], text=s["text"] or "",
        page_count=s["page_count"], has_file=bool(s["file_path"]),
        pages=[SourcePage(page_no=p["page_no"], width=p["width"], height=p["height"], ocr=bool(p["ocr"])) for p in pages],
    )


@router.get("/api/sources/{source_id}/file")
def get_source_file(source_id: str):
    with connect() as conn:
        s = conn.execute("SELECT file_path, title FROM sources WHERE id=?", (source_id,)).fetchone()
    if not s or not s["file_path"]:
        raise HTTPException(404, "no file for this source")
    path = (config.FILES_DIR / s["file_path"]).resolve()
    if config.FILES_DIR.resolve() not in path.parents or not path.exists():
        raise HTTPException(404, "file missing; re-run sync")
    return FileResponse(path, media_type="application/pdf",
                        headers={"Content-Disposition": f'inline; filename="{source_id.replace(":", "-")}.pdf"'})
