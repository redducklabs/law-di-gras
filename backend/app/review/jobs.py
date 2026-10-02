"""Background Blind spots runs: one per matter, progress kept in memory for GET /review to report."""

import threading
import traceback
from datetime import datetime, timezone

from app.review import agent
from app.schemas import CaseReview, RunProgress

_lock = threading.Lock()
_runs: dict[str, RunProgress] = {}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def progress(matter_id: str) -> RunProgress | None:
    return _runs.get(matter_id)


def current(matter_id: str) -> CaseReview:
    """Last completed review (or an empty one) plus the run state, if any."""
    r = agent.cached(matter_id) or CaseReview(matter_id=matter_id, generated_at="", cost_usd=0.0,
                                              model=agent.MODEL_OPUS, findings=[])
    r.run = _runs.get(matter_id)
    return r


def start(matter_id: str, force: bool = False) -> CaseReview:
    """Start a run in a background thread unless one is already running; return immediately."""
    with _lock:
        cur = _runs.get(matter_id)
        if not (cur and cur.status in ("queued", "running")):
            _runs[matter_id] = RunProgress(status="running", stage="Starting", pct=1, started_at=_now())
            threading.Thread(target=_work, args=(matter_id, force), daemon=True, name=f"review-{matter_id}").start()
    return current(matter_id)


def _work(matter_id: str, force: bool) -> None:
    def report(stage: str, pct: int) -> None:
        p = _runs[matter_id]
        _runs[matter_id] = p.model_copy(update={"stage": stage, "pct": max(p.pct, min(pct, 99))})

    try:
        agent.build(matter_id, force=force, progress=report)
        p = _runs[matter_id]
        _runs[matter_id] = p.model_copy(update={"status": "done", "stage": "Done", "pct": 100, "finished_at": _now()})
    except Exception as e:  # keep the previous review; surface the error
        traceback.print_exc()
        p = _runs[matter_id]
        _runs[matter_id] = p.model_copy(update={"status": "failed", "stage": "Failed", "finished_at": _now(),
                                                "error": str(e)[:300]})
