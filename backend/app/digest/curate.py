"""Haiku curation passes: "what changed recently" headlines and timeline milestones.

Both are cached in `digests` by a hash of their inputs, so an unchanged case
costs nothing. Recent headlines carry a verbatim quote checked by spans.locate.
"""

import hashlib
import json
from datetime import date, timedelta

from pydantic import BaseModel
from rapidfuzz import fuzz

from app.db import connect
from app.digest.spans import locate
from app.digest.structured import iso, row_citation
from app.llm import MODEL_HAIKU, structured
from app.retrieval.fence import FENCE_RULE, fence
from app.schemas import Fact, TimelineEvent

VERSION = "c4"
RECENT_DAYS = 14
RECENT_MIN = 5
RECENT_MAX = 10


def _cached(matter_id: str, kind: str, input_hash: str) -> str | None:
    with connect() as conn:
        row = conn.execute("SELECT input_hash, payload_json FROM digests WHERE matter_id = ? AND kind = ?",
                           (matter_id, kind)).fetchone()
    return row["payload_json"] if row and row["input_hash"] == input_hash else None


def _store(matter_id: str, kind: str, input_hash: str, payload: str) -> None:
    with connect() as conn:
        conn.execute("INSERT OR REPLACE INTO digests (matter_id, kind, input_hash, payload_json, model, created_at)"
                     " VALUES (?, ?, ?, ?, ?, datetime('now'))", (matter_id, kind, input_hash, payload, MODEL_HAIKU))


# --- Recent activity -------------------------------------------------------

class RecentItem(BaseModel):
    record_id: int
    headline: str   # who did what, max ~12 words
    detail: str     # one sentence
    quote: str      # verbatim span from the record


class RecentOut(BaseModel):
    items: list[RecentItem]


RECENT_SYSTEM = (
    "You write the 'what changed recently' feed of a personal-injury case dashboard for the firm's "
    "attorneys and paralegals. " + FENCE_RULE
)

RECENT_PROMPT = """For EACH record below, write one item:
- headline: max 12 words, says who did what (e.g. "Defense counsel proposed deposition dates",
  "Client reported new knee pain", "Adjuster confirmed policy limits"). Name the role or party,
  not "Email" or "Note".
- detail: one sentence with the specific substance (dates, amounts, next step) from the record.
- quote: a short span (10-150 characters) copied character-for-character from the record that
  supports the headline. No ellipses, no paraphrase.
- record_id: the record's id.

{records}"""


def recent_activity(matter_id: str, today: date) -> list[Fact]:
    with connect() as conn:
        rows = conn.execute("SELECT * FROM sources WHERE matter_id = ? AND kind IN ('note', 'communication', 'document')"
                            " AND date IS NOT NULL ORDER BY date DESC, id LIMIT 40", (matter_id,)).fetchall()
    cutoff = (today - timedelta(days=RECENT_DAYS)).isoformat()
    window = [r for r in rows if (iso(r["date"]) or "") >= cutoff]
    picked = (window if len(window) >= RECENT_MIN else rows[:RECENT_MIN * 2 - 2])[:RECENT_MAX]
    if not picked:
        return []
    ih = hashlib.sha256((VERSION + "".join(f"{r['id']}={r['content_hash']};" for r in picked)).encode()).hexdigest()
    payload = _cached(matter_id, "recent", ih)
    if payload:
        out = RecentOut.model_validate_json(payload)
    else:
        records = "\n\n".join(
            fence(i, f'kind="{r["kind"]}" date="{iso(r["date"])}" title="{(r["title"] or "")[:120]}"',
                  r["text"] or r["title"] or "", cap=2500)
            for i, r in enumerate(picked))
        out = structured(MODEL_HAIKU, RecentOut, RECENT_SYSTEM, RECENT_PROMPT.format(records=records),
                         purpose="recent", matter_id=matter_id, max_tokens=3000)
        _store(matter_id, "recent", ih, out.model_dump_json())

    facts: list[Fact] = []
    seen: set[int] = set()
    with connect() as conn:
        for it in out.items:
            if not 0 <= it.record_id < len(picked) or it.record_id in seen:
                continue
            seen.add(it.record_id)
            r = picked[it.record_id]
            if any(f.date == iso(r["date"]) and fuzz.token_set_ratio(f.label, it.headline) >= 70 for f in facts):
                continue  # same event logged twice (e.g. call note + communication)
            c = locate(conn, r["id"], it.quote)
            if c is None or not c.verified:
                c = row_citation(conn, r)  # still links to the record; quote = its title
            facts.append(Fact(id=f"recent-{it.record_id}", label=it.headline.strip(), value=it.detail.strip(),
                              date=iso(r["date"]), citations=[c], verified=c.verified))
    facts.sort(key=lambda f: f.date or "", reverse=True)
    return facts


# --- Timeline milestones ---------------------------------------------------

class MilestoneOut(BaseModel):
    indices: list[int]


MILESTONE_SYSTEM = (
    "You curate the compact timeline strip of a personal-injury case dashboard. " + FENCE_RULE
)

MILESTONE_PROMPT = """Today is {today}. Pick at most 12 events, including 1-2 upcoming (after today) if any exist, (by index) that a trial attorney would
want on a one-line case timeline: the incident, the first emergency/hospital visit, pivotal
treatment (surgery, injections, imaging that confirmed injuries, end of treatment), demand sent,
suit filed/served, pivotal court dates, statute of limitations, and the next upcoming deadlines,
depositions, IMEs, mediation or trial. Skip routine correspondence, internal reviews and duplicates.
Never pick routine recurring therapy or chiropractic visits; for upcoming items prefer what moves
the case (surgery scheduling, court dates, depositions, IMEs, file reviews before conferences).

<case_record id="events">
{events}
</case_record>"""


def mark_milestones(matter_id: str, events: list[TimelineEvent], today: date, cap: int = 12) -> None:
    """Sets `major` in place. Falls back to incident + nearest deadlines if the call fails."""
    if not events:
        return
    lines = "\n".join(json.dumps({"i": i, "date": e.date, "kind": e.kind, "label": e.label})
                      for i, e in enumerate(events))
    ih = hashlib.sha256((VERSION + today.isoformat() + lines).encode()).hexdigest()
    payload = _cached(matter_id, "milestones", ih)
    picks: list[int] = []
    try:
        if payload:
            picks = MilestoneOut.model_validate_json(payload).indices
        else:
            out = structured(MODEL_HAIKU, MilestoneOut, MILESTONE_SYSTEM,
                             MILESTONE_PROMPT.format(today=today.isoformat(), events=lines),
                             purpose="milestones", matter_id=matter_id, max_tokens=500)
            picks = out.indices
            _store(matter_id, "milestones", ih, out.model_dump_json())
    except Exception as e:
        print(f"milestones failed, using fallback: {e}")
    chosen = {i for i, e in enumerate(events) if e.kind == "incident"}
    for i in picks:
        if len(chosen) >= cap:
            break
        if 0 <= i < len(events):
            chosen.add(i)
    future = [i for i, e in enumerate(events) if e.is_future]
    if future and not any(events[i].is_future for i in chosen):
        chosen.add(future[0])  # the strip always shows what is coming next
    for i in chosen:
        events[i].major = True
