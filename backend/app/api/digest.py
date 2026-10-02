"""S2 routes: digest (cached), dashboard, search, ask."""

from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool

from app.digest import dashboard
from app.digest.ask import ask as ask_question
from app.digest.extract import ExtractionFailed
from app.retrieval.search import search as hybrid_search
from app.digest.chat import chat as chat_answer
from app.digest.draft import draft as make_draft
from app.schemas import Answer, AskRequest, ChatRequest, ChatResponse, Dashboard, Draft, DraftRequest, Passage

router = APIRouter(tags=["digest"])
M = "/api/matters/{matter_id}"


@router.post(M + "/digest", response_model=Dashboard)
async def digest(matter_id: str, force: bool = False) -> Dashboard:
    try:
        return await run_in_threadpool(dashboard.build, matter_id, force)
    except LookupError as e:
        raise HTTPException(404, str(e))
    except ExtractionFailed as e:
        raise HTTPException(502, f"{e}; previous dashboard kept, retry POST /digest")


@router.get(M + "/dashboard", response_model=Dashboard)
def get_dashboard(matter_id: str) -> Dashboard:
    d = dashboard.cached(matter_id)
    if d is None:
        raise HTTPException(404, "no digest yet; POST /digest first")
    return d


@router.get(M + "/search", response_model=list[Passage])
def search(matter_id: str, q: str, k: int = 8) -> list[Passage]:
    if not q.strip():
        return []
    return hybrid_search(matter_id, q, top_k=min(k, 20))


@router.post(M + "/ask", response_model=Answer)
def ask(matter_id: str, body: AskRequest) -> Answer:
    if not body.question.strip():
        raise HTTPException(400, "empty question")
    return ask_question(matter_id, body.question.strip())


@router.post(M + "/draft", response_model=Draft)
def draft(matter_id: str, body: DraftRequest) -> Draft:
    """Grounded draft for one next step. Returned for review only; nothing is sent."""
    try:
        return make_draft(matter_id, body)
    except LookupError as e:
        raise HTTPException(404, str(e))



@router.get("/api/pipeline")
def pipeline() -> dict:
    """Digest pipeline revision this server runs (compare across servers before a digest)."""
    return {"pipeline_rev": dashboard.PIPELINE_REV, "pipeline_version": dashboard.PIPELINE_VERSION}


@router.post(M + "/chat", response_model=ChatResponse)
def chat(matter_id: str, body: ChatRequest) -> ChatResponse:
    """Multi-turn ask-the-case: cited, verified answer plus server-validated deeplinks."""
    try:
        return chat_answer(matter_id, body)
    except ValueError as e:
        raise HTTPException(400, str(e))
