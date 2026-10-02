"""Update keys in the MAIN checkout's .env (shared by every worktree). Never echoes values."""

import os

from app.config import ENV_PATH


def set_env_values(values: dict[str, str]) -> None:
    lines = ENV_PATH.read_text(encoding="utf-8").splitlines() if ENV_PATH.exists() else []
    seen = set()
    for i, line in enumerate(lines):
        key = line.split("=", 1)[0].strip()
        if key in values:
            lines[i] = f"{key}={values[key]}"
            seen.add(key)
    lines += [f"{k}={v}" for k, v in values.items() if k not in seen]
    ENV_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    os.environ.update(values)
