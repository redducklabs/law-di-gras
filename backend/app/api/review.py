"""S7 routes: Blind spots (agentic whole-case review).

GET returns the last completed review plus `run` while a background run is in flight.
POST starts a background run (one per matter) and returns immediately.
"""

from fastapi import APIRouter, HTTPException

from app.digest import dashboard
from app.review import jobs
from app.schemas import CaseReview

router = APIRouter(tags=["review"])
M = "/api/matters/{matter_id}"


@router.get(M + "/review", response_model=CaseReview)
def get_review(matter_id: str) -> CaseReview:
    r = jobs.current(matter_id)
    if not r.findings and r.run is None and not r.generated_at:
        raise HTTPException(404, "no review yet; POST /review first")
    return r


@router.post(M + "/review", response_model=CaseReview)
def run_review(matter_id: str, force: bool = False) -> CaseReview:
    if dashboard.cached(matter_id) is None:
        raise HTTPException(404, "no dashboard yet for this matter")
    return jobs.start(matter_id, force)
