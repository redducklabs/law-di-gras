"""S6 route: built-in audit of the cached dashboard or Blind spots review. GET only; runs in the background."""

from typing import Literal

from fastapi import APIRouter, HTTPException

from app.audit.builtin import get_report
from app.schemas import AuditReport

router = APIRouter(tags=["audit"])


@router.get("/api/matters/{matter_id}/audit", response_model=AuditReport)
def audit(matter_id: str, target: Literal["dashboard", "review"] = "dashboard") -> AuditReport:
    """Stored audit for the current payload; otherwise starts one (once per payload) and returns its progress."""
    rep = get_report(matter_id, target)
    if rep is None:
        raise HTTPException(404, f"no {target} to audit yet")
    return rep
