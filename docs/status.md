# Project status

Maintained by the integration/manager session. Plan:
`docs/plans/2026-10-02-case-brief-dashboard.md`. Deadline 4:00 PM PT; feature
freeze 3:00 PM; video recorded 3:00–3:30; submit by 3:45.

## Now (updated 09:55 PT)

| Stream | Session | State | Landed on main | Next milestone |
|---|---|---|---|---|
| S1 Clio + ingestion | Stream S1 | Writing client/login | none yet | `POST /sync` fills sources |
| S2 Retrieval + digest | Stream S2 | Writing embed/spans | none yet | embeddings + search over S1 data |
| S3 UI design | Stream S3 UI design | Drafting visual directions on fixture | none yet | Aron picks a direction |
| S4 Provider + sharing | Stream S4 | Writing providers | none yet | share settings + provider API |
| Integration | this session | Contracts pushed | contracts | SourcePane, wire routes |

## Demo path

- [ ] Firm dashboard loads Sapini (timeline strip, client header)
- [ ] Headline + KPI tiles from live digest
- [ ] Needs action + last client contact
- [ ] Click date/injury → source pane highlighted
- [ ] Find in case (+ cited Q&A)
- [ ] Share panel → provider link
- [ ] Provider page
- [ ] Cost per case number for submission

## Risks / watch list

- Nothing landed on main yet; streams should push small commits early.
- S2 depends on S1 data; S2 should develop on whatever S1 has synced.

## Log

- 09:55 Contracts + skeleton pushed (3cb53f1). Four stream sessions started in worktrees.
