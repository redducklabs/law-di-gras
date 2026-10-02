"""S7 routes: Blind spots (agentic whole-case review). GET is cached; POST runs the agent (1-3 min)."""

from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool

from app.review import agent
from app.schemas import CaseReview

router = APIRouter(tags=["review"])
M = "/api/matters/{matter_id}"


@router.get(M + "/review", response_model=CaseReview)
def get_review(matter_id: str) -> CaseReview:
    r = agent.cached(matter_id)
    if r is None:
        raise HTTPException(404, "no review yet; POST /review first")
    return r


@router.post(M + "/review", response_model=CaseReview)
async def run_review(matter_id: str, force: bool = False) -> CaseReview:
    try:
        return await run_in_threadpool(agent.build, matter_id, force)
    except LookupError as e:
        raise HTTPException(404, str(e))
