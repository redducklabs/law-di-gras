"""Minimal firm sign-in: one user from .env, HMAC-signed HttpOnly session cookie.

Credentials: APP_LOGIN_USER / APP_LOGIN_PASSWORD in the main .env (falls back to
the hosted demo's DEMO_AUTH_USER / DEMO_AUTH_PASSWORD). No user set = auth off.
Cookie key: APP_SESSION_SECRET, generated into the main .env on first use.
Values are never logged or echoed.
"""

import hashlib
import hmac
import logging
import os
import secrets
import time

log = logging.getLogger("auth")

COOKIE = "ldg_session"  # same name as app/demo_auth.py, so one sign-in serves both
TTL = 7 * 24 * 3600

# Paths that never need a session: sign-in itself, health, and provider share links
# (/api/share/{token} and its token-scoped document routes).
PUBLIC_PREFIXES = ("/api/auth/", "/api/health", "/api/share/")


def creds() -> tuple[str, str]:
    user = os.getenv("APP_LOGIN_USER") or os.getenv("DEMO_AUTH_USER") or ""
    pw = os.getenv("APP_LOGIN_PASSWORD") or os.getenv("DEMO_AUTH_PASSWORD") or ""
    return user, pw


def enabled() -> bool:
    user, pw = creds()
    return bool(user and pw)


_key: bytes | None = None


def _secret() -> bytes:
    global _key
    if _key is None:
        s = os.getenv("APP_SESSION_SECRET")
        if not s:
            s = secrets.token_urlsafe(32)
            try:
                from app.clio.envfile import set_env_values
                set_env_values({"APP_SESSION_SECRET": s})  # main .env; value never printed
                log.info("generated APP_SESSION_SECRET into the main .env")
            except Exception:
                log.warning("could not persist APP_SESSION_SECRET; sessions reset on restart")
        _key = hashlib.sha256(b"ldg-app-session:" + s.encode()).digest()
    return _key


def _sign(user: str, exp: int) -> str:
    return hmac.new(_secret(), f"{user}|{exp}".encode(), hashlib.sha256).hexdigest()


def make_cookie(user: str) -> str:
    exp = int(time.time()) + TTL
    return f"{user}|{exp}|{_sign(user, exp)}"


def session_user(cookie: str | None) -> str | None:
    """The signed-in user for a cookie value, or None."""
    if not cookie:
        return None
    try:
        user, exp, sig = cookie.rsplit("|", 2)
    except ValueError:
        return None
    if not exp.isdigit() or int(exp) < time.time():
        return None
    if not hmac.compare_digest(sig, _sign(user, int(exp))):
        return None
    return user if user == creds()[0] else None


def check_password(username: str, password: str) -> bool:
    user, pw = creds()
    if not (user and pw):
        return False
    # Compare both, always, so timing does not reveal which one failed.
    u_ok = hmac.compare_digest(username.strip().encode(), user.encode())
    p_ok = hmac.compare_digest(password.encode(), pw.encode())
    return u_ok and p_ok


def is_public(path: str) -> bool:
    return not path.startswith("/api/") or path.startswith(PUBLIC_PREFIXES)
