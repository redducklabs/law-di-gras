# Project status

Maintained by the integration/manager session. Plan:
`docs/plans/2026-10-02-case-brief-dashboard.md`. Deadline 4:00 PM PT; feature
freeze 3:00 PM; video recorded 3:00–3:30; submit by 3:45.

## Now (updated 10:25 PT)

| Stream | State | Landed on main | Next |
|---|---|---|---|
| S1 Clio + ingestion | **Done**; archive session | 219 sources, 361 pages (10 OCR via Windows OCR), 567 chunks | none |
| S2 Retrieval + digest | Done core; working on follow-ups | Hybrid search, 64/64 facts verified, Opus brief, cached dashboard, /search, /ask | Meaningful "recent" items; timeline milestones; re-digest |
| S3 UI design | Built firm Case Brief + templated drafts | Tokens, components, Case Brief, Next steps drafts | Subtle timeline (now a 44-label wall), live data, provider restyle |
| S4 Provider + sharing | Done core | Providers (10 found), share settings, server-filtered provider view, SharePanel, ProviderPage | Done-check on Sapini, provider's own lien |
| S5 Source pane | To start (fresh worktree) | Stub + contract in `src/source/` | PDF highlight, text highlight, Find/Ask |
| Integration | App wired | Routes `/` and `/p/:token`, Share + source drawer | Watch streams, demo script |

## Demo path

- [x] Firm dashboard loads Sapini live (client header, stage stepper, timeline)
- [x] Headline + KPI tiles from live digest
- [x] Needs action / Next steps + last client contact
- [ ] Click date/injury → source pane highlighted (S5)
- [ ] Find in case (+ cited Q&A) UI (S5; API done)
- [x] Share panel → provider link (wired; done-check on Sapini pending)
- [ ] Provider page verified on Sapini data
- [x] Cost per case: ~$1.48 first digest, ~$0.13–0.50 re-digest

## Risks / watch list

- Timeline strip is cluttered on real data (44 events); S3 + S2 fixing.
- Re-sync by S1 code changes doc hashes → next digest rebuilds (2–5 min). Digest once before recording.
- App is Windows-only (winocr); fine for localhost demo, note for judges.

## Log

- 09:55 Contracts + skeleton pushed (3cb53f1). Four stream sessions started in worktrees.
- 10:25 All four streams landed core work. App wired and verified live on Sapini at :5175. Sent S2/S3/S4 follow-ups; S5 (source pane) queued.
