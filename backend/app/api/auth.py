"""Sign-in routes for the firm app. Provider share links stay public (see app/auth/session.py).

POST /api/auth/login accepts JSON {username, password} (the React sign-in page)
or a urlencoded form (the hosted demo's HTML page in app/demo_auth.py, which
keeps serving GET /api/auth/login). GET /api/auth/check is what Caddy's
forward_auth calls in the hosted deploy.
"""

import json
from urllib.parse import parse_qs, quote

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, RedirectResponse, Response

from app.auth import session

router = APIRouter(tags=["auth"])


def _https(request: Request) -> bool:
    return request.headers.get("x-forwarded-proto", request.url.scheme) == "https"


def _set(r: Response, request: Request, user: str) -> Response:
    r.set_cookie(session.COOKIE, session.make_cookie(user), max_age=session.TTL, httponly=True,
                 secure=_https(request), samesite="lax", path="/")
    return r


def _safe_next(nxt: str | None) -> str:
    return nxt if nxt and nxt.startswith("/") and not nxt.startswith("//") else "/"


@router.post("/api/auth/login")
async def login(request: Request) -> Response:
    body = (await request.body()).decode("utf-8", "replace")
    is_json = "json" in request.headers.get("content-type", "")
    if is_json:
        try:
            data = json.loads(body or "{}")
        except json.JSONDecodeError:
            data = {}
    else:
        data = {k: v[0] for k, v in parse_qs(body).items()}
    username, password = str(data.get("username", "")), str(data.get("password", ""))
    ok = session.check_password(username, password)
    if is_json:
        if not session.enabled():
            return JSONResponse({"ok": True, "user": None, "auth_enabled": False})
        if not ok:
            return JSONResponse({"detail": "That username and password didn't match."}, status_code=401)
        return _set(JSONResponse({"ok": True, "user": username.strip(), "auth_enabled": True}), request, username.strip())
    nxt = _safe_next(data.get("next"))
    if not ok:
        return RedirectResponse(f"/login?error=1&next={quote(nxt, safe='')}", status_code=303)
    return _set(RedirectResponse(nxt, status_code=303), request, username.strip())


@router.post("/api/auth/logout")
def logout_json() -> Response:
    r = JSONResponse({"ok": True})
    r.delete_cookie(session.COOKIE, path="/")
    return r


@router.get("/api/auth/logout")
def logout_redirect() -> Response:
    r = RedirectResponse("/login", status_code=302)
    r.delete_cookie(session.COOKIE, path="/")
    return r


@router.get("/api/auth/me")
def me(request: Request) -> Response:
    if not session.enabled():
        return JSONResponse({"user": None, "auth_enabled": False})
    user = session.session_user(request.cookies.get(session.COOKIE))
    if not user:
        return JSONResponse({"detail": "sign in required", "auth_enabled": True}, status_code=401)
    return JSONResponse({"user": user, "auth_enabled": True})


@router.get("/api/auth/check")
def check(request: Request) -> Response:
    """Caddy forward_auth: 200 passes; pages redirect to /login, API calls get 401."""
    if not session.enabled() or session.session_user(request.cookies.get(session.COOKIE)):
        return Response(status_code=200)
    uri = request.headers.get("X-Forwarded-Uri", "/")
    if uri.startswith("/api/") and "text/html" not in request.headers.get("accept", ""):
        return JSONResponse({"detail": "sign in required"}, status_code=401)
    return RedirectResponse(f"/login?next={quote(uri, safe='')}", status_code=302)
