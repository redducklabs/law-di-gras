#!/usr/bin/env bash
# Copy a snapshot of the local Sapini data (SQLite + downloaded files) to the
# demo Droplet. Run from Git Bash on the machine that has the synced data.
# Case data goes laptop -> Droplet over SSH only; never through GitHub.
#
#   deploy/seed-data.sh            # uses ~/.ssh/law_di_gras_demo and doctl to find the Droplet
#
# Safe while the local app runs: SQLite's online backup API takes a consistent copy.
set -euo pipefail

KEY="${DEMO_SSH_KEY_FILE:-$HOME/.ssh/law_di_gras_demo}"
MAIN_ROOT="$(dirname "$(git rev-parse --path-format=absolute --git-common-dir)")"
DATA="${DATA_DIR:-$MAIN_ROOT/backend/data}"
W() { if command -v cygpath >/dev/null; then cygpath -m "$1"; else echo "$1"; fi; }  # Windows python needs C:/ paths
IP="${DEMO_IP:-$(doctl compute droplet list --format Name,PublicIPv4 --no-header | awk '$1=="law-di-gras-demo"{print $2}')}"
[ -n "$IP" ] || { echo "No law-di-gras-demo Droplet found"; exit 1; }

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
mkdir -p "$TMP/snap"

echo "Snapshotting $DATA/app.db"
python -c "import sqlite3,sys; s=sqlite3.connect(sys.argv[1]); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" \
  "$(W "$DATA/app.db")" "$(W "$TMP/snap/app.db")"
cp -r "$DATA/files" "$TMP/snap/files"
tar -C "$TMP/snap" -czf "$TMP/data.tgz" .
du -h "$TMP/data.tgz"

SSH=(ssh -i "$KEY" -o StrictHostKeyChecking=accept-new "root@$IP")
scp -i "$KEY" -o StrictHostKeyChecking=accept-new "$TMP/data.tgz" "root@$IP:/tmp/data.tgz"
"${SSH[@]}" 'set -e
  cd /opt/law-di-gras/deploy 2>/dev/null && docker compose stop api || true
  rm -rf /var/lib/law-di-gras/app.db* /var/lib/law-di-gras/files
  tar -C /var/lib/law-di-gras -xzf /tmp/data.tgz && rm /tmp/data.tgz
  cd /opt/law-di-gras/deploy 2>/dev/null && docker compose start api || true
  ls -la /var/lib/law-di-gras'
echo "Seeded $IP"
