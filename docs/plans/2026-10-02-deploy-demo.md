# Plan: demo on demo.redducklaw.com (separate session)

Goal: a hosted copy of the Case Brief demo at `https://demo.redducklaw.com`,
without touching local work or the existing redducklaw marketing site.

## Decisions (manager recommendation; confirm with Aron before acting)

- **Subdomain, not apex.** `redducklaw.com` and `www` belong to the App Platform
  landing app (`C:\Repos\redducklaw\infra\landing`). Leave it alone; add one DNS
  A record `demo` in the DigitalOcean-hosted zone. Never touch MX, DKIM or
  google-site-verification records.
- **One Droplet, not DOKS.** The old DOKS + Terraform stack (redducklaw
  `infra/terraform`, `infra/k8s`) is overkill and was torn down. Use one Ubuntu
  Droplet (sfo3, about $12/mo) running Docker Compose:
  - `api`: the FastAPI backend (uvicorn)
  - `caddy`: automatic Let's Encrypt TLS; serves the built frontend `dist/` and
    proxies `/api/*` to `api:8000`
  - SQLite and downloaded files on a host volume
- **No app-code changes.** Everything lives in `deploy/` in this repo. The app
  runs as is; Caddy does static files + proxy.
- **Data:** ship a snapshot of `backend/data/` (SQLite + files), so the hosted
  demo serves the cached digest instantly and costs nothing per view. Optional
  live re-sync: Clio tokens in the server `.env`; scanned-page OCR falls back to
  RapidOCR on Linux (winocr is Windows-only), and unchanged documents are not
  re-OCR'd.
- **Access control:** Caddy basic auth on the whole site (case material is
  confidential even if synthetic). Exception: `/p/*` and `/api/share/*`, so a
  provider link works the way it would in real use. Credentials go to Aron
  only and into the submission form, never into git.
- **Secrets:** copy the needed keys from the main `.env` to the Droplet with
  `scp` (Anthropic, OpenAI, Cohere; Clio only if live sync is wanted). Never
  commit them, never echo them.

## Steps

Update: Aron wants deploys from GitHub Actions. `demo-provision.yml`
(manual, creates Droplet + `demo` record) and `demo-deploy.yml` (push to main
or manual) do the outward work; secrets come from GitHub secrets. Case data is
seeded from the laptop with `deploy/seed-data.sh` (repo is public). Runbook and
secret list: `deploy/README.md`.


- [x] Read `C:\Repos\redducklaw\docs\deployment-info.md` and
      `docs\retirement-and-restore.md` (read-only; never modify that repo)
- [x] `deploy/Dockerfile.api` (python:3.13-slim, uv, `uv sync`; winocr is
      Windows-only, so make it a platform-conditional dependency in a
      `contract:` commit to `backend/pyproject.toml`; RapidOCR stays)
- [x] `deploy/Caddyfile`, `deploy/docker-compose.yml`, `deploy/README.md` (runbook)
- [ ] Build the frontend locally (`npm run build`), ship `dist/` with the bundle
- [ ] **Ask Aron** before each outward action: create Droplet (cost), add DNS
      record, copy secrets, upload case data
- [ ] `doctl` (already installed) to create the Droplet and the `demo` A record
- [ ] rsync `deploy/`, `frontend/dist`, `backend/`, the `backend/data/` snapshot;
      `docker compose up -d`
- [ ] Verify: TLS, basic auth, brief loads, chip opens PDF with highlight,
      AI draft, share link works without auth
- [ ] Add the URL and credentials-handling note to `docs/submission.md`

## Session prompt

```
You own the DEPLOY stream: put the Law-di-gras Case Brief demo online at https://demo.redducklaw.com. Work in your own git worktree. Read CLAUDE.md, docs/plans/2026-10-02-deploy-demo.md (your plan, including the recommended decisions) and docs/status.md first.
Rules: Do not interrupt local work. Touch only deploy/ (new), docs/plans/2026-10-02-deploy-demo.md, and the deploy section of docs/submission.md; a winocr platform marker in backend/pyproject.toml is allowed as a small `contract:` commit. Never modify C:\Repos\redducklaw (read-only reference). Clio stays read-only (GET only). Secrets never go into git, logs or chat; copy them with scp. Do not touch the redducklaw.com apex/www records or the App Platform landing app; never touch MX/DKIM/verification records.
Before each outward-facing action (creating the Droplet, adding the DNS record, copying secrets or case data to the server), state exactly what you will do and the monthly cost, and wait for Aron's yes.
Land work with git pull --rebase origin main then git push origin HEAD:main; stage only your paths.
Done when: https://demo.redducklaw.com serves the brief over TLS behind basic auth, a source chip opens the highlighted PDF, an AI draft renders, and a provider share link (/p/...) works without the basic-auth prompt. Report the URL and how credentials were handed over (not the credentials themselves).
```
