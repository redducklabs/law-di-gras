# Hosted demo: demo.redducklaw.com

One DigitalOcean Droplet (`law-di-gras-demo`, sfo3, s-1vcpu-2gb, about $12/mo)
running Docker Compose: `api` (FastAPI) and `caddy` (Let's Encrypt TLS, static
frontend, `/api` proxy, basic auth). Provider links (`/p/*`, `/api/share/*`)
and the static bundle skip basic auth.

| Where | What |
|---|---|
| `/opt/law-di-gras/{backend,deploy,frontend-dist}` | code, shipped by CI |
| `/etc/law-di-gras/app.env`, `auth.caddy` | secrets + basic auth, written by CI (mode 600) |
| `/var/lib/law-di-gras` | SQLite + downloaded files, seeded from a laptop |

## GitHub configuration

Repository **secrets** (Settings → Secrets and variables → Actions):

| Secret | Required | Value |
|---|---|---|
| `DO_TOKEN` | yes | DigitalOcean API token, read+write (Droplets, SSH keys, Domains) |
| `DEMO_SSH_KEY` | yes | private key of the deploy keypair (`~/.ssh/law_di_gras_demo`) |
| `DEMO_BASIC_AUTH_PASSWORD` | yes | password for the site's basic auth |
| `ANTHROPIC_API_KEY` | yes | AI drafts, Ask, re-digest |
| `OPENAI_API_KEY` | yes | query embeddings for Find / Ask |
| `COHERE_API_KEY` | optional | rerank; without it search uses RRF order |
| `CLIO_CLIENT_ID`, `CLIO_CLIENT_SECRET`, `CLIO_ACCESS_TOKEN`, `CLIO_REFRESH_TOKEN` | optional | only for live re-sync on the server. Leave unset for the hackathon: a server-side token refresh could invalidate the laptop's Clio token. |

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

## Ops

```bash
ssh -i ~/.ssh/law_di_gras_demo root@<ip>
cd /opt/law-di-gras/deploy && docker compose logs -f --tail 100
```

Teardown: `doctl compute droplet delete law-di-gras-demo` and delete the
`demo` A record. Nothing else in the `redducklaw.com` zone is touched.
