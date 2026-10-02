"""Sign-in page + session cookie for the hosted demo.

Only active behind Caddy (deploy/Caddyfile): Caddy's forward_auth asks
/api/auth/check on every protected request. Local dev never calls it.
Credentials: DEMO_AUTH_USER / DEMO_AUTH_PASSWORD in the server env. The cookie
is HMAC-signed with a key derived from the password, so changing the password
signs everyone out.
"""

import hashlib
import hmac
import html
import os
import time
from urllib.parse import parse_qs, quote

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response

router = APIRouter(tags=["auth"])
COOKIE = "ldg_session"
TTL = 7 * 24 * 3600


def _creds() -> tuple[str, str]:
    return os.getenv("DEMO_AUTH_USER", "demo"), os.getenv("DEMO_AUTH_PASSWORD", "")


def _sign(exp: int) -> str:
    _, pw = _creds()
    key = hashlib.sha256(b"ldg-session:" + pw.encode()).digest()
    return hmac.new(key, str(exp).encode(), hashlib.sha256).hexdigest()


def _valid(cookie: str | None) -> bool:
    if not cookie or not _creds()[1]:
        return False
    exp, _, sig = cookie.partition(".")
    return exp.isdigit() and int(exp) > time.time() and hmac.compare_digest(sig, _sign(int(exp)))


def _safe_next(nxt: str | None) -> str:
    return nxt if nxt and nxt.startswith("/") and not nxt.startswith("//") else "/"


@router.get("/api/auth/check")
def check(request: Request) -> Response:
    if _valid(request.cookies.get(COOKIE)):
        return Response(status_code=200)
    uri = request.headers.get("X-Forwarded-Uri", "/")
    if uri.startswith("/api/") and "text/html" not in request.headers.get("accept", ""):
        return JSONResponse({"detail": "sign in required"}, status_code=401)
    return RedirectResponse(f"/login?next={quote(uri, safe='')}", status_code=302)


@router.get("/api/auth/login", response_class=HTMLResponse)
def login_page(request: Request, next: str | None = None, error: str | None = None) -> Response:
    if _valid(request.cookies.get(COOKIE)):
        return RedirectResponse(_safe_next(next), status_code=302)
    return HTMLResponse(_page(_safe_next(next), bool(error)))


@router.post("/api/auth/login")
async def login(request: Request) -> Response:
    # Plain urlencoded form; parsed by hand to avoid adding python-multipart.
    form = {k: v[0] for k, v in parse_qs((await request.body()).decode()).items()}
    username, password, next = form.get("username", ""), form.get("password", ""), form.get("next", "/")
    user, pw = _creds()
    ok = pw and hmac.compare_digest(username.strip(), user) and hmac.compare_digest(password, pw)
    if not ok:
        return RedirectResponse(f"/login?error=1&next={quote(_safe_next(next), safe='')}", status_code=303)
    exp = int(time.time()) + TTL
    r = RedirectResponse(_safe_next(next), status_code=303)
    r.set_cookie(COOKIE, f"{exp}.{_sign(exp)}", max_age=TTL, httponly=True, secure=True, samesite="lax")
    return r


@router.get("/api/auth/logout")
def logout() -> Response:
    r = RedirectResponse("/login", status_code=302)
    r.delete_cookie(COOKIE)
    return r


def _page(nxt: str, error: bool) -> str:
    err = '<p class="err" role="alert">That username and password didn\'t match.</p>' if error else ""
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Sign in · Red Duck Lawyer</title><meta name="robots" content="noindex">
<link rel="icon" type="image/png" href="/favicon.png"><link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap">
<style>
:root{{--bg:#f5f6fa;--card:#fff;--ink:#0f172a;--muted:#64748b;--line:#e2e8f0;--field:#fff;--brand:#b91c1c;--brand-h:#991b1b;--ring:#fecaca;--err:#b91c1c;--errbg:#fef2f2}}
@media (prefers-color-scheme:dark){{:root{{--bg:#0b1020;--card:#111827;--ink:#e5e7eb;--muted:#94a3b8;--line:#1f2a44;--field:#0b1222;--ring:#7f1d1d;--errbg:#2a1215;--err:#fca5a5}}}}
*{{box-sizing:border-box}}
body{{margin:0;min-height:100vh;background:radial-gradient(1200px 600px at 50% -10%,rgba(185,28,28,.12),transparent 60%),var(--bg);
  color:var(--ink);font:14px/1.5 Inter,system-ui,-apple-system,Segoe UI,sans-serif;display:grid;place-items:center;padding:16px}}
main{{width:100%;max-width:380px}}
.brand{{text-align:center;margin-bottom:18px}}
.brand img{{width:132px;height:132px;display:block;margin:0 auto 6px}}
.brand b{{display:block;font-size:20px;letter-spacing:-.02em}}
.brand span{{color:var(--muted);font-size:13px}}
.card{{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:28px;box-shadow:0 1px 2px rgba(15,23,42,.04),0 8px 24px rgba(15,23,42,.06)}}
h1{{font-size:18px;margin:0;letter-spacing:-.01em}}
.sub{{margin:4px 0 20px;color:var(--muted);font-size:13px}}
label{{display:block;font-size:12px;font-weight:600;margin:14px 0 6px}}
input{{width:100%;font:inherit;padding:10px 12px;border:1px solid var(--line);border-radius:9px;background:var(--field);color:var(--ink);outline:none}}
input:focus{{border-color:var(--brand);box-shadow:0 0 0 3px var(--ring)}}
button{{width:100%;margin-top:20px;font:inherit;font-weight:600;color:#fff;background:var(--brand);border:0;border-radius:9px;padding:11px;cursor:pointer}}
button:hover{{background:var(--brand-h)}}
.err{{margin:0 0 4px;padding:9px 12px;border-radius:9px;background:var(--errbg);color:var(--err);font-size:13px}}
.foot{{text-align:center;color:var(--muted);font-size:12px;margin-top:16px}}
</style></head><body><main>
<div class="brand"><img src="/brand/redducklawyer-glow.png" alt="Red Duck Lawyer"><b>Red Duck Lawyer</b><span>Case Brief</span></div>
<div class="card">
<h1>Sign in</h1><p class="sub">Where the case stands, with every fact linked to its source.</p>
{err}
<form method="post" action="/login">
<input type="hidden" name="next" value="{html.escape(nxt)}">
<label for="u">Username</label><input id="u" name="username" autocomplete="username" required autofocus>
<label for="p">Password</label><input id="p" name="password" type="password" autocomplete="current-password" required>
<button type="submit">Sign in</button>
</form></div>
<p class="foot">Hosted demo by Red Duck Labs</p>
</main></body></html>"""
