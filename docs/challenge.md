# Challenge brief

Event: Swans · Applied AI Hackathon (https://eventship.com/event/applied-ai-hackathon-1).
The exact challenge has not been announced yet. This file collects what the
organizers have shown so far. Update it as more slides or the brief arrive.

## Domain context: personal-injury law (slide 05, "All the law you need")

1. **Someone gets hurt.** The classic case is a car crash. The injured person
   hires an attorney on contingency: the attorney is paid only if the client wins.
2. **Doctors treat on a promise.** Medical providers treat the client now and
   are paid from the settlement later. That claim on the settlement is a
   **lien**, so the providers are also betting on the case.
3. **The case takes years.** Records pile up, insurers negotiate, and courts move
   slowly. The file grows with notes, emails, tasks and documents, often
   thousands of pages.
4. **Two sides, one case.** Both the **firm** and the **medical providers** need
   to know where the case stands. Right now, neither can see it.

Tip from the slide: liens are usually negotiated down at the end, so the client
takes home more money.

## What this suggests (inference, not the announced challenge)

- The likely problem is **case-status visibility** across a long, document-heavy
  personal-injury case, for both the PI firm and the lien-holding medical
  providers.
- Promising angles: an AI-generated case status summary from the case file,
  with every point linked to its source page; a provider-facing view of the case
  stage and expected settlement timing; and a lien tracker that supports
  end-of-case reduction negotiations.
- Users are now likely **PI attorneys and their staff** (paralegals, case
  managers) plus **medical-provider billing/lien staff**, not only trial
  attorneys. Confirm once the challenge is announced.

## Working direction (2026-10-02, from Aron)

**Turn a case into a dashboard.** Ingest a PI case file (notes, emails, tasks,
documents) and show where the case stands: stage, key dates and next steps,
medical treatment and bills/liens, insurer negotiation status, and open
risks. Every dashboard fact links to its source page (catalog: A1, A7, R2, R7
plus PDF highlighting). Likely two views: the firm, and the medical providers.

## Organizer pain point (live, 2026-10-02)

Existing case dashboards are awful: you **cannot see what is required, or the
state of things, at a glance**. Design implication: the first screen answers
"where does this case stand and what needs doing now?" in seconds. One headline
status, the few items that need action, then detail on demand (with source
links). Fewer widgets, not more.

## Data access (live, 2026-10-02)

We expect API access to the firm's case-management system, probably **Clio**
(to be confirmed). **Read-only, always. We never write to it.** See the rule in
`CLAUDE.md` → *Limits that still apply*.
