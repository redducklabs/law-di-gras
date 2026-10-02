# Auto audit report: 00001-Sapini

Generated 2026-10-02T12:11 by `uv run python -m app.audit` (checks 7). Dashboard cached 2026-10-02 19:07:06, generated_at 2026-10-02T19:07:06+00:00. Audit LLM cost $0.23.

**Findings:** 4 critical, 0 major, 5 minor. Items audited: 89.

Severity: critical = wrong number/date/party/tense on screen; major = unsupported or misleading; minor = cosmetic.

## Check 7. Ask-the-case chat

| Sev | Item | On screen | Cited quote | What's wrong | Owner |
|---|---|---|---|---|---|
| critical | chat: What are the client's injuries, and which ones does t… | A left shoulder arthroscopy is on the calendar for 2023-07-26 at New Horizon Surgical Center [4]. |  | tense_wrong: The surgery date 2023-07-26 is long past, and the operative report shows the arthroscopy was performed. It is not upcoming. | S2 |
| critical | chat: What are the client's injuries, and which ones does t… | The evidence does not say which specific injuries the defense disputes. |  | contradicted: The record does identify disputed matters: the answer's affirmative defenses, the serious injury objection, and the IME reports finding all sprains resolved and no traumatic brain injury evidence. The claim that the evidence is silent is wrong. | S2 |
| critical | chat: What are the client's injuries, and which ones does t… | Orthopedic and neurological IMEs are on the calendar for 2026-09-02 and 2026-09-07 [7][8]. |  | tense_wrong: The calendar entries show the IMEs scheduled for 9/2 and 9/7, but both are past as of 2026-10-02, and the notes and task show they were attended. The sentence frames them as upcoming. | S2 |
| critical | chat: What are the client's injuries, and which ones does t… | The evidence does not contain any IME findings. |  | contradicted: The record contains the Hostin and Tsao IME reports with findings, e.g. diagnoses of resolved sprains and normal brain MRI. | S2 |
| minor | chat: And is the $100k/$300k Ferrara's policy or Metro-Nort… | Claims Service Bureau, which administers Metro-North's claims, wrote on 2026-09-08 confirming "the coverage position on this file": bodily injury liability limits of $100,000 per person and $300,000 per occurrence, with no excess or umbrella coverage disclosed. [1][2] |  | partly: The 2026-09-08 email confirms the limits and no excess or umbrella coverage. However, cited note [1] does not support the claim that CSB administers Metro-North's claims for this sentence's quote context—actually it does say claims are administered by CSB. The 'on this file' quote is accurate. Minor issue: the email doesn't tie the limits to Metro-North, but the sentence doesn't claim that. | S2 |
| minor | chat: And is the $100k/$300k Ferrara's policy or Metro-Nort… | The file itself flags this as a conflict: self-insured with no stated limit versus $100,000 / $300,000 per Claims Service Bureau. [3] |  | partly: The file shows both positions: the 2023 notes say self-insured with no stated ceiling, and CSB's 2026 email gives $100k/$300k. But no passage flags this as a conflict; the 'file itself flags' framing is the author's inference. Also the note says Ferrara personally carries $100k/$300k. | S2 |
| minor | chat: Did the Pullano deposition happen? | The timeline lists the Pullano deposition as *scheduled* for 2025-12-08, with no record it occurred. [2] |  | partly: The subpoena supports the Dec 8, 2025 date. The reference to 'the timeline' is not shown in the passages. 'No record it occurred' is consistent with the file and the March 2026 note, which lists the deposition as outstanding. | S2 |
| minor | chat: Did the Pullano deposition happen? | The Metro-North scope-of-employment disclosure and the Pullano deposition remain an open action, status waiting, on Defendants (Metro-North). [3] |  | partly: The 2026-03-06 note lists both items as outstanding on the defense side. 'Remain... status waiting' presents a March 2026 status as current; later notes do not confirm it. The 'action, status waiting' wording is not in the source. | S2 |
| minor | chat: What are the client's injuries, and which ones does t… | Liability is contested, and comparative negligence, assumption of risk and a seatbelt defence are to be anticipated. [5] |  | partly: Liability contested and anticipated defenses are supported by the 9/15/2026 note. But the defenses are already pleaded in the answer and bill of particulars, so 'to be anticipated' understates their status. | S2 |

**Q:** What is overdue right now, and what are we waiting on from other people?

> **Overdue right now**
> 
> - **McCulloch Orthopaedic: updated records and right shoulder surgical date**: due 2026-08-25, overdue, waiting on McCulloch Orthopaedic Surgical Services, PLLC [1]. Our 2026-08-03 email was the third written request for a surgical date [2].
> - **Updated employment and commission records from client**: due 2026-09-26, overdue [3]. We asked Justin on 2026-09-21 for commission statements after 2022 and Northwestern Mutual confirmation of pre-accident production [4].
> 
> **Waiting on others (not yet overdue or no due date)**
> 
> - **Justin Sapini**: commission statements after 2022 and Northwestern Mutual confirmation of pre-accident production [5]. A client appointment on these records is scheduled for 2026-10-29 [6].
> - **Advanced Rockland Chiropractic**: current daily notes and itemised bill to date, due 2026-10-07 [7]. Our 2026-09-26 request asked for an itemised ledger with CPT codes [8].
> - **SportsCare Physical Therapy**: ongoing treatment notes, due 2026-10-14 [9].
> - **Montefiore Nyack Hospital**: confirmation whether further records or charges exist beyond the 24 April 2023 attendance (no due date stated) [10].
> - **Claims Service Bureau (Metro-North)**: incident report and vehicle assignment/dispatch records for the morning of the collision (no due date stated) [11].
> - **Defendants (Metro-North)**: scope-of-employment disclosure and Pullano deposition (no due date stated) [12]. The Pullano deposition was scheduled for 2025-12-08, with no record it occurred [13].

Citations 13; links: Next steps, Share panel: McCulloch Orthopaedic, Commission records request email

**Q:** What insurance coverage is available and what are the limits?

> **Coverage on file — there is an unresolved conflict about whose policy the stated bodily injury limits belong to.** [1][2]
> 
> **Defendants**
> - **Metro-North Commuter Railroad:** Self-insured; no carrier and no declarations page. [3] Claims are administered by Claims Service Bureau, c/o D&D Associates, Garden City, claim SIR068120. [3]
> - **Ferrara (personal auto policy):** $100,000 / $300,000. [3][4]
> - The 2023-05-14 note says Metro-North is self-insured and that the $100,000 / $300,000 belongs to Ferrara's personal policy, not Metro-North. [2] Weiler's 2026-09-09 note treats the adjuster email as written confirmation of defendant liability limits of $100,000 / $300,000. [5] Defendants' discovery response said insurance information would be provided under separate cover. [6]
> 
> **Client's own coverage**
> - **UM/UIM:** $25,000 / $50,000, below the defendant's limits, so it adds nothing. [5][7]
> - **No-fault (Progressive, claim 22-4471102):** $50,000, exhausted. [8]
> 
> **Practical read:** Recovery is capped at $100,000 unless the case reaches a second defendant, and the Medicaid lien of $22,180.00 comes off any recovery. [5]

Citations 8; links: Self-insured coverage note, Coverage confirmed note

**Q:** And is the $100k/$300k Ferrara's policy or Metro-North's?

> - The same note says Ferrara personally carries auto coverage identified at $100,000 / $300,000. [1]
> - Claims Service Bureau, which administers Metro-North's claims, wrote on 2026-09-08 confirming "the coverage position on this file": bodily injury liability limits of $100,000 per person and $300,000 per occurrence, with no excess or umbrella coverage disclosed. [1][2]
> - That email does not say whose policy or program those limits belong to. [2]
> - The file itself flags this as a conflict: self-insured with no stated limit versus $100,000 / $300,000 per Claims Service Bureau. [3]
> - Defendants' discovery response said insurance coverage information would be provided under separate cover. [4]
> 
> The coverage note says that if Metro-North comes out of the case on scope of employment, Ferrara's policy is the entire recovery. [1] The note also says no statement of exposure has been requested from the authority. [1]

Citations 4; links: Coverage note (self-insured), Claims Service Bureau coverage email, Coverage conflict entry

**Q:** What are the client's injuries, and which ones does the defense dispute?

> **Injuries claimed**
> 
> - Case summary: both shoulders, both knees, and a head injury [1].
> - At intake: cervical and lumbar spine, both shoulders, both knees [2]. CT head and cervical at Montefiore Nyack ER were both negative [2].
> - The bill of particulars also lists lumbar spine myofascial derangement, an L5-S1 disc bulge narrowing the lateral recesses and inferior foramina bilaterally, restricted range of motion of the back, low back pain radiating to the lower extremities, and thoracic spine myofascial derangement [3].
> - A left shoulder arthroscopy is on the calendar for 2023-07-26 at New Horizon Surgical Center [4].
> 
> **What the defense disputes**
> 
> The evidence does not say which specific injuries the defense disputes. The firm's own notes flag these exposures:
> 
> - Liability is contested, and comparative negligence, assumption of risk and a seatbelt defence are to be anticipated. [5]
> - The client denied prior injuries at intake. [2] His records include 2011 left ankle and left foot X-rays showing a small dorsal avulsion fracture of the anterior talus [6]. He has also complained of left ankle pain from this accident, but no left ankle injury is claimed [6][5].
> - The left shoulder MRI that supported the surgery also reports hypoplasia of the posterior inferior glenoid, a developmental variant. [5]
> - Orthopedic and neurological IMEs are on the calendar for 2026-09-02 and 2026-09-07 [7][8]. The evidence does not contain any IME findings.

Citations 8; links: Injuries, Case posture note, Prior ankle discrepancy

**Q:** When did we last talk to the client, and what did we discuss?

> The last client contact was a phone call on **2026-09-27**, when Justin called about his treatment status [1][2].
> 
> What was discussed:
> - He asked whether he should keep attending physical therapy while the case is pending; he was advised yes, to keep going and to keep his own record of every visit [1].
> - He confirmed the right shoulder surgery still has no date [1].
> - He said he is otherwise fine and will send updated employment records "soon" [1].
> 
> For context, in the prior call he asked again when the right shoulder will be done, and was told the surgeon wants to see him first and that we have asked five times; he was still going to physical therapy twice a week [3].
> 
> The next client contact is a follow-up call scheduled for 2026-10-14 to check whether the right shoulder surgery has been scheduled and to chase employment records [4].

Citations 4; links: Client call 2026-09-27, Scheduled follow-up call 2026-10-14, Recent activity

**Q:** Did the Pullano deposition happen?

> **No — there is no record that it happened.**
> 
> - Plaintiff's subpoena ad testificandum, dated November 2, 2025, commanded Kyle Pullano to appear for a virtual Examination Before Trial on December 8, 2025, at 10:00 a.m. [1]
> - The timeline lists the Pullano deposition as *scheduled* for 2025-12-08, with no record it occurred. [2]
> - The Metro-North scope-of-employment disclosure and the Pullano deposition remain an open action, status waiting, on Defendants (Metro-North). [3]
> - As of the 2026-09-15 case-posture note, Pullano had been identified as the person who can answer the scope-of-employment question, but nobody had contacted him. [4]
> 
> Why it matters: Pullano was a passenger in the defendants' vehicle [5], and whether Ferrara was on duty or on a break determines whether vicarious liability holds against Metro-North. [4][6]

Citations 6; links: Pullano subpoena (Dec 8, 2025 EBT), Open action: scope disclosure & Pullano deposition, Timeline: scheduled Pullano deposition

**Q:** What did the court rule on our summary judgment motion?

> The evidence provided does not contain any summary judgment motion or a ruling on one.
> 
> The record does reference a Decision and Order (Tsai, J.) in which the Court denied a cross motion and dismissed the Complaint, noting Plaintiff's failure to provide the Presentation of Claim before starting suit [1]. After that dismissal, Plaintiff served another Presentation of Claim by overnight mail dated September 10, 2024, and started this suit pursuant to CPLR 205 after waiting 30 days [1]. That ruling concerned a cross motion. [1]
> 
> If a summary judgment motion was filed, it is not reflected in the materials available to me.

Citations 1; links: Complaint (references prior Decision & Order), Case status, Case timeline

