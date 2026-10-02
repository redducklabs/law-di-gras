"""Read-only Clio Manage API client.

Clio is READ-ONLY for this project. This module is the only code that talks to
Clio, and it only ever issues HTTP GET. Token refresh posts to Clio's OAuth
token endpoint (not the data API); that is the one non-GET call and it changes
no case data.
"""

import logging
import os
import time
from typing import Any, Iterator

import httpx

from app import config
from app.clio.envfile import set_env_values

log = logging.getLogger("clio")

API = "/api/v4"


class ReadOnlyViolation(RuntimeError):
    pass


class ClioClient:
    def __init__(self) -> None:
        self.base = config.CLIO_BASE_URL.rstrip("/")
        self.access_token = os.getenv("CLIO_ACCESS_TOKEN", "")
        self.refresh_token = os.getenv("CLIO_REFRESH_TOKEN", "")
        self.http = httpx.Client(timeout=60, follow_redirects=True)

    # --- the only verb -----------------------------------------------------
    def request(self, method: str, *args, **kwargs):
        if method.upper() != "GET":
            raise ReadOnlyViolation(f"Clio is read-only; refused {method}")
        return self._get(*args, **kwargs)

    def get(self, path: str, params: dict | None = None) -> dict:
        return self._get(path, params).json()

    def download(self, path: str, params: dict | None = None) -> bytes:
        return self._get(path, params).content

    def paginate(self, path: str, params: dict | None = None) -> Iterator[dict]:
        """Yield every record across pages (cursor pagination via meta.paging.next)."""
        params = {"limit": 200, **(params or {})}
        url: str | None = path
        while url:
            body = self._get(url, params).json()
            yield from body.get("data") or []
            url = ((body.get("meta") or {}).get("paging") or {}).get("next")
            params = None  # next URL already carries the query

    # --- internals ---------------------------------------------------------
    def _url(self, path: str) -> str:
        if path.startswith("http"):
            return path
        if not path.startswith("/api/"):
            path = f"{API}/{path.lstrip('/')}"
        return self.base + path

    def _get(self, path: str, params: dict | None = None) -> httpx.Response:
        url = self._url(path)
        for attempt in range(6):
            r = self.http.get(url, params=params, headers={"Authorization": f"Bearer {self.access_token}"})
            if r.status_code == 401 and attempt == 0:
                self._refresh()
                continue
            if r.status_code == 429:
                wait = float(r.headers.get("Retry-After", "5"))
                log.warning("Clio rate limited; sleeping %ss", wait)
                time.sleep(min(wait, 60))
                continue
            if r.status_code >= 500 and attempt < 3:
                time.sleep(2 ** attempt)
                continue
            r.raise_for_status()
            return r
        r.raise_for_status()
        return r

    def _refresh(self) -> None:
        if not self.refresh_token:
            raise RuntimeError("Clio 401 and no refresh token; run python -m app.clio.login")
        r = self.http.post(
            f"{self.base}/oauth/token",
            data={
                "grant_type": "refresh_token",
                "refresh_token": self.refresh_token,
                "client_id": config.CLIO_CLIENT_ID,
                "client_secret": config.CLIO_CLIENT_SECRET,
            },
        )
        r.raise_for_status()
        tok = r.json()
        self.access_token = tok["access_token"]
        self.refresh_token = tok.get("refresh_token") or self.refresh_token
        set_env_values({"CLIO_ACCESS_TOKEN": self.access_token, "CLIO_REFRESH_TOKEN": self.refresh_token})
        log.info("Clio access token refreshed")


_client: ClioClient | None = None


def client() -> ClioClient:
    global _client
    if _client is None:
        _client = ClioClient()
    return _client
