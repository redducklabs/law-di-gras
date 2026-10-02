# Pitch talking points (4 min total: ~75 s talk, 88 s video, ~75 s talk)

## Before the video (~75 s)

- **The problem.** A PI file is thousands of entries. Attorneys asked for "the 10 that matter out of 300", what changed, and what's stuck, at a glance. Providers treating on a lien have no visibility at all.
- **Our bet: trust, not more widgets.** In law, one wrong cite costs credibility in front of a judge. Nothing reaches the screen unless its quote is found verbatim in the Clio record, one click from the highlighted page.
- **Real data.** Sapini is pulled live from Clio through a GET-only client and never written back. It's digested once into our own cache so it opens fast. No case content is hardcoded.

## Play the video (88 s)

## After the video (~75 s)

- **Honesty in layers:**
  - verbatim quote matching
  - numbers computed in code, not by the model
  - a code check plus a Claude judge on every generated sentence
  - conflicts in the file shown side by side, not resolved
  - an audit that runs on every digest and flags anything doubtful
- **It caught real errors in our own output.** Example: "both vehicles southbound" is flagged on screen because the record contradicts it.
- **Blind spots.** An agent reads the whole file the way a senior partner would, without being asked a question. Every finding is cited and checked for overstatement. It found that the defense claims it annexed the incident report while our own email says it isn't there.
- **Both halves of the brief:**
  - The firm gets the 90-second brief, top-3 next steps, drafts with citations, and chat that answers only from the record.
  - Providers get a server-filtered view: status, coverage, what we need, and their own bills. The attorney controls it; strategy and notes are never shared.
- **Practical.** About $2.50 per case to digest. In production, Clio webhooks would keep it live; we didn't build that because creating a subscription writes to Clio.
- **Close:** "Every fact traceable. Draft, not decision. The attorney stays in control."
