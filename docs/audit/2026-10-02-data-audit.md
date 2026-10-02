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

## Re-run after S2 r12 (dashboard 18:53 UTC)

Checks 1, 2, 3, 5 and 6 ran on the re-digested dashboard and cost $0.63.

Result: **0 claims the record contradicts or does not contain**. The judge's 3
"critical" flags are false positives: it confirmed that firm costs and specials
sum correctly while still flagging them. Raw output is in
[auto-report.md](auto-report.md).

| # | Finding | Status |
|---|---|---|
| 1 | Case value rounding | **Resolved.** Shows $177,600 – $355,200, and the cap note is now conditional on Metro-North staying liable. |
| A | "No police report" in headline | **Resolved.** The claim is removed. |
| 2 | Bullet 0 liability claims | **Still open (re-cite).** The wording is now accurate, but the bullet still cites only pleadings. Cite note 2996972633. |
| 3 | Bullet 4 "McCulloch overdue" | **Resolved.** Now cites tasks 1417160243 and 1417160363. |
| 4 | Bullet 1 knee/spine/TBI dispute, 07/2023 repair | **Resolved.** Both claims are removed, and "no MMI declared" is cited. |
| 5 | Status line has no own citations | **Still open.** The new text, "in discovery against Metro-North; both sides are trying to schedule the client deposition", names only one of two defendants (Ferrara is also a defendant). The deposition claim is in note 2996972258 but is not cited. |
| 6, E | Defense IME findings in the injury list; carpal tunnel | **Resolved.** The Tsao cards are gone, and defense opinions are now labeled "Defense IME (Dr. Katzman)". |
| 7 | Left shoulder "repair 07/26/2023" | **Resolved.** Removed. |
| 8 | Recent activity used Clio filing dates | **Resolved.** The Tsao and Katzman reports are now dated 2026-03-24 and 2026-02-04. |
| 9 | "Client confirmed he will continue PT" | **Resolved.** Now reads "he was told yes… and he confirmed the right shoulder surgery still has no date", which matches the note. |
| 10 | SOL "deadline passed" | **Resolved.** Now reads "(suit filed 2024, satisfied)". Minor: cite the complaint for "suit filed". |
| 11 | Statement-of-damages deadline | **Resolved.** Removed. |
| 12 | IME dates conflict with the reports (Mar vs Sep 2026) | **Partly.** Now hedged as "Calendar: … IME", but the conflict with the reports' March 2026 dates is still not surfaced. |
| 13 | Compliance conference shown as occurred | **Resolved.** Now "Calendar: Compliance conference". |
| 14 | Hudson Valley "Treatment starts 2023-05-08" | **Still open.** The date is still not in the cited quote, which is a provider list from the bill of particulars. |
| 15 | Last visit reads as end of treatment | **Resolved (S3).** Firm and provider views now say "billed through". |
| 16 | Document header dates | **Resolved (S5).** The header now reads "Filed in Clio …". |
| Kinds | Medical calendar events typed `legal` | **Resolved.** Now typed `treatment`. |
| B | CSB email gives $100k/$300k, cited as Ferrara's | **Still open** (sent after r12 started). |
| C | UM listed as coverage | **Mostly resolved.** Bullet 2 now reads "client UM/UIM $25,000/$50,000" with no claim that it adds to recovery. |
| D | Specials shown as final | **Still open** (sent after r12). The KPI still says "billed" with no "running/unreconciled" label. |
| 17 | OCR on the photo ID | **Deferred** by the manager. |

**New findings in this pass:**

| Sev | On screen | What's wrong | Owner |
|---|---|---|---|
| major | Knee card: "MRI of both knees… Defense IME (Dr. Katzman): 'no recent traumatic injury or internal derangement.'" | Katzman's quote is his **left-knee** conclusion, attached to a bilateral card. Scope it ("left knee") or cite the right-knee conclusion too. | S2 |
| major | Status line "Litigation is in discovery against Metro-North" | It drops Ferrara, a named defendant (see #5). | S2 |
| minor | Several injury cards, and bullets 1, 2 and 3 | The record supports these claims, but a different source than the one cited is the primary one. Examples: knee MRI → doc 21121911503; specials → note 2996971223; no-fault → comm 5029430243. Exact cites are in auto-report.md, check 2b. | S2 |
| minor | Recent "notice dated March 24 / February 4" | These are NYSCEF filing dates; the notices carry no date of their own. Say "filed". | S2 |
| minor | Recent: "CSB sent Katzman review" (9/22) and "Defense counsel served Katzman report" (2/4) | The same report appears twice, from two transmittals. | S2 |

## Re-run after S2 r16 (dashboard 19:12 UTC)

Checks 1, 2, 3, 5 and 6 cost $0.70. Raw output is in [auto-report.md](auto-report.md).

The judge again flagged firm costs and the Montefiore bill as "critical" while
confirming both sums are correct, so those are false positives. The record check
flagged the surfaced coverage conflict as "contradicted", which is the intended
behavior, not an error. KPIs reconcile and provider views are clean.

| # | Finding | Status |
|---|---|---|
| B | CSB $100k/$300k vs Metro-North self-insured | **Surfaced** as "Conflict:" on the Metro-North coverage line, the case value and bullet 3, and the case value says "capped at $100,000 per person if those limits apply". **New problem:** see N1. |
| C | UM | **Resolved.** |
| D | Specials shown as final | **Resolved.** Now "running figure… ledgers unreconciled". |
| E | Carpal tunnel | **Resolved.** |
| 2 | Bullet 0 cites only pleadings | **Still open.** The new text adds "three versions of the collision on file", but its 4 citations are still the complaint and bill of particulars. None is note 2996972633 or note 2996970518, which say it. |
| 5 | Status line has no own citations | **Still open.** The text is now "Action is in discovery; both sides are trying to schedule the client deposition"; the Ferrara omission is resolved. Cite note 2996972258. |
| 12 | IME dates (Sep calendar vs Mar reports) | **Still open.** |
| 14 | Hudson Valley "Treatment starts 2023-05-08" | **Still open.** It still cites only the bill of particulars provider list. |
| knee | Katzman's left-knee quote on the bilateral card | **Still open.** |

**New in r16:**

| Sev | On screen | What's wrong | Owner |
|---|---|---|---|
| **major N1** | Coverage tile now has three lines with limits: "Metro-North… Conflict: self-insured vs $100k/$300k"; "**BI liability · Claims Service Bureau (Metro-North claim administrator) · defendant** · $100,000 / $300,000"; "Ferrara personal policy · $100,000 / $300,000" | **Wrong party.** CSB is Metro-North's claims administrator, not a defendant or an insurer. The same $100k/$300k now reads as a second policy, so a reader sees $200k/$600k of liability coverage. Drop the CSB line and keep the conflict on the Metro-North line only. | S2 |
| major N2 | Labels now carry note text and attribution. Injury: "Left shoulder posterior labral tear **— MRI also shows… glenoid hypoplasia, developmental not traumatic; defence expected to use it (Aron Weiler, 2023-07-12)**". Specials KPI label: "…running figure stands… least certain (Aron Weiler, 2026-09-25)" | The label sits next to the MRI finding, so a reader takes 2023-07-12 as the MRI date. The record check made exactly that mistake; the MRI was 05/24/2023. The text also makes long tile labels, and "developmental not traumatic" comes from the firm's note, not the MRI. Move caveats into the value or a note line, and keep labels short. | S2 (S3 for layout) |
| major N3 | Injury cards: "Defense IME (Dr. Katzman…)" | Katzman did a **radiology review**, not an IME (the Hostin and Tsao exams were the IMEs). Say "Defense radiology review (Dr. Katzman)". | S2 |
| minor N4 | Bullet 4 ends "…$50,000 no-fault exhausted. McCulloch records and surgical date." | A sentence fragment is left over from a merged bullet. | S2 |
| minor | "Treatment starts: New Horizon Surgical Center" | This was a one-day surgery, not the start of a course of treatment. | S2 |
| minor | SOL "(suit filed 2024, satisfied)" | Cites only the calendar entry; cite the complaint for "suit filed". | S2 |

## Re-run after S2 r20 (dashboard 19:26 UTC)

Dashboard checks 1, 2, 3, 5 and 6 cost $0.63, and the chat check cost $0.28.
Raw output is in [auto-report.md](auto-report.md) and
[auto-report-chat.md](auto-report-chat.md).

The judge's "critical" flags on firm costs and specials are false positives again
(it confirmed both sums). KPIs reconcile and provider views are clean.

| # | Finding | Status |
|---|---|---|
| chat critical | "No IME findings" / "evidence does not say what the defense disputes" | **Resolved.** The answer lists Katzman's per-side disputes with citations. One remaining gap is listed as C1 below. |
| chat coverage | Chat said "capped at $100k" while the tile said uncapped | **Resolved.** Chat now quotes the tile's conflict wording, and the follow-up says plainly that the record doesn't say whose limits they are. |
| N1 | CSB shown as a defendant | **Resolved**, but see R1. |
| N2 | Long labels with attribution | **Resolved.** Labels are short; caveats sit in "· Note: per firm note of <date>". |
| N3 / knee | Katzman shown as an IME; bilateral knee card | **Resolved.** Now "Defense radiology review", scoped per side, and the knees are split. |
| N4 | Bullet fragment | **Resolved.** |
| 14 | Hudson Valley start date | **Resolved.** Now cites the expense entry "2023-05-08 to 2023-08-08". |
| 2 | Bullet 0 cites only pleadings | **Still open.** |
| 5 | Status line has no own citations | **Still open.** The text now opens "The Presentation of Claim was served on Metro-North…". |
| 12 | IME dates Sep vs Mar | **Still open** (known). |

**New in r20:**

| Sev | On screen | What's wrong | Owner |
|---|---|---|---|
| **major R1** | The coverage tile has three lines (Metro-North conflict, no-fault, UM/UIM). **Ferrara's personal auto policy is gone**, and headline bullet 2 no longer mentions it. | This is a regression. Note 2996970398 ("Ferrara personally carries auto coverage identified at $100,000 / $300,000… if Metro-North comes out… that policy is the entire recovery") is still in the record. Removing the CSB line took the co-defendant's coverage with it. Restore "Ferrara personal auto · $100,000 / $300,000". | S2 |
| major R2 | Timeline "Statute of limitations: 2026-04-22 (suit filed 2024, **satisfied**)", which now cites the complaint's "on February 1, 2024, Plaintiff started a **prior** lawsuit" | That prior suit was **dismissed** for failure to serve a Presentation of Claim (same page of the complaint). This action was recommenced under CPLR 205 after the 9/10/2024 Presentation of Claim. Citing the dismissed suit as proof the SOL is "satisfied" is wrong on its face, and "satisfied" is a legal conclusion the record does not state. Suggest "Action recommenced under CPLR 205 (complaint p7); SOL 4/22/2026" with that cite. | S2 |
| major R3 | Headline bullet 2 "Coverage conflict: Metro-North self-insured vs $100,000/$300,000" | The $100k/$300k is not in any cited quote; the bullet cites only expense entries. Cite comm 5029429688 or 5029426433 and note 2996971778. | S2 |
| major C1 | Chat (injuries): "I couldn't find a defense dispute of the cervical, lumbar, thoracic or left shoulder findings in the retrieved record." | Hostin's orthopedic IME diagnoses the neck, back and other sprains as **resolved**, which disputes the spine claims. Tsao's neuro IME also calls the thoracic strain resolved. The hedge "in the retrieved record" keeps it from being a hard error, but the answer omits both IMEs. Add the Hostin and Tsao IME conclusions to injury evidence. | S2 |
| minor | UM/UIM note "sits under defendant's $100,000" | $100,000 is not in the cited quote. The note says it, but the cited span doesn't. | S2 |
| minor | Timeline "Calendar: Post-operative follow-up", "Calendar: Consultation re second surgery" | Hedged with "Calendar:", which is acceptable. The judge still reads them as occurred. | S2 |

## Check 7: ask-the-case chat (S2 /chat, 7 questions incl. 1 follow-up and 1 trick)

Run: `uv run python -m app.audit --checks 7 --suffix=-chat` ($0.23). Full Q&A
transcript: [auto-report-chat.md](auto-report-chat.md). Every citation span is
verbatim, every [n] marker is in range, and every deeplink is valid (sections,
sources, timeline dates, share targets).

| Sev | Question | Answer text | What's wrong | Owner |
|---|---|---|---|---|
| **critical** | "What are the client's injuries, and which ones does the defense dispute?" | "The evidence does not say which specific injuries the defense disputes." / "The evidence does not contain any IME findings." | False. The record has the Hostin ortho IME (sprains resolved), the Tsao neuro IME ("objectively resolved") and the Katzman radiology review ("no evidence…"), and the dashboard's own injury cards quote them. Retrieval missed the expert reports, so the answer reports their absence as fact. Fix: add the expert reports and the dashboard injury facts to chat evidence for injury questions, and stop "the evidence does not contain X" claims unless retrieval actually covered X. | S2 |
| major | same | "A left shoulder arthroscopy is on the calendar for 2023-07-26" | It was performed (New Horizon op record, bill). Saying "on the calendar" undersells the main surgery in the case. | S2 |
| major | "What insurance coverage is available…?" | "Practical read: Recovery is capped at $100,000 unless the case reaches a second defendant" [Weiler 9/9 note] | This contradicts the dashboard KPI ("no cap while Metro-North remains liable"). Chat and dashboard must not disagree on coverage in front of judges. This is the same B conflict; resolve it in one place. | S2 |
| minor | follow-up "Is the $100k/$300k Ferrara's or Metro-North's?" | starts "The same note says…" | Dangling reference with no antecedent in this answer. Otherwise good: it surfaces the conflict with both cites. | S2 |
| minor | "What is overdue…?" / Pullano | "scope-of-employment disclosure and Pullano deposition… remain an open action" | Presents a 2026-03-06 note's status as current. | S2 |

Done well: the trick question ("our summary judgment motion") correctly says there is none in the record and distinguishes the prior cross-motion dismissal. The Pullano answer is hedged correctly ("no record it happened"). Last client contact matches the record.

## Check 8: S7 Blind spots (cached review 19:37 UTC, 5 findings)

What I checked:
- All **27/27 citation quotes are verbatim** and on the cited page (span check).
- Each claim is read against its full source page: the Metro-North IR-1 and
  cover sheet (doc-40 pp3–4), notes, emails, and the Hostin and Tsao reports.
- The review is firm-only; nothing in `share/` references it, so providers never
  see this strategy content.

| Finding | Verdict | Why |
|---|---|---|
| bs1: IR-1 says Ferrara "was heading to the jobsite", On-Duty, while the 9/5/2026 email says the incident report was not produced | **KEEP** | Verified. IR-1 (doc-40 p3, filed on NYSCEF 09/30/2025) reads "Mr.Ferrara was heading to the jobsite", with On-Duty marked. Doc-40 p1 says "Annexed hereto is the Metro-North Railroad Incident Report". The firm's own 9/5/2026 email to CSB says "neither of which appears in your response". The finding is real and strong. Optional: note that the dispatch records may still genuinely be missing. |
| bs2: Travelers auto policy on Metro-North's cover sheet vs self-insured vs $100k/$300k | **KEEP (small fix)** | Verified. Metro-North's own Accident Report Cover Sheet (doc-40 p4) lists "Automobile Policy # HC2ECAP477M0330TCT19-Travelers Indemnity". The "Policy Limits Confirmed" flag (custom field = True) and the valuation note's "Recovery is capped… The defendant carries $100,000" both exist. **Fix:** cite them; they are claimed in why-it-matters but not in the citations. |
| bs3: No record of Pullano being deposed; EBT subpoena 12/8/2025 | **KEEP (fix wording)** | It is hedged correctly ("No record found…", "nothing on file showing it was held"), and the 3/6/2026 note (2996972423) lists the Pullano deposition as still outstanding, so add that cite. **Fix two overreaches:** (1) "the **only** non-party eyewitness": plaintiff's discovery response refers to witnesses "listed on the Police Accident Report", so say "a non-party eyewitness". (2) "raise non-compliance at the **upcoming compliance conference**": no compliance conference is scheduled. The only calendar entries are a past one (4/15/2025) and a 10/21 internal file review, so drop "upcoming" or say "request a compliance conference". |
| bs4: Police report conflict, plus "Metro-North's report places the crash on an Exit# 16 ramp" (location conflict) | **FIX: cut the location half** | The police-report half is verified: plaintiff's doc-08 says "Annexed is a copy of the Police Accident Report", Hostin lists one dated 4/23/2023, and the firm's 9/15 note says "There is no police accident report in the file". **The location conflict is overreach.** The **same** Metro-North document's cover sheet (doc-40 p4) gives "Accident Loc/Town/St: **Cedar St & Garden St, New Rochelle**", matching our bill of particulars, and the IR-1 says he was "getting off the Exit#16 in NewRochelle". The record doesn't show two different locations. The suggestion that "the defense will use it to impeach him" is not supported. Retitle it as the police-report conflict only. |
| bs5: Two mechanisms told to the two defense examiners; prior-injury denial vs 2011 ankle/foot X-rays; discovery response "Not applicable" | **KEEP** | Verified. Hostin p4: "his vehicle struck another vehicle as both were merging". Tsao p3: "sideswiped by a truck and struck the sidewalk" and "no reported… unrelated injuries". Tsao p4 records list "X-ray report of the left ankle, dated 10/5/11". Plaintiff's doc-08 p4 says "PRIOR AND/OR SUBSEQUENT INJURIES Not applicable". The next step (supplement the response, deposition prep) is sound practice. |

Net: **3 keep (bs1, bs5, bs2 with cites added), 2 fix (bs3 wording, bs4 cut the location claim).** None needs to be cut entirely. bs1 is the strongest demo moment.

## Status

- [x] Checks 1–6 run on the current cached dashboard.
- [x] Re-run after S2 r12; see delta above. Open: 2, 5, 12, 14, B, D + 2 new majors.
