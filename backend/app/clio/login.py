"""One-time Clio OAuth 2.0 login. Writes tokens to the main checkout's .env.

Run: cd backend && uv run python -m app.clio.login
Opens the browser to Clio's consent page, catches the redirect on
CLIO_REDIRECT_URI, exchanges the code, and stores CLIO_ACCESS_TOKEN /
CLIO_REFRESH_TOKEN without printing them.
"""

import secrets
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlencode, urlparse

import httpx

from app import config
from app.clio.envfile import set_env_values


def main() -> None:
    redirect = urlparse(config.CLIO_REDIRECT_URI)
    state = secrets.token_urlsafe(16)
    result: dict = {}

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802
            u = urlparse(self.path)
            if u.path != redirect.path:
                self.send_response(404)
                self.end_headers()
                return
            q = parse_qs(u.query)
            result.update({k: v[0] for k, v in q.items()})
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(b"<h3>Clio connected. You can close this tab.</h3>")
            threading.Thread(target=server.shutdown, daemon=True).start()

        def log_message(self, *a):
            pass

    server = HTTPServer((redirect.hostname or "127.0.0.1", redirect.port or 8765), Handler)
    url = f"{config.CLIO_BASE_URL}/oauth/authorize?" + urlencode({
        "response_type": "code",
        "client_id": config.CLIO_CLIENT_ID,
        "redirect_uri": config.CLIO_REDIRECT_URI,
        "state": state,
    })
    print("Opening Clio consent page in your browser...")
    webbrowser.open(url)
    server.serve_forever()

    if result.get("state") != state or "code" not in result:
        raise SystemExit(f"OAuth failed: {result.get('error', 'missing code or bad state')}")
    r = httpx.post(f"{config.CLIO_BASE_URL}/oauth/token", data={
        "grant_type": "authorization_code",
        "code": result["code"],
        "redirect_uri": config.CLIO_REDIRECT_URI,
        "client_id": config.CLIO_CLIENT_ID,
        "client_secret": config.CLIO_CLIENT_SECRET,
    })
    r.raise_for_status()
    tok = r.json()
    set_env_values({"CLIO_ACCESS_TOKEN": tok["access_token"], "CLIO_REFRESH_TOKEN": tok.get("refresh_token", "")})
    print(f"Tokens saved to {config.ENV_PATH}")


if __name__ == "__main__":
    main()
