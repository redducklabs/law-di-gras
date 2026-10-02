# Auto audit report: 00001-Sapini

Generated 2026-10-02T12:36 by `uv run python -m app.audit` (checks 7). Dashboard cached 2026-10-02 19:26:25, generated_at 2026-10-02T19:26:25+00:00. Audit LLM cost $0.28.

**Findings:** 0 critical, 2 major, 5 minor. Items audited: 88.

Severity: critical = wrong number/date/party/tense on screen; major = unsupported or misleading; minor = cosmetic.

## Check 7. Ask-the-case chat

| Sev | Item | On screen | Cited quote | What's wrong | Owner |
|---|---|---|---|---|---|
| major | chat: And is the $100k/$300k Ferrara's policy or Metro-Nort… | **Dashboard:** The Dashboard KPI for Metro-North Commuter Railroad, claim SIR068120, reads: Conflict: Self-insured; no stated limit vs $100,000 per person / $300,000 per occurrence (Claims Service Bureau, 2026-09-08) [3]. |  | unsupported: No excerpt or passage shows a Dashboard KPI with this text. The cited note only says Metro-North is self-insured, and the 2026-09-08 email gives the limits. The 'Conflict' KPI reading is not in the record. | S2 |
| major | chat: What are the client's injuries, and which ones does t… | I couldn't find a defense dispute of the cervical, lumbar, thoracic or left shoulder findings in the retrieved record. |  | unsupported: A 2026-09-15 note and a 2023 note say the defence will lean on the glenoid hypoplasia in the left shoulder MRI, and the defense IME (Hostin) lists the left shoulder MRI including hypoplasia. More importantly, the defense IME doctors (Tsao, Hostin) examined the cervical, lumbar and shoulder complaints; the retrieved record does not show their conclusions, so the absence claim is not established, and the 2023 note anticipates a defense challenge to the left shoulder. | S2 |
| minor | chat: Did the Pullano deposition happen? | The timeline lists the Pullano deposition as scheduled for 2025-12-08, with no record it occurred [2]. |  | partly: The subpoena supports the December 8, 2025 date, and nothing shows the deposition occurred. But no 'timeline' is in the record, and the cited subpoena only commands appearance, so 'scheduled' as listed on a timeline is unsupported. | S2 |
| minor | chat: Did the Pullano deposition happen? | An open action lists the Metro-North scope-of-employment disclosure and Pullano deposition with status waiting, waiting on Defendants (Metro-North) [4]. |  | partly: The note supports the two items being outstanding on the defendants' side. No 'open action' with the status 'waiting' appears in the passages, so that framing is unsupported. | S2 |
| minor | chat: What did the court rule on our summary judgment motio… | The complaint states that, by Decision and Order (Tsai, J.), the Court denied the cross motion and dismissed the Complaint, noting Plaintiff's failure to provide the Presentation of Claim before starting suit [1]. |  | partly: The complaint does recite a Decision and Order (Tsai, J.) that denied the cross motion and dismissed the earlier complaint for failure to present the claim. But that ruling was in the prior action and not on a summary judgment motion. The sentence blurs this by attributing it to 'the complaint' without noting that it concerns the earlier case. | S2 |
| minor | chat: What did the court rule on our summary judgment motio… | The "Demand history and current damages update" note states that the action is now in discovery and both sides are trying to schedule the client deposition [2]. |  | partly: The cited note (2026-08-03) says the action is now in discovery. The statement that both sides are trying to schedule the client deposition comes from a different note dated 2025-08-27, which is not the one cited, and that status may be out of date. | S2 |
| minor | chat: What insurance coverage is available and what are the… | **Defendant liability (Metro-North Commuter Railroad, claim SIR068120):** Conflict: Self-insured; no stated limit vs $100,000 per person / $300,000 per occurrence (Claims Service Bureau, 2026-09-08) [1]. |  | partly: Both positions are in the record (2023 self-insured note vs 2026-09-08 confirmation of $100k/$300k), but the cited note only supports the self-insured side. The later written confirmation supersedes it; framing as an unresolved conflict is questionable. | S2 |

**Q:** What is overdue right now, and what are we waiting on from other people?

> - Updated records and right shoulder surgical date from McCulloch Orthopaedic Surgical Services, PLLC: status overdue, due 2026-08-25, waiting on McCulloch Orthopaedic [1]. The firm's 2026-08-03 email to McCulloch was its third written request for a surgical date [2].
> - Obtain updated employment and commission records from client: status overdue, due 2026-09-26 [3].
> 
> **Waiting on others**
> 
> - **Justin Sapini (client):** commission statements after 2022 and Northwestern Mutual confirmation of pre-accident production [4]. The 2026-09-21 email to Justin Sapini described this as the single biggest number in the claim, resting on one document [5].
> - **McCulloch Orthopaedic Surgical Services, PLLC:** updated records and right shoulder surgical date (overdue) [1].
> - **Advanced Rockland Chiropractic Offices, P.C.:** current daily notes and itemised bill to date, due 2026-10-07 [6]. The firm's 2026-09-26 email requested the itemised ledger with CPT codes [7].
> - **SportsCare Physical Therapy of New York:** ongoing treatment notes, due 2026-10-14 [8].
> - **Montefiore Nyack Hospital:** confirmation whether further records or charges exist beyond the 24 April 2023 attendance [9].
> - **Claims Service Bureau (Metro-North):** incident report and vehicle assignment/dispatch records for the morning of the collision [10].
> - **Defendants (Metro-North):** scope-of-employment disclosure and Pullano deposition [11]. The Pullano deposition was scheduled for 2025-12-08, with no record it occurred [12].

Citations 12; links: Next steps, McCulloch Orthopaedic share panel, Commission records email

**Q:** What insurance coverage is available and what are the limits?

> **Defendant liability (Metro-North Commuter Railroad, claim SIR068120):** Conflict: Self-insured; no stated limit vs $100,000 per person / $300,000 per occurrence (Claims Service Bureau, 2026-09-08) [1].
> 
> - A coverage note dated 2023-05-14 states that Metro-North Commuter Railroad is self-insured, with no carrier and no declarations page to request [2].
> - The 2023-05-14 coverage note states that claims are administered by Claims Service Bureau, c/o D&D Associates, Garden City, claim number SIR068120 [2].
> - The 2023-05-14 coverage note states that Ferrara personally carries auto coverage identified at $100,000 / $300,000, and that if Metro-North comes out of the case on scope of employment, that policy is the entire recovery [2].
> - A 2026-09-08 email from Claims Service Bureau states that the bodily injury liability limits are $100,000 per person and $300,000 per occurrence, and that no excess or umbrella coverage is disclosed [3].
> - A 2026-09-09 firm note states that coverage was confirmed in writing by the adjuster and that recovery is capped at $100,000 unless the case reaches a second defendant [4].
> 
> **Client's own coverage:**
> - UM/UIM (client's own policy): $25,000 / $50,000; per firm note of 2026-06-04, UM/UIM sits under defendant's $100,000 and adds nothing [5].
> - No-fault (Progressive Insurance Company, client's own policy): Exhausted ($50,000) [6].
> 
> **Lien:** New York State Medicaid has asserted a lien against any recovery [7]. The 2026-09-09 firm note states the Medicaid lien is $22,180.00 [4].

Citations 7; links: Coverage KPIs, Claims Service Bureau coverage email, Self-insured coverage note

**Q:** And is the $100k/$300k Ferrara's policy or Metro-North's?

> - A 2023-05-14 coverage note states that Metro-North Commuter Railroad is self-insured, with no carrier and no declarations page, and that Ferrara personally carries auto coverage identified at $100,000 / $300,000. [1]
> - The 2023-05-14 coverage note states that Metro-North claims are administered by Claims Service Bureau, claim number SIR068120. [1] A 2026-09-08 email from Claims Service Bureau states that the bodily injury liability limits on the file are $100,000 per person and $300,000 per occurrence, with no excess or umbrella coverage disclosed [2].
> - **Dashboard:** The Dashboard KPI for Metro-North Commuter Railroad, claim SIR068120, reads: Conflict: Self-insured; no stated limit vs $100,000 per person / $300,000 per occurrence (Claims Service Bureau, 2026-09-08) [3].
> 
> I couldn't find, in the retrieved record, a statement identifying whose policy the limits in the 2026-09-08 Claims Service Bureau email belong to [2]. The 2023-05-14 note states that if Metro-North comes out of the case on scope of employment, Ferrara's policy is the entire recovery [1].

Citations 3; links: Coverage note: Metro-North is self-insured (2023-05-14), Claims Service Bureau email (2026-09-08), Coverage KPIs

**Q:** What are the client's injuries, and which ones does the defense dispute?

> **Claimed injuries (per imaging and records)**
> - **Cervical spine:** MRI showed straightening of the lordosis and a shallow disc bulge at C5-6 flattening the left ventral margin of the canal [1].
> - **Lumbar spine:** MRI showed an L5-S1 disc bulge with lateral predominance narrowing the lateral recesses and inferior foramina bilaterally [2].
> - **Thoracic spine:** The bill of particulars claims thoracic spine myofascial derangement [3].
> - **Left shoulder:** MRI showed a partial tear of the posterior inferior labrum at 8-9 o'clock and a low-grade interstitial tear of the posterior infraspinatus fibers [4].
> - **Right shoulder:** MRI of 05/24/2023 showed an intermediate-grade interstitial tear of the anterior half of the infraspinatus and a partial tear of the posterior inferior labrum at 8 o'clock [5].
> - **Left knee:** MRI of 07/03/2023 showed a horizontal undersurface tear of the posterior horn of the medial meniscus, with prepatellar soft tissue edema reflecting soft tissue contusion [6].
> - **Right knee:** MRI of 07/03/2023 showed a horizontal undersurface tear of the posterior horn of the medial meniscus [7].
> - **Brain:** MRI brain with DTI of 08/08/2023 showed 2 of 12 regions of interest and 1 of 6 white matter tracts abnormal, and a hemosiderin focus in the subcortical right parietal lobe [8].
> 
> **Disputed in the defense radiology review (Marc J. Katzman, M.D.)** [9]
> - **Right shoulder:** The defense radiology review by Marc J. Katzman, M.D. states "no evidence of recent traumatic injury to the right shoulder" [9].
> - **Left knee:** The defense radiology review by Marc J. Katzman, M.D. states "no recent traumatic injury or internal derangement" [10].
> - **Right knee:** The defense radiology review by Marc J. Katzman, M.D. states "no recent traumatic injury or internal derangement" [11].
> - **Brain:** The defense radiology review by Marc J. Katzman, M.D. states the brain MRI "reveals no evidence of traumatic injury to the brain" [12].
> 
> I couldn't find a defense dispute of the cervical, lumbar, thoracic or left shoulder findings in the retrieved record.
> 
> **Related exposures**
> - The 2026-09-15 firm note flags that the left shoulder MRI reports hypoplasia of the posterior inferior glenoid, a developmental variant, as a causation exposure [13].
> - The client denied prior injuries at intake, but his own records include 2011 left ankle and left foot X-rays showing a small dorsal avulsion fracture of the anterior talus [14].

Citations 14; links: Injuries, Katzman radiology review, Case posture note (causation exposure)

**Q:** When did we last talk to the client, and what did we discuss?

> The most recent client contact on the dashboard is a phone call: "Client call: should he keep going to PT" [1]. The note "Client call: treatment status" dated 2026-09-27 records that call [2].
> 
> What was discussed, per the 2026-09-27 note [2]:
> - Justin called and asked whether he should keep attending physical therapy while the case is pending [2].
> - He was advised yes, to keep going, and to keep his own record of every visit [2].
> - He confirmed the right shoulder surgery still has no date [2].
> - He said he is otherwise fine and will send updated employment records "soon" [2].
> 
> For context, the 2026-09-25 call note records that he asked again when the right shoulder will be done, and was told the surgeon wants to see him first and that the firm has asked five times [3]. The 2026-09-25 call note also records that he is still going to physical therapy twice a week [3].
> 
> A follow-up call with the client re treatment status is scheduled for 2026-10-14 [4].

Citations 4; links: Client call note 2026-09-27, Call note 2026-09-25, Next steps

**Q:** Did the Pullano deposition happen?

> I couldn't find any record that the Pullano deposition took place in the retrieved record.
> 
> - A subpoena ad testificandum commanded Kyle Pullano to appear for an Examination Before Trial on December 8, 2025, at 10:00 a.m., to be conducted virtually. [1]
> - The timeline lists the Pullano deposition as scheduled for 2025-12-08, with no record it occurred [2].
> - The compliance conference note dated 2026-03-06 states that the Metro-North scope-of-employment disclosure and the Pullano deposition were outstanding on the defendants' side [3].
> - An open action lists the Metro-North scope-of-employment disclosure and Pullano deposition with status waiting, waiting on Defendants (Metro-North) [4].
> - The case posture note dated 2026-09-15 states that Kyle Pullano, a Metro-North employee, has been identified as the person who can answer the scope-of-employment question and that nobody has contacted him [5].
> - The defendants' response to demand identifies Kyle Pullano, Metro-North Employee, as a passenger in the responding defendants' vehicle [6].
> - The case posture note dated 2026-09-15 describes scope of employment as "the whole case" [5].

Citations 6; links: Pullano subpoena, Scheduled Pullano deposition, Next steps

**Q:** What did the court rule on our summary judgment motion?

> I couldn't find a summary judgment motion or any ruling on one in the retrieved record.
> 
> Related court and status items in the retrieved record:
> - The complaint states that, by Decision and Order (Tsai, J.), the Court denied the cross motion and dismissed the Complaint, noting Plaintiff's failure to provide the Presentation of Claim before starting suit [1].
> - The complaint states that Plaintiff then served another Presentation of Claim by overnight mail dated September 10, 2024, and started this suit pursuant to CPLR 205 after waiting 30 days [1].
> - The "Demand history and current damages update" note states that the action is now in discovery and both sides are trying to schedule the client deposition [2].

Citations 2; links: Complaint (prior Decision and Order), Case status, Timeline

