"""Settings shared by every stream.

Worktrees: `.env` and the SQLite data dir live in the MAIN checkout, so every
worktree session reads the same credentials and the same synced Sapini data.
"""

import os
import subprocess
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent.parent


def _main_checkout() -> Path:
    """Root of the main checkout, even when running inside a git worktree."""
    try:
        common = subprocess.run(
            ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
            cwd=BACKEND_DIR, capture_output=True, text=True, check=True,
        ).stdout.strip()
        return Path(common).parent
    except Exception:
        return BACKEND_DIR.parent


REPO_ROOT = _main_checkout()
ENV_PATH = REPO_ROOT / ".env"
load_dotenv(ENV_PATH)

DATA_DIR = Path(os.getenv("DATA_DIR") or REPO_ROOT / "backend" / "data")
FILES_DIR = DATA_DIR / "files"
DB_PATH = DATA_DIR / "app.db"
DATA_DIR.mkdir(parents=True, exist_ok=True)
FILES_DIR.mkdir(parents=True, exist_ok=True)

CLIO_BASE_URL = os.getenv("CLIO_BASE_URL", "https://app.clio.com")
CLIO_CLIENT_ID = os.getenv("CLIO_CLIENT_ID", "")
CLIO_CLIENT_SECRET = os.getenv("CLIO_CLIENT_SECRET", "")
CLIO_REDIRECT_URI = os.getenv("CLIO_REDIRECT_URI", "http://127.0.0.1:8765/clio/callback")
# Name (or substring) of the matter to digest; resolved against Clio at runtime.
MATTER_QUERY = os.getenv("MATTER_QUERY", "Sapini")

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
COHERE_API_KEY = os.getenv("COHERE_API_KEY", "")

# Firm setting: draft case-value rule = these multipliers x billed specials (admin-editable via .env).
CASE_VALUE_MULTIPLIER_LOW = float(os.getenv("CASE_VALUE_MULTIPLIER_LOW") or 1.5)
CASE_VALUE_MULTIPLIER_HIGH = float(os.getenv("CASE_VALUE_MULTIPLIER_HIGH") or 3.0)
