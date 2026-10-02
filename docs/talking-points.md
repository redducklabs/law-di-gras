# Pitch talking points (4 min total: ~75 s talk, 88 s video, ~75 s talk)

The video already shows: Cases list, case brief, a source chip opening the PDF, the coverage conflict, Blind spots, the audit badge, a Next-steps draft, one chat question, and the provider view. Use the talk time for what it **doesn't** show. Pick 4–6 bullets; don't read them all.

## Open (~20 s, before the video)

- A PI file is thousands of entries. Attorneys asked for "the 10 that matter out of 300", what changed, and what's stuck, at a glance. Providers on a lien have no visibility at all.
- Our bet is trust, not more widgets: nothing reaches the screen unless its quote is found verbatim in the Clio record.
- Sapini is pulled live from Clio (GET-only, never written back) and digested once into our own cache.
  - A production version would use Clio webhooks for live updates.

## Not in the video: go deeper here (~2 min)

**Timeline**
- Zoom and pan: double-click or pinch to zoom, drag to pan, "All 33 events" to reset.
- Medical, legal and deadline lanes, so a lawyer reads the case through time.
- Tense is honest: scheduled vs. occurred vs. adjourned vs. deadline, from each entry's own wording. A subpoenaed deposition with no record of happening reads "Scheduled … (no record it occurred)".
- Date conflicts are caught in code: the IME calendar dates conflict with the reports' NYSCEF filing stamps, so both show as conflicts instead of picking one.

**Find in case (search)**
- Hybrid retrieval: AI-generated likely questions per passage, embeddings, keyword search fused by rank, then a reranker.
- Results are cited passages that open the page with the passage highlighted, including scanned PDFs (OCR with line positions).
- "Ask the record" from the source pane gives a cited answer next to the document.

**Ask the case (chat)**
- Multi-turn, and answers only from retrieved record evidence plus the verified brief.
- Every citation is span-checked. Claims that something is absent are banned unless a search backs them.
- Links are validated on the server: they scroll to a brief section, jump to a timeline date, open a source page, or open sharing.
- Defense opinions stay attributed: "injuries" answers include the defense IMEs per body part, never as the client's findings.

**Drafts**
- Every Next step drafts a templated follow-up in one click; "Improve with AI" rewrites it from the record.
- Every date, amount and name is checked against the cited quotes; anything unverifiable becomes a visible `[verify: …]`, never a guess.

**Numbers you can defend**
- Specials, firm costs, liens, next steps and "waiting on" are computed in code from Clio entries, not by the model. The audit confirms they reconcile ($118,400 = 9 charges).
- Case value is a visible, configurable firm rule (1.5–3x specials), labeled as a draft.
- Statute of limitations follows the operative complaint: the action was recommenced under CPLR 205, and the dismissed prior suit is ignored.

**Blind spots, deeper**
- Runs in the background with a live progress bar; the previous review stays on screen while it runs.
- Rejects findings that overstate the record ("only", "never"), cite law not in a quoted passage, or are reconciled elsewhere in the same document.
- Each finding has a concrete next step for the team, cited.

**Built-in audit, deeper**
- Runs automatically on every new digest and review. Flags carry a severity and a plain-English note on the exact item.
- It caught real errors in our own output, e.g. "both vehicles southbound" is flagged because the record contradicts it.
- A separate audit stream gated each release; findings and fixes are logged in `docs/audit/`.

**Provider sharing, deeper**
- The attorney toggles per provider what they see (status, coverage, requests, bills, specific records) and previews it live before sharing.
- Filtering happens on the server; the audit confirms none of the 10 provider links leaks notes, strategy or another provider's data.
- "Updates since your last visit" for the provider, and "Opened by … on …" for the firm.
- Links work without a login, like a real provider would get.

**Cases page**
- Every matter sorted by what needs attention: overdue, waiting on others, next deadline, days since last client contact, specials, coverage, value.
- The 4 extra rows are labeled "Sample · not from Clio"; only Sapini is real.

**Under the hood**
- Ingestion: 31 documents and 361 pages, with OCR for scans, plus 42 notes, 69 communications, tasks, calendar entries and expenses.
- Incremental re-sync skips unchanged items by content hash.
- Cost: about $2.50 per case for the first digest, cents per refresh; drafts about $0.01, a chat answer about $0.13.
- Hosted at demo.redducklaw.com with its own read-only Clio grant, alongside the localhost build.
- Three visual skins (Pinstripe, Ledger, Classic); the look is design tokens, not a rebuild.

## Close (~10 s)

- "Every fact traceable. Draft, not decision. The attorney stays in control."
