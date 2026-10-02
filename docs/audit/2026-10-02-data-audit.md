# Sapini data audit (S6), 2026-10-02

Audited the cached dashboard for `00001-Sapini` (generated 18:15 UTC) with
`cd backend; uv run python -m app.audit --ocr`. That run audits 103 on-screen
items, re-checks every citation span, compares each source with Clio (GET only),
renders all 10 provider views in process (no share view is logged), and
vision-transcribes the 10 OCR pages. The audit costs about $0.41 per run, and the
total so far is $1.21.

The full machine output, including minor findings and the per-provider and
per-document tables, is in [auto-report.md](auto-report.md). Below is the curated
list with false positives removed. The judge's severities vary between runs: for
example, it flagged McCulloch's $9,530 as critical while confirming the line items
sum to $9,530. Severities below are mine.

Severity: **critical** means a wrong number, date, party or tense on screen.
**Major** means unsupported or misleading. **Minor** means cosmetic.

## What is clean

- **Every citation span is verbatim.** All quotes on screen are found in the
  cited source and page, with 0 span failures.
- **Ingestion matches Clio exactly.** Counts are notes 42, communications 69,
  tasks 14, calendar entries 17, expenses 14 and documents 31. Every stored text
  and date equals Clio's current record, and no HTML entities are left in the
  text.
- **Specials reconcile.** $118,400 equals the sum of the 9 medical-charge
  entries, and each provider's billed figure equals its Clio entry. Each Clio
  entry also equals the total line on that provider's itemized bill PDF.
- **Firm costs reconcile.** $1,410 equals the 5 non-medical entries.
- **Coverage and lien figures are in their quotes:** $100k/$300k, $25k/$50k,
  no-fault $50k and Medicaid $22,180.
- **Provider views are clean.** No notes, emails or other providers' data appear
  in any of the 10 views, even with every section switched on.

## Check 1–2: fact support and headline

| Sev | On screen | Cited quote | What's wrong | Owner |
|---|---|---|---|---|
| major | Headline bullet "Liability contested… Client gave three inconsistent accounts, there is no police report, and the sideswipe carries no fault presumption." | "negligently merging"; "Ferrara was in the course of his" (pleadings) | None of the three specific claims (three accounts, no police report, no presumption) is in any cited quote. This is the most judge-visible unsupported line. Cite the notes that say it, or drop it. | S2 |
| major | Headline bullet "Urgent: McCulloch records and right shoulder surgery date are overdue (due 08/25). Defense wants the deposition after this surgery." | "Both sides are trying to schedule the client deposition" | The 08/25 McCulloch task is not cited, and no quote says defense wants the deposition after the surgery. | S2 |
| major | Headline bullet "…Spine, knee, and TBI claims are disputed by defense IMEs." / "Left shoulder labral repair done 07/2023" | Tsao "objectively resolved"; MRI labral tear | Nothing cited shows a knee or spine dispute; only neuro (Tsao) is cited. The 07/2023 repair date is not in any cited quote. | S2 |
| major | Headline bullet "$118,400 billed specials against Metro-North…" | "$3,475.00", "$1,450.00" | Only 2 of the 9 charge entries are cited, so the total cannot be traced from this bullet. Cite the KPI's 9 entries. | S2 |
| major | Status line "In litigation and discovery… Next: lock down the right shoulder arthroscopy date, which is holding up the client's deposition." | (none) | The status line has no citations of its own. The judge also notes the 2025-10-24 note says Capiola won't schedule until the client stops deferring, so the framing omits the cause. | S2 |
| major | Injury "Left shoulder… arthroscopic repair performed 07/26/2023 (post-op dx …)" (date 2023-05-24) | MRI labral tear; BoP "LEFT SHOULDER SIGNIFICANT POSTERIOR LABRAL TEAR" | The repair and its 07/26/2023 date are not in either quote. The op note or the calendar entry should be cited. | S2 |
| major | Injury "Traumatic brain injury… disputed by defense radiologist and IME as objectively resolved/no traumatic injury" | Tsao "Brain Injury, objectively resolved" | Tsao says *status post* TBI, objectively resolved, which concedes a past injury. "No traumatic injury" misstates it, and no defense-radiologist quote is cited. | S2 |
| major | Injuries "Post-concussion syndrome…", "Bilateral wrist injury with carpal tunnel syndrome", "Thoracic strain" (date 2026-03-04) | Tsao IME p6 "…objectively resolved", "incidental bilateral carpal tunnel" | These are **defense IME findings shown in the client's injury list** (wrong party). Carpal tunnel is called *incidental*, meaning not accident-related. "Positive Tinel's, bilateral ulnar tingling" is not in the quote, and the 2026-03-04 date is not in the quote. | S2 |
| major | Recent "Defense exchanged radiology expert report from Dr. Katzman" (2026-09-22); "Defense exchanged… Dr. Tsao" (2026-09-20) | "the report of Dr. Marc J. Katzman, dated December 8, 2025…" | Recent activity uses the **Clio filing date** as the event date. The excerpts show NYSCEF receipt on 02/04/2026 and 03/24/2026, so seven-month-old exchanges are presented as last week. | S2 (S4 for the date source) |
| major | Recent "Client confirmed he will continue physical therapy attendance… he is attending PT and will maintain records" | "Advised yes, keep going, and to keep his own record of every visit" | The client asked and was advised; he did not confirm. This misattributes the statement to the client. | S2 |
| major | Treatment McCulloch "last visit 2024-05-27, visits 8" | bill lines | 2024-05-27 is a treatment-planning consult, and the 8 visits include a $0 bundled post-op line. Minor in substance. | S2 |
| major | Treatment SportsCare "last visit 2023-12-14", Advanced Rockland "last visit 2024-08-15" | "This is the latest physical therapy date" (2023 records) | This is misleading next to ongoing treatment. The calendar shows PT on 10/10 and 10/17/2026 and chiro on 10/09/2026, and the 2025-04 note says "still treating". The line reads as if treatment ended in 2023 or 2024. Label it "last billed" or show "ongoing". | S2 |
| minor | Recent "attorney explained surgeon requires initial consultation" | "the surgeon wants to see him first" | "Initial" is wrong; Capiola has treated him since 2023. | S2 |

## Check 2b: headline, injury and recent claims vs the whole record

How this check works:
- Sonnet splits each item into atomic claims; there were 40 claims across the
  headline, injuries and recent activity.
- Each claim is retrieved against the whole case file with the app's own hybrid
  search, plus the item's own cited spans.
- Sonnet then judges each claim. This tells S2 whether to **re-cite** a claim
  (the record supports it) or **drop** it (the record does not support it, or
  contradicts it).
- The per-claim table is in [auto-report-2b.md](auto-report-2b.md).

| Sev | On screen | Record evidence | What's wrong | Owner |
|---|---|---|---|---|
| **critical** | Headline bullet 0: "there is no police report" | Plaintiff's own discovery response (doc-08): "Annexed is a copy of the Police Accident Report". Tsao IME records list: "Police accident report dated 4/23/23" | The record **contradicts** the claim. The source is the firm's 2026-09-15 note "There is no police accident report in the file", but the file's own discovery response says one was annexed. Do not state it as fact; show it as a conflict, or drop it. | S2 |
| major | Coverage: Metro-North "Self-insured; no stated limit"; case value "not capped"; Ferrara "$100,000 / $300,000" cites the 2026-09-08 email | communication 5029426433, **from Claims Service Bureau** (Metro-North's administrator, claim SIR068120): "The bodily injury liability limits are $100,000 per person and $300,000 per occurrence. No excess or umbrella coverage is disclosed." | Metro-North's own claims administrator confirms $100k/$300k on this file. The dashboard silently attributes that email to Ferrara and still says Metro-North is uncapped. This is a record conflict that bears on the "not capped" case-value note; surface it rather than resolve it silently. | S2 |
| major | Headline bullet 2: "$25k UM" listed as available coverage | note 2996972483: "The client's own UM/UIM is $25,000 / $50,000, below the defendant's limits, so it does not add anything here." | It is shown as a recovery source; the firm's note says it adds nothing. | S2 |
| major | Specials KPI "$118,400.00 billed" shown as a settled figure | note 2996972063: "The running figure of $118,400.00 stands… [chiro and PT ledgers] never been reconciled". The judge also cites a 2025-12-08 note saying not to quote it as final | It should be labeled "running / unreconciled" (the recent-activity item already says so). | S2 |
| major | Injury "Bilateral wrist injury with carpal tunnel syndrome… positive Tinel's" | Hostin ortho IME: "Tinel's sign at the carpal tunnel [is] negative", diagnosis wrist sprain, resolved | The two defense IMEs conflict, and the screen shows one as the diagnosis. Combined with the wrong-party issue (item 6 above), this item should be removed from the client's injury list or marked as disputed defense findings. | S2 |
| fix-cite | Headline bullet 0: "three inconsistent accounts", "liability contested on mechanism and scope", "sideswipe carries no presumption" | note 2996972633 (Case posture, 2026-09-15) states each verbatim | These are **supported, just not cited**. Cite note 2996972633 (and 2996970518 "three different accounts"). This downgrades finding 2 above from unsupported to mis-cited. | S2 |
| fix-cite | Bullet 4: "McCulloch… overdue (due 08/25)"; bullet 1: "repair done 07/2023" | task 1417160243; New Horizon op record doc 21121916438 | These are supported; cite these sources. | S2 |
| minor | Status line "…holding up the client's deposition" | note: surgery is "the single item holding the case where it is" | The record supports "holding up the case", not specifically the deposition. | S2 |
| info | Case value draft $180k–$355k | note 2996971448 "Case evaluation… Valuation: $375,000" (2026-06-04) | The firm's own valuation note is above the rule's top end. This is not an error, but an attorney may ask; consider showing it next to the rule. | S2 |

## Check 3: KPI reconciliation

| Sev | On screen | Cited quote | What's wrong | Owner |
|---|---|---|---|---|
| **critical** | Case value "$180,000 – $355,000"; label "Firm rule: 1.5x–3x billed specials ($118,400)" | n/a | 1.5 × 118,400 = **$177,600**, and 3 × 118,400 = **$355,200**. The low end is rounded **up** by $2,400 and the high end **down** by $200, with the rounding undisclosed. An attorney doing the math on stage sees a wrong number. Show the exact figures, or round both ends consistently and say so. | S2 |
| major | Case value "not capped: Liability self-insured; no stated limit" | Ferrara $100k/$300k note | The note says that if Metro-North exits (scope of employment is contested), Ferrara's $100k/$300k is the whole recovery. "Not capped" hides that risk. | S2 |

## Check 4: ingestion and documents

| Sev | On screen | Cited quote | What's wrong | Owner |
|---|---|---|---|---|
| major | Source pane header date for 8 pleadings and discovery docs, e.g. subpoena "Jan 2, 2025" (text says EBT on Dec 8, 2025, dated Nov 2025), complaint "Mar 8, 2024" (page 1 dates Oct 2024), letter to judge "Sep 24, 2024" (letter dated Apr 16, 2025) | n/a | The header shows Clio's `received_at`, which for these docs is **earlier than the document's own date**. It reads as impossible ("letter on Sep 24, 2024 describing a Jan 2025 filing"). It also feeds "Recent" with wrong dates (see above). Label it "Filed in Clio", or extract the document date. Full table is in auto-report.md. | S4 (label: S3) |
| major | OCR p1 of `01-intake…photo-id.pdf` | n/a | Word error is about 69%. The ID card is mostly unreadable to search. Low demo impact. | S4 |
| minor | OCR complaint pp1–8, letter to judge | n/a | Word error is 2–11%. The NYSCEF stamp date "10/11/2024" and some numbers (5102/5104, a phone number) are garbled on every page. Body text is fine. | S4 |

## Check 5: timeline semantics

| Sev | On screen | Cited quote | What's wrong | Owner |
|---|---|---|---|---|
| major | "2026-04-22 Statute of limitations (deadline passed)" (major milestone) | "Three-year statute of limitations expires" | Suit was commenced in 2024 (index 160000/2024), so "deadline passed" reads as a **blown SOL** in front of trial attorneys. Show "SOL 4/22/2026, satisfied: action commenced 2024", or drop "passed". | S2 |
| major | "2024-12-02 Response to demand for statement of damages due (deadline passed)" | "within fifteen (15) days of the date hereof" | 12/02/2024 is the demand's own date, and the due date is about 12/17/2024. Nothing shows a response was missed. | S2 |
| major | "2026-09-02 Orthopedic IME attended", "2026-09-07 Neurological IME, Dr. Tsao" | task / calendar entry | These conflict with the record. Hostin's report says the examination took place **March 31, 2026**, and Tsao's report is dated **March 4, 2026**. Clio dates them September. The dashboard shows the September dates without flagging the conflict. The injury cards date the same findings 2026-03-04. | S2 |
| major | "2025-04-15 Compliance conference" (major, past) | calendar entry only | A calendar entry is not evidence the conference happened. The 4/16/2025 letter to the judge says no PC date had been received. Hedge it like the deposition items. | S2 |
| major | "2023-05-08 Treatment starts: Hudson Valley Radiology…" | BoP provider list | The date is not in the quote or nearby. Cite the radiology record or bill instead. | S2 |
| minor | "Left shoulder arthroscopy", "Pre-operative consultation", "Post-operative follow-up", "Consultation re second surgery" | calendar entries | These are typed `legal`, not `treatment` (wrong color and filter). Past calendar entries are shown as occurred with no hedge. | S2 |
| minor | Future "Client treatment: PT/chiro", "File review…", "Client appointment…" | calendar entries | Appointments and internal reminders are typed `deadline`. | S2 |
| minor | Actions: "Confirm date of right shoulder arthroscopy with Dr. Capiola's office" and "Call to McCulloch Orthopaedic re right shoulder surgical date" (both 10/10); "Obtain updated employment… records" (overdue) and "Commission statements after 2022…" (waiting) | n/a | These are the same asks listed twice. | S2 |

## Check 6: provider views

| Sev | On screen | Cited quote | What's wrong | Owner |
|---|---|---|---|---|
| minor | All 10 provider links: "Updates" shows "Neurological IME, Dr. Jack W. Tsao" and "Orthopedic IME attended" | n/a | Defense IMEs are litigation detail, shown to treating providers who did not opt in to the timeline (they come through `updates`). The timeline toggle is off for every saved link. | S4 |

Deeper per-provider checks on each saved link found no problems:
- every treatment line belongs to that provider, and its billed figure equals
  that provider's own Clio charges;
- every request is owed by that provider;
- no other party's lien is shown;
- no strategy wording appears in the status line;
- every provider with Clio charges sees their billing line.

David Capiola sees no lines because he bills under McCulloch (minor).

Saved links: 10 providers, 0 leaked citations, 0 cross-provider names, and no
strategy terms (case value, settlement, liability, deposition) in any saved view.

## Status

- [x] Checks 1–6 run on the current cached dashboard.
- [ ] Re-run after S2/S4 fixes land and mark each row resolved.
