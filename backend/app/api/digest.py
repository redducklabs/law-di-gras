"""S2 routes: digest (cached), dashboard, search, ask."""

from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool

from app.digest import dashboard
from app.digest.ask import ask as ask_question
from app.retrieval.search import search as hybrid_search
from app.schemas import Answer, AskRequest, Dashboard, Passage

router = APIRouter(prefix="/api/matters/{matter_id}", tags=["digest"])


@router.post("/digest", response_model=Dashboard)
async def digest(matter_id: str, force: bool = False) -> Dashboard:
    try:
        return await run_in_threadpool(dashboard.build, matter_id, force)
    except LookupError as e:
        raise HTTPException(404, str(e))


@router.get("/dashboard", response_model=Dashboard)
def get_dashboard(matter_id: str) -> Dashboard:
    d = dashboard.cached(matter_id)
    if d is None:
        raise HTTPException(404, "no digest yet; POST /digest first")
    return d


@router.get("/search", response_model=list[Passage])
def search(matter_id: str, q: str, k: int = 8) -> list[Passage]:
    if not q.strip():
        return []
    return hybrid_search(matter_id, q, top_k=min(k, 20))


@router.post("/ask", response_model=Answer)
def ask(matter_id: str, body: AskRequest) -> Answer:
    if not body.question.strip():
        raise HTTPException(400, "empty question")
    return ask_question(matter_id, body.question.strip())
