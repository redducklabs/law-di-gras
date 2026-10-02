"""Pre-commit secret guard. Blocks staged .env files, known key formats, and any
value from the main checkout's .env. Never prints the secret itself."""
import re, subprocess, sys
from pathlib import Path


def git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True, encoding="utf-8", errors="replace").stdout


staged = [p for p in git("diff", "--cached", "--name-only", "--diff-filter=ACMR").splitlines() if p]
problems = []

for p in staged:
    name = Path(p).name
    if re.fullmatch(r"\.env(\..+)?", name) and name != ".env.example":
        problems.append(f"{p}: .env files must never be committed")

# Values from the main checkout's .env (shared by all worktrees).
main_root = Path(git("rev-parse", "--path-format=absolute", "--git-common-dir").strip()).parent
secrets = []
env_file = main_root / ".env"
if env_file.exists():
    for line in env_file.read_text(encoding="utf-8", errors="replace").splitlines():
        m = re.match(r"\s*([A-Z0-9_]+)\s*=\s*(.*)", line)
        if m:
            v = m.group(2).strip().strip('"').strip("'")
            if len(v) >= 12 and not v.startswith("http"):
                secrets.append((m.group(1), v))

patterns = [
    ("Anthropic key", r"sk-ant-[A-Za-z0-9_\-]{20,}"),
    ("OpenAI key", r"sk-(proj-)?[A-Za-z0-9_\-]{32,}"),
    ("GitHub token", r"gh[pousr]_[A-Za-z0-9]{30,}"),
    ("AWS key", r"AKIA[0-9A-Z]{16}"),
    ("Bearer token", r"Bearer\s+[A-Za-z0-9\-_\.]{30,}"),
    ("Private key", r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
]

diff = git("diff", "--cached", "-U0", "--no-color")
current = None
for line in diff.splitlines():
    if line.startswith("+++ "):
        current = line[6:] if line.startswith("+++ b/") else line[4:]
        continue
    if not line.startswith("+") or line.startswith("+++"):
        continue
    for key, v in secrets:
        if v in line:
            problems.append(f"{current}: contains the value of {key} from .env")
    for label, pat in patterns:
        if re.search(pat, line):
            problems.append(f"{current}: looks like a {label}")

if problems:
    print("Commit blocked by secret guard:", file=sys.stderr)
    for p in sorted(set(problems)):
        print("  - " + p, file=sys.stderr)
    print("Unstage the file or remove the secret. Secrets belong only in the main checkout's .env.", file=sys.stderr)
    sys.exit(1)
