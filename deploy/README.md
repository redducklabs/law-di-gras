# Hosted demo: demo.redducklaw.com

One DigitalOcean Droplet (`law-di-gras-demo`, sfo3, s-1vcpu-2gb, about $12/mo)
running Docker Compose: `api` (FastAPI) and `caddy` (Let's Encrypt TLS, static
frontend, `/api` proxy). Sign-in is a branded `/login` page with a session
cookie (`backend/app/demo_auth.py`, checked by Caddy `forward_auth`). Provider
links (`/p/*`, `/api/share/*`), the static bundle and `/brand/*` logos are public.

| Where | What |
|---|---|
| `/opt/law-di-gras/{backend,deploy,frontend-dist}` | code, shipped by CI |
| `/etc/law-di-gras/app.env` | secrets + sign-in credentials, written by CI (mode 600) |
| `/var/lib/law-di-gras` | SQLite + downloaded files (seeded from a laptop) + `clio.env` (tokens from Connect Clio) |

## GitHub configuration

Repository **secrets** (Settings → Secrets and variables → Actions):

| Secret | Required | Value |
|---|---|---|
| `DO_TOKEN` | yes | DigitalOcean API token, read+write (Droplets, SSH keys, Domains) |
| `DEMO_SSH_KEY` | yes | private key of the deploy keypair (`~/.ssh/law_di_gras_demo`) |
| `DEMO_BASIC_AUTH_PASSWORD` | yes | sign-in password for the site |
| `ANTHROPIC_API_KEY` | yes | AI drafts, Ask, re-digest |
| `OPENAI_API_KEY` | yes | query embeddings for Find / Ask |
| `COHERE_API_KEY` | optional | rerank; without it search uses RRF order |
| `CLIO_CLIENT_ID`, `CLIO_CLIENT_SECRET` | for refresh | Clio app credentials. Tokens are NOT secrets: sign in, open `/api/clio`, click Connect Clio. |

Repository **variables** (optional): `DEMO_BASIC_AUTH_USER` (default `demo`),
`DEMO_DOMAIN` (default `demo.redducklaw.com`), `CASE_VALUE_MULTIPLIER_LOW` /
`_HIGH` (match the local `.env` if it overrides the 1.5 / 3.0 defaults).

## First deploy

1. Actions → **demo-provision** → Run, type `CREATE`. Creates the Droplet,
   registers the deploy key, and creates/updates only the `demo` A record.
2. Actions → **demo-deploy** → Run (later pushes to `main` that touch
   `backend/`, `frontend/`, `deploy/` deploy automatically).
3. Seed the case data from the laptop (Git Bash, repo root):
   `deploy/seed-data.sh`. Data never goes through GitHub (the repo is public).

Re-run step 3 whenever the local digest changes. Code deploys keep the data.

## Refresh from Clio on the server

1. In the Clio developer app, add the redirect URI
   `https://demo.redducklaw.com/api/clio/callback` (keep the 127.0.0.1 one for local).
2. Sign in, open `https://demo.redducklaw.com/api/clio`, click **Connect Clio**
   and approve. Tokens land in `/var/lib/law-di-gras/clio.env`.
3. Click **Sync from Clio + re-digest** (GET-only sync, then a forced digest;
   new scanned pages OCR with RapidOCR, slower than the laptop).

## Ops

```bash
ssh -i ~/.ssh/law_di_gras_demo root@<ip>
cd /opt/law-di-gras/deploy && docker compose logs -f --tail 100
```

Teardown: `doctl compute droplet delete law-di-gras-demo` and delete the
`demo` A record. Nothing else in the `redducklaw.com` zone is touched.
