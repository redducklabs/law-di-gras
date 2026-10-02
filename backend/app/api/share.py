"""Provider sharing routes (S4). Our DB only; nothing here talks to Clio.

Contract routes: providers list, share settings GET/PUT, provider view by token.
Extra routes used by the share panel / provider page: document picker, unsaved
preview, and token-scoped access to shared documents only.
"""

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse

from app.config import FILES_DIR
from app.db import connect
from app.schemas import Provider, ProviderView, ShareSettings, SourceDetail, SourcePage
from app.share.providers import list_providers, load_dashboard, provider_by_id
from app.share.view import (
    build_view, documents_for_panel, get_settings, log_view, save_settings, settings_by_token,
)

router = APIRouter()


def _provider(matter_id: str, contact_id: str) -> Provider:
    p = provider_by_id(matter_id, contact_id)
    if not p:
        raise HTTPException(404, "provider not found on this matter")
    return p


@router.get("/api/matters/{matter_id}/providers", response_model=list[Provider])
def providers(matter_id: str):
    return list_providers(matter_id)


@router.get("/api/matters/{matter_id}/share/{contact_id}", response_model=ShareSettings)
def share_get(matter_id: str, contact_id: str):
    _provider(matter_id, contact_id)
    return get_settings(matter_id, contact_id)


@router.put("/api/matters/{matter_id}/share/{contact_id}", response_model=ShareSettings)
def share_put(matter_id: str, contact_id: str, body: ShareSettings):
    _provider(matter_id, contact_id)
    return save_settings(matter_id, contact_id, body)


@router.get("/api/matters/{matter_id}/share/{contact_id}/documents")
def share_documents(matter_id: str, contact_id: str) -> list[dict]:
    """Documents the attorney may tick for this provider; provider-related ones first."""
    return documents_for_panel(matter_id, _provider(matter_id, contact_id), load_dashboard(matter_id))


@router.post("/api/matters/{matter_id}/share/{contact_id}/preview", response_model=ProviderView)
def share_preview(matter_id: str, contact_id: str, body: ShareSettings):
    """What the provider would see with these (unsaved) settings. Not logged."""
    try:
        saved = get_settings(matter_id, contact_id)  # preview what their next visit shows
        return build_view(matter_id, _provider(matter_id, contact_id), body, since=saved.last_viewed_at)
    except LookupError as e:
        raise HTTPException(404, str(e))


def _by_token(token: str) -> tuple[str, ShareSettings]:
    found = settings_by_token(token)
    if not found:
        raise HTTPException(404, "link not found or revoked")
    return found


@router.get("/api/share/{token}", response_model=ProviderView)
def provider_view(token: str, request: Request):
    matter_id, s = _by_token(token)
    try:
        # s.last_viewed_at is read before this visit is logged = the previous view.
        view = build_view(matter_id, _provider(matter_id, s.contact_id), s, since=s.last_viewed_at)
    except LookupError as e:
        raise HTTPException(404, str(e))
    log_view(token, request.headers.get("user-agent"))
    return view


def _shared_source(token: str, source_id: str):
    matter_id, s = _by_token(token)
    if not s.sections.documents or source_id not in s.source_ids:
        raise HTTPException(404, "not shared")
    with connect() as conn:
        row = conn.execute("SELECT * FROM sources WHERE id=? AND matter_id=? AND kind='document'",
                           (source_id, matter_id)).fetchone()
        pages = conn.execute("SELECT page_no, width, height, ocr FROM pages WHERE source_id=? ORDER BY page_no",
                             (source_id,)).fetchall()
    if not row:
        raise HTTPException(404, "not shared")
    return row, pages


@router.get("/api/share/{token}/sources/{source_id}", response_model=SourceDetail)
def shared_source(token: str, source_id: str):
    row, pages = _shared_source(token, source_id)
    return SourceDetail(
        id=row["id"], kind=row["kind"], title=row["title"] or "", date=row["date"], author=row["author"],
        text=row["text"] or "", page_count=row["page_count"], has_file=bool(row["file_path"]),
        pages=[SourcePage(page_no=p["page_no"], width=p["width"] or 0, height=p["height"] or 0, ocr=bool(p["ocr"]))
               for p in pages],
    )


@router.get("/api/share/{token}/sources/{source_id}/file")
def shared_source_file(token: str, source_id: str):
    row, _ = _shared_source(token, source_id)
    path = (FILES_DIR / (row["file_path"] or "")).resolve()
    if not row["file_path"] or not path.is_file() or FILES_DIR.resolve() not in path.parents:
        raise HTTPException(404, "file not available")
    return FileResponse(path, media_type="application/pdf", filename=path.name,
                        content_disposition_type="inline")
