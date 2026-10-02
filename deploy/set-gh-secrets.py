"""Load the demo's GitHub Actions secrets and variables. Prints names only, never values.

Sources: the main checkout's .env (AI + Clio keys), doctl's saved token (DO_TOKEN),
~/.ssh/law_di_gras_demo (deploy key), and a generated basic-auth password kept in
~/law-di-gras-demo-credentials.txt (outside the repo; hand it over from there).

Run from the backend venv so python-dotenv is available:
    cd backend && uv run python ../deploy/set-gh-secrets.py
"""

import os
import re
import secrets
import subprocess
from pathlib import Path

from dotenv import dotenv_values

REPO = "redducklabs/law-di-gras"
HOME = Path.home()
MAIN_ROOT = Path(subprocess.run(
    ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
    capture_output=True, text=True, check=True,
).stdout.strip()).parent
env = dotenv_values(MAIN_ROOT / ".env")


def put(kind: str, name: str, value: str) -> None:
    if not value:
        print(f"skip {name} (no value)")
        return
    r = subprocess.run(["gh", kind, "set", name, "--repo", REPO], input=value, text=True, capture_output=True)
    print(f"{kind} {name}: {'ok' if r.returncode == 0 else 'FAILED ' + r.stderr.strip()[:200]}")


cred = HOME / "law-di-gras-demo-credentials.txt"
if cred.exists():
    pw = re.search(r"password: (\S+)", cred.read_text()).group(1)
else:
    pw = secrets.token_urlsafe(18)
    cred.write_text(f"https://demo.redducklaw.com\nuser: demo\npassword: {pw}\n")
put("secret", "DEMO_BASIC_AUTH_PASSWORD", pw)
put("secret", "DEMO_SSH_KEY", (HOME / ".ssh" / "law_di_gras_demo").read_text())

doctl_cfg = Path(os.environ.get("APPDATA", HOME / ".config")) / "doctl" / "config.yaml"
m = re.search(r"^access-token:\s*(\S+)", doctl_cfg.read_text(), re.M) if doctl_cfg.exists() else None
put("secret", "DO_TOKEN", m.group(1) if m else "")

for k in ["ANTHROPIC_API_KEY", "OPENAI_API_KEY", "COHERE_API_KEY",
          "CLIO_CLIENT_ID", "CLIO_CLIENT_SECRET", "CLIO_ACCESS_TOKEN", "CLIO_REFRESH_TOKEN"]:
    put("secret", k, env.get(k) or "")

put("variable", "DEMO_BASIC_AUTH_USER", "demo")
put("variable", "DEMO_DOMAIN", "demo.redducklaw.com")
for k in ["CASE_VALUE_MULTIPLIER_LOW", "CASE_VALUE_MULTIPLIER_HIGH"]:
    put("variable", k, env.get(k) or "")
