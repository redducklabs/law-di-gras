"""Opus headline brief written ONLY from verified facts.

The model sees fact ids and their values, never raw case text, and every
bullet must reference fact ids; bullets citing unknown ids are dropped. A case
value range is kept only when it references a specials or coverage fact.
"""

import hashlib
import json
from datetime import date

from pydantic import BaseModel

from app.db import connect
from app.llm import MODEL_OPUS, structured
from app.retrieval.fence import FENCE_RULE
from app.schemas import ActionItem, Citation, Fact, Headline


class Bullet(BaseModel):
    text: str
    fact_ids: list[str]


class CaseValue(BaseModel):
    low: float
    high: float
    basis: str
    fact_ids: list[str]


class BriefOut(BaseModel):
    status_line: str
    stage: str
    bullets: list[Bullet]
    case_value: CaseValue | None = None


SYSTEM = (
    "You are a senior personal-injury litigation attorney writing the top of a case brief for the firm's "
    "team. Write direct, professional analysis; it is a draft for attorney review. Use ONLY the facts "
    "provided (each has an id). Never add facts, numbers, names or dates that are not in them. "
    + FENCE_RULE
)

PROMPT = """Today is {today}. Matter status in the case-management system: {status}.

<case_record id="facts">
{facts}
</case_record>

<case_record id="open_actions">
{actions}
</case_record>

Write:
- status_line: one sentence (max ~30 words) saying where the case stands right now and what is next.
- stage: a 1-3 word PI case stage (e.g. Intake, Treating, Treatment complete, Demand prep,
  Demand sent, Negotiation, Litigation, Settled), chosen from the facts.
- bullets: 3 to 5 short bullets (max ~20 words each) a partner needs in 90 seconds: liability,
  injuries/treatment, specials vs coverage, liens, and the most urgent open item. Each bullet lists
  the fact_ids it rests on (at least one).
- Do not state a settlement value or range; the dashboard computes it by a fixed rule."""


def _fact_line(f: Fact) -> dict:
    d = {"id": f.id, "label": f.label, "value": f.value}
    if f.amount is not None:
        d["amount"] = f.amount
    if f.date:
        d["date"] = f.date
    return d


def write_brief(matter_id: str, facts: list[Fact], actions: list[ActionItem], status: str,
                today: date) -> Headline:
    verified = [f for f in facts if f.verified]
    by_id = {f.id: f for f in verified}
    acts = [{"title": a.title, "status": a.status, "due": a.due_date, "waiting_on": a.waiting_on}
            for a in actions[:15]]
    content = PROMPT.format(today=today.isoformat(), status=status or "unknown",
                            facts="\n".join(json.dumps(_fact_line(f)) for f in verified),
                            actions="\n".join(json.dumps(a) for a in acts) or "none")
    ih = hashlib.sha256((SYSTEM + content).encode()).hexdigest()
    with connect() as conn:
        row = conn.execute("SELECT input_hash, payload_json FROM digests WHERE matter_id = ? AND kind = 'brief'",
                           (matter_id,)).fetchone()
    if row and row["input_hash"] == ih:
        out = BriefOut.model_validate_json(row["payload_json"])
    else:
        out = structured(MODEL_OPUS, BriefOut, SYSTEM, content, purpose="brief", matter_id=matter_id,
                         effort="medium", max_tokens=4000)
        with connect() as conn:
            conn.execute("INSERT OR REPLACE INTO digests (matter_id, kind, input_hash, payload_json, model, created_at)"
                         " VALUES (?, 'brief', ?, ?, ?, datetime('now'))", (matter_id, ih, out.model_dump_json(), MODEL_OPUS))

    bullets: list[Fact] = []
    for i, b in enumerate(out.bullets):
        refs = [by_id[x] for x in b.fact_ids if x in by_id]
        if not refs:
            continue
        cits: list[Citation] = []
        for r in refs:
            cits.extend(r.citations[:2])
        bullets.append(Fact(id=f"brief-{i}", label=", ".join(r.label for r in refs[:3]), value=b.text,
                            citations=cits, verified=True))

    return Headline(status_line=out.status_line, stage=out.stage, bullets=bullets)
