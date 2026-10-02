"""Opus headline brief, verified claim by claim against the quotes it cites.

Opus sees each verified fact with its own quotes and must reference fact ids.
Every bullet and the status line then go through the same checks as drafts:
deterministic tokens (dates, amounts, codes, names) and a Sonnet claim judge,
both against ONLY the quotes of the facts it references. One regenerate with
the failures listed; anything still unsupported is stripped (or the bullet
dropped). The verified Headline is cached by its exact input.
"""

import hashlib
import json
from datetime import date

from pydantic import BaseModel

from app.db import connect
from app.digest.conflicts import check_statements
from app.digest.verify import Corpus, check_tokens, judge_claims
from app.llm import MODEL_OPUS, structured
from app.retrieval.fence import FENCE_RULE
from app.schemas import ActionItem, Citation, Fact, Headline

VERSION = "b7"


class Bullet(BaseModel):
    text: str
    fact_ids: list[str]


class BriefOut(BaseModel):
    status_line: str
    status_fact_ids: list[str]
    stage: str
    bullets: list[Bullet]


SYSTEM = (
    "You are a senior personal-injury litigation attorney writing the top of a case brief for the firm's "
    "team; it is a draft for attorney review. Every statement must be supported by the QUOTES of the facts "
    "it cites (ids). Do not add counts, causes, characterizations, attributions (who said or wants what), "
    "dates, amounts or names that those quotes do not state. Prefer fewer, safer words. Attribute every "
    "defense IME / defense expert opinion explicitly (e.g. 'defense radiology review says ...'); never blend "
    "it into the client's findings. Where a fact is marked Conflict or carries a caveat, keep that visible. "
    "When the status line names who the case is against, name every defendant the facts name. "
    "A defense opinion covers only the body part and side it addresses: name it ('defense review, left "
    "knee: ...') and never let it read as covering other injuries in the same sentence. "
    + FENCE_RULE
)

PROMPT = """Today is {today}. Matter status in the case-management system: {status}.

Facts (id, label, value, quotes). Only the quotes are evidence:
<case_record id="facts">
{facts}
</case_record>

Open actions (also citable by id; their quote is the Clio task/calendar record):
<case_record id="open_actions">
{actions}
</case_record>

Write:
- status_line: one sentence (max ~30 words): where the case stands and what is next.
  status_fact_ids: the ids it rests on (at least one).
- stage: a 1-3 word PI case stage (e.g. Intake, Treating, Treatment complete, Demand prep,
  Demand sent, Negotiation, Litigation, Settled), chosen from the facts.
- bullets: 3 to 5 short bullets (max ~20 words each) a partner needs in 90 seconds: liability,
  injuries/treatment, specials vs coverage, liens, the most urgent open item. Each lists its fact_ids.
- Do not state a settlement value or range; the dashboard computes it by a fixed rule.{retry}"""

# Facts computed in code from cited Clio rows: their value is itself evidence.
DERIVED = ("specials", "firm_spent", "last_client_contact", "charge-", "billed-", "adverse_parties")


def _quotes(f: Fact) -> list[str]:
    q = [c.quote[:400] for c in f.citations if c.verified]
    if f.id.startswith(DERIVED):
        q.insert(0, f"{f.label}: {f.value}")
    return q


def _cits(f: Fact) -> list[Citation]:
    return list(f.citations) if f.id.startswith(DERIVED) else list(f.citations[:2])


def _action_fact(i: int, a: ActionItem) -> Fact:
    parts = [a.title, f"status {a.status}"]
    if a.due_date:
        parts.append(f"due {a.due_date}")
    if a.waiting_on:
        parts.append(f"waiting on {a.waiting_on}")
    return Fact(id=f"action-{i}", label="Open action", value="; ".join(parts), citations=a.citations,
                verified=True)


def _check(matter_id: str, items: list[tuple[str, list[str]]], names: Corpus) -> list[list[str]]:
    judged = judge_claims(matter_id, items, purpose="verify_brief")
    fails = []
    for (text, quotes), j in zip(items, judged):
        fails.append(check_tokens(text, Corpus("\n".join(quotes)), names) + list(j.unsupported))
    return fails


def _strip(matter_id: str, items: list[tuple[str, list[str]]], names: Corpus) -> list[str]:
    """Keep only supported parts; "" when nothing safe remains."""
    out = []
    for (text, quotes), j in zip(items, judge_claims(matter_id, items, purpose="verify_brief")):
        if not j.unsupported and not check_tokens(text, Corpus("\n".join(quotes)), names):
            out.append(text)
            continue
        safe = j.supported_text.strip()
        out.append(safe if safe and not check_tokens(safe, Corpus("\n".join(quotes)), names) else "")
    return out


def write_brief(matter_id: str, facts: list[Fact], actions: list[ActionItem], status: str,
                today: date) -> Headline:
    verified = [f for f in facts if f.verified] + [_action_fact(i, a) for i, a in enumerate(actions[:15])]
    by_id = {f.id: f for f in verified}
    fact_lines = "\n".join(json.dumps({"id": f.id, "label": f.label, "value": f.value, "quotes": _quotes(f)})
                           for f in verified if not f.id.startswith("action-"))
    action_lines = "\n".join(json.dumps({"id": f.id, "record": f.value}) for f in verified if f.id.startswith("action-"))
    base = dict(today=today.isoformat(), status=status or "unknown", facts=fact_lines, actions=action_lines or "none")
    ih = hashlib.sha256((VERSION + SYSTEM + PROMPT.format(**base, retry="")).encode()).hexdigest()
    with connect() as conn:
        row = conn.execute("SELECT input_hash, payload_json FROM digests WHERE matter_id = ? AND kind = 'brief'",
                           (matter_id,)).fetchone()
        titles = [r[0] or "" for r in conn.execute("SELECT title FROM sources WHERE matter_id = ?", (matter_id,))]
    if row and row["input_hash"] == ih:
        return Headline.model_validate_json(row["payload_json"])
    names = Corpus("\n".join(titles))

    def items_of(out: BriefOut) -> list[tuple[str, list[str], list[Fact]]]:
        rows = []
        for text, ids in [(out.status_line, out.status_fact_ids)] + [(b.text, b.fact_ids) for b in out.bullets]:
            refs = [by_id[x] for x in ids if x in by_id]
            rows.append((text, [q for r in refs for q in _quotes(r)], refs))
        return rows

    out = structured(MODEL_OPUS, BriefOut, SYSTEM, PROMPT.format(**base, retry=""), purpose="brief",
                     matter_id=matter_id, effort="medium", max_tokens=4000)
    rows = items_of(out)
    fails = _check(matter_id, [(t, q) for t, q, _ in rows], names)
    if any(fails):
        listed = "\n".join(f"- \"{rows[i][0][:100]}\": unsupported {', '.join(f)}" for i, f in enumerate(fails) if f)
        retry = ("\n\nYour previous version had statements not supported by the quotes of the facts they cite. "
                 f"Rewrite them using only what those quotes say, or cite the facts that do:\n{listed}")
        out = structured(MODEL_OPUS, BriefOut, SYSTEM, PROMPT.format(**base, retry=retry), purpose="brief_retry",
                         matter_id=matter_id, effort="medium", max_tokens=4000)
        rows = items_of(out)
    # Re-cite before dropping: a statement the cited facts don't support may be supported elsewhere.
    fails = _check(matter_id, [(t, q) for t, q, _ in rows], names)
    extra: dict[int, list[Citation]] = {}
    failing = [i for i, f in enumerate(fails) if f]
    if failing:
        found = check_statements(matter_id, [(rows[i][0], [c for r in rows[i][2] for c in r.citations]) for i in failing],
                                 purpose="record_check_recite")
        for i, (v, cit) in zip(failing, found):
            if v.verdict == "supported" and cit is not None:
                extra[i] = [cit]
                rows[i] = (rows[i][0], rows[i][1] + [cit.quote], rows[i][2])
    texts = _strip(matter_id, [(t, q) for t, q, _ in rows], names)

    status_refs = rows[0][2]
    status_extra = extra.get(0, [])
    status_line = texts[0] or (f"{out.stage}." if out.stage else "")
    bullets: list[Fact] = []
    for i, (text, (_, _, refs)) in enumerate(zip(texts[1:], rows[1:])):
        if not text or not refs:
            continue
        # record sources first, computed billing rows after, so a bullet's limits aren't "cited" to bills
        cits = [c for r in refs if not r.id.startswith(DERIVED) for c in _cits(r)] + extra.get(i + 1, []) + \
            [c for r in refs if r.id.startswith(DERIVED) for c in _cits(r)]
        bullets.append(Fact(id=f"brief-{i}", label=", ".join(r.label for r in refs[:3]), value=text,
                            citations=cits, verified=True))
    head = Headline(status_line=status_line, stage=out.stage, bullets=bullets,
                    status_citations=[c for r in status_refs for c in _cits(r)] + status_extra)
    with connect() as conn:
        conn.execute("INSERT OR REPLACE INTO digests (matter_id, kind, input_hash, payload_json, model, created_at)"
                     " VALUES (?, 'brief', ?, ?, ?, datetime('now'))", (matter_id, ih, head.model_dump_json(), MODEL_OPUS))
    return head
