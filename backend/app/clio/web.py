"""Clio connect + data refresh from the browser (the hosted demo has no CLI).

GET  /api/clio           status page: connect, sync + re-digest
GET  /api/clio/connect   redirect to Clio's consent page
GET  /api/clio/callback  exchange the code, store tokens (never echoed)
POST /api/clio/refresh   background job: sync the matter from Clio (GET only), then re-digest
GET  /api/clio/status    JSON status for the page

Needs CLIO_REDIRECT_URI pointing at /api/clio/callback on this host, registered
in the Clio developer app. Site-level basic auth protects these routes.
"""

import html
import logging
import secrets
import threading
import time
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse

from app import config
from app.clio import client as clio_client
from app.clio.envfile import set_env_values
from app.db import connect

log = logging.getLogger(__name__)
router = APIRouter(tags=["clio"])

_states: dict[str, float] = {}
_job: dict = {"state": "idle", "detail": "", "started": None, "finished": None}
_lock = threading.Lock()


def _connected() -> bool:
    import os
    return bool(os.getenv("CLIO_ACCESS_TOKEN") or os.getenv("CLIO_REFRESH_TOKEN"))


def _matter_id() -> str:
    with connect() as conn:
        row = conn.execute("SELECT id FROM matters ORDER BY id LIMIT 1").fetchone()
    return row[0] if row else "default"


@router.get("/api/clio/connect")
def connect_clio() -> RedirectResponse:
    if not (config.CLIO_CLIENT_ID and config.CLIO_CLIENT_SECRET):
        raise HTTPException(500, "CLIO_CLIENT_ID / CLIO_CLIENT_SECRET not configured")
    now = time.time()
    for s, t in list(_states.items()):
        if now - t > 600:
            _states.pop(s, None)
    state = secrets.token_urlsafe(16)
    _states[state] = now
    url = f"{config.CLIO_BASE_URL}/oauth/authorize?" + urlencode({
        "response_type": "code",
        "client_id": config.CLIO_CLIENT_ID,
        "redirect_uri": config.CLIO_REDIRECT_URI,
        "state": state,
    })
    return RedirectResponse(url)


@router.get("/api/clio/callback")
def callback(code: str | None = None, state: str | None = None, error: str | None = None) -> RedirectResponse:
    if error or not code or not state or _states.pop(state, None) is None:
        return RedirectResponse(f"/api/clio?msg={'Clio connect failed: ' + (error or 'bad or expired state')}")
    r = httpx.post(f"{config.CLIO_BASE_URL}/oauth/token", data={
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": config.CLIO_REDIRECT_URI,
        "client_id": config.CLIO_CLIENT_ID,
        "client_secret": config.CLIO_CLIENT_SECRET,
    }, timeout=30)
    if r.status_code != 200:
        log.warning("Clio token exchange failed: %s", r.status_code)
        return RedirectResponse(f"/api/clio?msg=Clio token exchange failed ({r.status_code})")
    tok = r.json()
    set_env_values({"CLIO_ACCESS_TOKEN": tok["access_token"], "CLIO_REFRESH_TOKEN": tok.get("refresh_token", "")})
    clio_client._client = None  # next call picks up the new tokens
    log.info("Clio connected")
    return RedirectResponse("/api/clio?msg=Clio connected")


def _run_refresh(matter_id: str) -> None:
    from app.clio.sync import sync_matter
    from app.digest import dashboard
    try:
        _job.update(detail="Syncing from Clio (read-only)…")
        stats = sync_matter(matter_id)
        summary = f"{stats.get('sources', 0)} sources, {stats.get('pages', 0)} pages, {len(stats.get('errors') or [])} errors"
        _job.update(detail=f"Synced {summary}. Re-digesting…")
        dashboard.build(str(stats["matter_id"]), True)
        _job.update(state="done", detail=f"Synced {summary}; brief re-digested.")
    except Exception as e:  # surfaced on the page; tokens never appear in these messages
        log.exception("Clio refresh failed")
        _job.update(state="failed", detail=f"{type(e).__name__}: {e}"[:400])
    finally:
        _job["finished"] = time.strftime("%H:%M:%S")


@router.post("/api/clio/refresh")
def refresh() -> dict:
    if not _connected():
        raise HTTPException(409, "Connect Clio first")
    with _lock:
        if _job["state"] == "running":
            return _job
        _job.update(state="running", detail="Starting…", started=time.strftime("%H:%M:%S"), finished=None)
        threading.Thread(target=_run_refresh, args=(_matter_id(),), daemon=True).start()
    return _job


@router.get("/api/clio/status")
def status() -> dict:
    return {"connected": _connected(), "job": _job}


@router.get("/api/clio", response_class=HTMLResponse)
def page(msg: str | None = None) -> str:
    note = f'<p class="msg">{html.escape(msg)}</p>' if msg else ""
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Clio data</title>
<link rel="icon" href="/favicon.png">
<style>
:root{{--bg:#f6f7f9;--card:#fff;--ink:#0f172a;--muted:#64748b;--line:#e2e8f0;--brand:#b91c1c}}
@media (prefers-color-scheme:dark){{:root{{--bg:#0b1020;--card:#121a2e;--ink:#e2e8f0;--muted:#94a3b8;--line:#22304d}}}}
body{{margin:0;background:var(--bg);color:var(--ink);font:14px/1.5 system-ui,-apple-system,Segoe UI,sans-serif;display:grid;place-items:center;min-height:100vh;padding:16px;box-sizing:border-box}}
.card{{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:24px;max-width:460px;width:100%}}
h1{{font-size:16px;margin:0 0 4px}} p{{margin:6px 0;color:var(--muted)}} .msg{{color:var(--ink);font-weight:600}}
.row{{display:flex;gap:8px;margin-top:16px;flex-wrap:wrap}}
a.btn,button{{font:inherit;font-weight:600;border-radius:8px;padding:8px 14px;cursor:pointer;text-decoration:none;border:1px solid var(--line);background:var(--card);color:var(--ink)}}
.primary{{background:var(--brand)!important;color:#fff!important;border-color:var(--brand)!important}}
button:disabled{{opacity:.5;cursor:default}} #job{{font-size:13px;min-height:1.5em;word-break:break-word}}
</style></head><body><div class="card">
<img src="/brand/redducklawyer.png" alt="" style="width:48px;height:48px;float:right"><h1>Clio data</h1><p>Connect the firm's Clio account (read-only), then pull the latest matter data and rebuild the brief.</p>
{note}<p id="conn">Checking connection…</p><p id="job"></p>
<div class="row"><a class="btn" id="connect" href="/api/clio/connect">Connect Clio</a>
<button class="primary" id="refresh" disabled>Sync from Clio + re-digest</button><a class="btn" href="/">Back to brief</a></div>
</div><script>
const $=id=>document.getElementById(id);
async function poll(){{
  const s=await (await fetch('/api/clio/status')).json(), j=s.job;
  $('conn').textContent=s.connected?'Clio: connected':'Clio: not connected';
  $('connect').textContent=s.connected?'Reconnect Clio':'Connect Clio';
  $('refresh').disabled=!s.connected||j.state==='running';
  $('job').textContent=j.state==='idle'?'':`${{j.state}} (started ${{j.started}}${{j.finished?', finished '+j.finished:''}}): ${{j.detail}}`;
  if(j.state==='running')setTimeout(poll,3000);
}}
$('refresh').onclick=async()=>{{await fetch('/api/clio/refresh',{{method:'POST'}});poll();}};
poll();
</script></body></html>"""
