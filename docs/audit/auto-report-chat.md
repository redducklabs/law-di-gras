# Auto audit report: 00001-Sapini

Generated 2026-10-02T13:13 by `uv run python -m app.audit` (checks 7). Dashboard cached 2026-10-02 20:08:05, generated_at 2026-10-02T20:08:05+00:00. Audit LLM cost $0.56.

**Findings:** 1 critical, 0 major, 7 minor. Items audited: 88.

Severity: critical = wrong number/date/party/tense on screen; major = unsupported or misleading; minor = cosmetic.

## Check 7. Ask-the-case chat

| Sev | Item | On screen | Cited quote | What's wrong | Owner |
|---|---|---|---|---|---|
| critical | chat: And is the $100k/$300k Ferrara's policy or Metro-Nort… | The defendants' discovery response stated insurance coverage information was to be provided under separate cover [5]. |  | tense_wrong: The response says insurance coverage information is 'to be provided under separate cover', which is a promise of future production. The sentence's past-tense 'was to be provided' is a reasonable restatement, but the later email suggests coverage was subsequently confirmed, so this is not a present-tense assertion. The wording fits the response but is misleading as a statement of current status. | S2 |
| minor | chat: What are the client's injuries, and which ones does t… | Right shoulder: the defense radiology review by Marc J. |  | partly: Sentence is a fragment introducing the Katzman right shoulder review. The review is in the record, but the sentence completes only in the next sentence. | S2 |
| minor | chat: What are the client's injuries, and which ones does t… | Left knee: the defense radiology review by Marc J. |  | partly: Fragment introducing Katzman's left knee review. The review exists, but the sentence is incomplete. | S2 |
| minor | chat: What are the client's injuries, and which ones does t… | Right knee: the defense radiology review by Marc J. |  | partly: Fragment introducing Katzman's right knee review. The review exists, but the sentence is incomplete. | S2 |
| minor | chat: What are the client's injuries, and which ones does t… | Brain: the defense radiology review by Marc J. |  | partly: Fragment introducing Katzman's brain review. The review exists, but the sentence is incomplete. | S2 |
| minor | chat: What did the court rule on our summary judgment motio… | The demand history and current damages update states that the action is now in discovery and both sides are trying to schedule the client deposition [2]. |  | partly: The cited 2026-08-03 note supports that the action is now in discovery. It does not say both sides are trying to schedule the client deposition. That comes from a separate 2025-08-27 note, so presenting it as the current status in the damages update is inaccurate and may be stale. | S2 |
| minor | chat: What insurance coverage is available and what are the… | **Case value (draft):** Firm rule (configurable): 1.5x–3x billed specials ($118,400.00); conflicting limits (Self-insured; no stated limit vs $100,000 per person / $300,000 per occurrence (Claims Service Bureau, 2026-09-08)); capped at $100,000 per person if those limits apply; before liens ($22,18… |  | partly: The cited span is a $3,475 expense and supports nothing here. The $100k cap, $22,180 lien and $118,400 specials appear elsewhere. The 1.5x–3x rule is not in the passages. The range is $177,600–$355,200, which is above the cap, and the figure is not supported by the cited text. | S2 |
| minor | chat: What is overdue right now, and what are we waiting on… | Defendants (Metro-North): scope-of-employment disclosure and Pullano deposition. [12] |  | partly: The 2026-03-06 note lists the scope-of-employment disclosure and the Pullano deposition as outstanding on the defendants' side. That note is about seven months old, and nothing confirms the items are still outstanding today. The later notes do not clearly show current status. | S2 |

**Q:** What is overdue right now, and what are we waiting on from other people?

> **Overdue**
> - Updated records and right shoulder surgical date from McCulloch Orthopaedic Surgical Services, PLLC: overdue, due 2026-08-25, waiting on McCulloch. [1] The 2026-08-03 email to McCulloch was the third written request for a surgical date. [2]
> - Obtain updated employment and commission records from client: overdue, due 2026-09-26. [3] The 2026-09-21 email to Justin Sapini asked for commission statements for the years after 2022 and anything from Northwestern Mutual confirming pre-accident production. [4]
> 
> **Waiting on others**
> - Justin Sapini: commission statements after 2022 and Northwestern Mutual confirmation of pre-accident production. [5]
> - Advanced Rockland Chiropractic Offices, P.C.: current daily notes and itemised bill to date, due 2026-10-07. [6] The 2026-09-26 email to Advanced Rockland requested the itemised ledger to date with CPT codes. [7]
> - SportsCare Physical Therapy of New York: ongoing treatment notes, due 2026-10-14. [8] The 2026-03-23 email to SportsCare was a second request for the updated ledger and notes. [9]
> - Montefiore Nyack Hospital: confirmation whether further records or charges exist beyond the 24 April 2023 attendance. [10]
> - Claims Service Bureau (Metro-North): incident report and vehicle assignment/dispatch records for the morning of the collision. [11]
> - Defendants (Metro-North): scope-of-employment disclosure and Pullano deposition. [12]

Citations 12; links: Next steps, McCulloch Orthopaedic share panel, Commission records email

**Q:** What insurance coverage is available and what are the limits?

> **Coverage and limits**
> 
> - **Metro-North Commuter Railroad (defendant, claim SIR068120):** Conflict: Self-insured; no stated limit vs $100,000 per person / $300,000 per occurrence (Claims Service Bureau, 2026-09-08) [1].
>   - A 2023-05-14 coverage note states Metro-North Commuter Railroad is self-insured, with no carrier and no declarations page to request, and that claims are administered by Claims Service Bureau, c/o D&D Associates, Garden City [2].
>   - A 2026-09-08 email from Claims Service Bureau states the bodily injury liability limits are $100,000 per person and $300,000 per occurrence, and that no excess or umbrella coverage is disclosed [3].
> - **Auto liability · Ferrara personal policy · defendant Anthony F. Ferrara:** $100,000 / $300,000 [4].
>   - The 2023-05-14 coverage note states that if Metro-North comes out of the case on scope of employment, the Ferrara policy is the entire recovery [2].
> - **UM/UIM · client's own policy:** $25,000 / $50,000 [5]. The 2026-06-04 case evaluation states "the client's own UM/UIM sits under it and adds nothing" [6].
> - **No-fault · Progressive Insurance Company · client's own policy:** Exhausted ($50,000) [7].
> 
> **Case value (draft):** Firm rule (configurable): 1.5x–3x billed specials ($118,400.00); conflicting limits (Self-insured; no stated limit vs $100,000 per person / $300,000 per occurrence (Claims Service Bureau, 2026-09-08)); capped at $100,000 per person if those limits apply; before liens ($22,180): $177,600 – $355,200 [8].
> 
> The 2026-09-09 note "Coverage confirmed in writing" states recovery is capped at $100,000 unless the case reaches a second defendant, and that the Medicaid lien of $22,180.00 comes off whatever is recovered [9]. The defendants' discovery response states insurance coverage information is to be provided under separate cover [10].

Citations 10; links: Coverage confirmation email (2026-09-08), Coverage note: Metro-North self-insured, Coverage KPIs

**Q:** And is the $100k/$300k Ferrara's policy or Metro-North's?

> - **Ferrara personal policy (defendant Anthony F. Ferrara):** $100,000 / $300,000 [1].
>   - The 2023-05-14 coverage note states Ferrara personally carries auto coverage identified at $100,000 / $300,000, and that if Metro-North comes out of the case on scope of employment, that policy is the entire recovery [2].
> - **Metro-North Commuter Railroad (defendant, claim SIR068120):** Conflict: Self-insured; no stated limit vs $100,000 per person / $300,000 per occurrence (Claims Service Bureau, 2026-09-08) [3].
>   - The 2023-05-14 coverage note states Metro-North is self-insured, with no carrier and no declarations page, and that claims are administered by Claims Service Bureau, c/o D&D Associates, Garden City, under claim number SIR068120 [2].
>   - A 2026-09-08 email from Claims Service Bureau to Aron Weiler states the bodily injury liability limits on this file are $100,000 per person and $300,000 per occurrence, with no excess or umbrella coverage disclosed [4].
> 
> The 2026-09-08 email does not name whose policy those limits belong to [4].
> 
> The defendants' discovery response stated insurance coverage information was to be provided under separate cover [5].

Citations 5; links: Claims Service Bureau email (2026-09-08), Coverage note: Metro-North is self-insured, Coverage KPIs

**Q:** What are the client's injuries, and which ones does the defense dispute?

> **Claimed injuries**
> 
> - The case summary describes injuries to both shoulders, both knees, and the head [1].
> - At intake, the client claimed injuries to the cervical and lumbar spine, both shoulders, and both knees [2].
> - Cervical spine: an MRI showed a shallow disc bulge at C5-6 flattening the left ventral margin of the canal [3].
> - Lumbar spine: an MRI showed an L5-S1 disc bulge with lateral predominance narrowing the lateral recesses and inferior foramina bilaterally [4].
> - The bill of particulars also lists thoracic spine myofascial derangement [5].
> - Left shoulder: the McCulloch Orthopaedic records show a partial posterior inferior labral tear and a low-grade interstitial infraspinatus tear [6].
> - Right shoulder: the McCulloch Orthopaedic records show an intermediate-grade interstitial infraspinatus tear and a partial posterior inferior labral tear [7].
> - Left knee: the injury record shows a horizontal undersurface tear of the posterior horn of the medial meniscus with prepatellar soft tissue edema [8].
> - Right knee: the injury record shows a horizontal undersurface tear of the posterior horn of the medial meniscus [9].
> 
> **Defense disputes**
> 
> - Right shoulder: the defense radiology review by Marc J. Katzman, M.D. states there is "no evidence of recent traumatic injury to the right shoulder" [10].
> - Left knee: the defense radiology review by Marc J. Katzman, M.D. states there is "no recent traumatic injury or internal derangement" [11].
> - Right knee: the defense radiology review by Marc J. Katzman, M.D. states there is "no recent traumatic injury or internal derangement" [12].
> - Brain: the defense radiology review by Marc J. Katzman, M.D. states the brain MRI "reveals no evidence of traumatic injury to the brain" [13].
> - The Katzman radiology review also found the 08/08/2023 DTI study within normal limits [14].
> - The Tsao expert exchange lists post-concussion syndrome, traumatic brain injury, and cervical, thoracic and lumbar strain as "objectively resolved" [15].
> - The Tsao expert exchange states the client can work without restrictions [15].
> 
> **Related exposures**
> 
> 
> I couldn't find a defense position specific to the left shoulder in the retrieved record.

Citations 15; links: Injuries, Katzman radiology review, Tsao neurological report

**Q:** When did we last talk to the client, and what did we discuss?

> The last client contact was a phone call: "Client call: should he keep going to PT" [1].
> 
> - He asked whether he should keep attending physical therapy while the case is pending; he was advised yes, keep going, and to keep his own record of every visit [2].
> - He confirmed the right shoulder surgery still has no date [2].
> - He said he is otherwise fine and will send updated employment records "soon" [2].
> 
> The prior call, on 2026-09-25, covered when the right shoulder will be done; Aron Weiler explained the surgeon wants to see him first and that the firm has asked five times, and the client was still going to physical therapy twice a week [3].
> 
> A follow-up call with the client is scheduled for 2026-10-14 to check whether the right shoulder surgery has been scheduled and to chase employment records [4].

Citations 4; links: Client call note (2026-09-27), Call re second surgery (2026-09-25), Next steps

**Q:** Did the Pullano deposition happen?

> I couldn't find any record that the Pullano deposition took place in the retrieved record. A subpoena ad testificandum dated November 2, 2025 directed Kyle Pullano to appear for a virtual Examination Before Trial on December 8, 2025 at 10:00 a.m. [1]. That deposition was only scheduled for 2025-12-08, and there is no record it occurred [2].
> 
> - Defendants' response to plaintiff's demand states that Kyle Pullano, a Metro-North employee, was a passenger in the responding defendants' vehicle [3].
> - The 2026-03-06 compliance conference note states that the Pullano deposition is outstanding on the defendants' side [4].
> - The 2026-09-15 case posture note states that Kyle Pullano has been identified as the person who can answer the scope-of-employment question and that nobody has contacted him [5].

Citations 5; links: Pullano subpoena (Dec 8, 2025 EBT), Case posture note (2026-09-15), Scheduled Pullano deposition

**Q:** What did the court rule on our summary judgment motion?

> I couldn't find a summary judgment motion or any ruling on one in the retrieved record.
> 
> The complaint describes a prior Decision and Order (Tsai, J.) that denied a cross motion and dismissed the earlier complaint for failure to provide the Presentation of Claim before starting suit. [1] After that dismissal, Plaintiff served another Presentation of Claim and started this suit under CPLR 205 [1].
> 
> The demand history and current damages update states that the action is now in discovery and both sides are trying to schedule the client deposition [2].

Citations 2; links: Complaint (prior Decision and Order), Case status update, Case status

