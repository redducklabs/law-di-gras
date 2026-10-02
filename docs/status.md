# Project status

Maintained by the integration/manager session. Plan:
`docs/plans/2026-10-02-case-brief-dashboard.md`. Deadline 4:00 PM PT; feature
freeze 3:00 PM; video recorded 3:00–3:30; submit by 3:45.

## Now (updated 11:55 PT)

| Stream | State | Next |
|---|---|---|
| S1 Clio + ingestion | Done (archived) | none |
| S2 Retrieval + digest | KPIs fixed; waiting_on + case value deterministic; grounded /draft live | Cache version guard; draft segment spacing |
| S3 UI design | KPI row above fold; 5-label timeline; Improve-with-AI wired | Aron's timeline-zoom choice; polish |
| S4 Provider + sharing | Done: requests, lien, updates-since, attendance | Standby for fixes |
| S5 Source pane | Done: PDF/OCR rect highlights, text spans, Find, Ask | Standby; search passages highlight whole chunk |
| Integration | :8000/:5175 on latest main | Demo script, submission notes, freeze 3:00 |

## Demo path

- [x] Firm dashboard loads Sapini live (client header, stage stepper, timeline)
- [x] KPI row above fold: specials $118,400 (9 providers), coverage, firm costs $1,410, draft value $180k–$355k (rule shown)
- [x] Next steps + waiting on others + last client contact + recent activity
- [x] Click date/injury → source pane, quote highlighted on the PDF page
- [x] Find in case + cited Q&A
- [x] Next step → template draft → Improve with AI (verified, cited)
- [x] Share panel → provider link; provider page (status, coverage, requests, visits/bills, updates since)
- [x] Cost per case: ~$1.50 first digest; ~$0.07–0.23 refresh; ~$0.01 per AI draft

## Risks / watch list

- Stale backends can overwrite the shared dashboard cache; restart after every pull (S2 adding version guard). Re-digest once before recording.
- App is Windows-only (winocr); fine for localhost demo, note for judges.

## Log

- 09:55 Contracts + skeleton pushed (3cb53f1). Four stream sessions started in worktrees.
- 10:25 All four streams landed core work. App wired and verified live on Sapini at :5175. Sent S2/S3/S4 follow-ups; S5 (source pane) queued.
- 10:55 Full review on live Sapini: timeline, recent activity, provider restyle good. Found KPI misclassification, KPI placement, provider-request gap; dispatched to S2/S3/S4. AI drafts (grounded, verified) approved: S2 route + S3 UI after fixes. S5 building source pane.
- 11:55 Every demo-path step works on live Sapini. Fixed: KPI misclassification, provider requests, deterministic waiting_on and case value, HTML entities (re-synced). Stale-server cache overwrite incident handled.
