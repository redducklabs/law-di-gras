"""FastAPI app. Integration owns this file; streams own their routers.

Run: cd backend && uv run uvicorn app.main:app --reload --port 8000
(each worktree uses its own port; see the plan's port table)
"""

import importlib
import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.auth import session

from app.db import init_db

log = logging.getLogger("app")

app = FastAPI(title="Law-di-gras")
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()

if not session.enabled():
    log.warning("APP_LOGIN_USER/APP_LOGIN_PASSWORD not set: firm sign-in is DISABLED (all /api open)")


@app.middleware("http")
async def require_session(request: Request, call_next):
    """Every /api/* needs a firm session except sign-in, health and provider share links."""
    if (session.enabled() and request.method != "OPTIONS" and not session.is_public(request.url.path)
            and not session.session_user(request.cookies.get(session.COOKIE))):
        return JSONResponse({"detail": "sign in required"}, status_code=401)
    return await call_next(request)

# Each stream exposes `router` in its module. Missing modules are skipped so
# streams can land independently.
# app.api.auth must precede app.demo_auth: it owns the shared /api/auth/* routes.
for module in ("app.api.auth", "app.api.cases", "app.api.sources", "app.api.digest", "app.api.share",
               "app.clio.web", "app.demo_auth"):
    try:
        app.include_router(importlib.import_module(module).router)
    except ModuleNotFoundError as e:
        if e.name != module:
            raise
        log.warning("router %s not present yet", module)


@app.get("/api/health")
def health() -> dict:
    try:
        from app.digest.dashboard import PIPELINE_REV
    except ImportError:
        PIPELINE_REV = None
    return {"ok": True, "pipeline_rev": PIPELINE_REV}
