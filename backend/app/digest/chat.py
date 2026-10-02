"""Ask-the-case chat: multi-turn, cited, verified, with server-validated deeplinks.

Evidence = retrieved passages (hybrid search on the question, plus the previous
question for follow-ups) + the cached Dashboard's actions, timeline and KPI
facts, each carrying its own verified citation. Opus answers citing evidence as
[n]. Then: every cited sentence is checked (tokens + Sonnet claim judge) against
ONLY the evidence it cites; uncited sentences may not carry dates, amounts or
names. One regenerate with the failures, then unsupported sentences are
stripped. Links are validated against the dashboard and the returned citations.
"""

import hashlib
import json
import re
from datetime import date

from pydantic import BaseModel

from app.db import connect
from app.digest import dashboard as dash
from app.digest.verify import Corpus, check_tokens, judge_claims
from app.llm import MODEL_OPUS, structured
from app.retrieval.fence import FENCE_RULE, fence
from app.retrieval.search import search
from app.schemas import ChatRequest, ChatResponse, Citation, Dashboard, DeepLink

VERSION = "ch3"
SECTIONS = {"timeline", "next-steps", "status", "kpis", "injuries", "treatment", "recent"}
ROUTES = {"/cases"}
MAX_LINKS = 3


class LinkOut(BaseModel):
    label: str
    kind: str                       # section | source | timeline | share | route
    section: str | None = None
    evidence: int | None = None     # kind=source: the [n] to open
    date: str | None = None
    contact_id: str | None = None
    path: str | None = None


class ChatOut(BaseModel):
    answer_markdown: str
    links: list[LinkOut]


SYSTEM = (
    "You answer questions about one personal-injury case for the firm's attorneys, paralegals and case "
    "managers. Answer ONLY from the numbered evidence. Put [n] after every sentence that states a fact, "
    "citing the evidence that says it. Never add dates, amounts, names, counts, causes or attributions the "
    "cited evidence does not state. Never claim the record lacks something: if the evidence does not answer, "
    "say \"I couldn't find <X> in the retrieved record\". A date that was only scheduled, noticed or subpoenaed "
    "is not an event that happened: say 'scheduled for'. A 'Calendar:' entry is only the firm's calendar; if "
    "other evidence shows the event was performed (operative record, bill), say it was performed. For "
    "coverage, limits and case value, state them exactly as the 'Dashboard KPI' evidence does, including any "
    "Conflict wording. Every sentence must stand alone: name its source instead of 'the same note'. Present "
    "an older note's status as of its date. Direct, concise, professional; markdown lists allowed. "
    + FENCE_RULE
)

PROMPT = """Today is {today}.

Earlier in this conversation:
{history}

Evidence (cite as [n]):
{evidence}

Dashboard sections you can link to: {sections}.
Providers you can open the share panel for (contact_id: name): {providers}

Question: {question}

Also propose up to 3 helpful links (kind: section | source | timeline | share | route):
- section: one of the section ids above;  - source: evidence number to open;
- timeline: a date that appears in the evidence;  - share: a provider contact_id above;
- route: "/cases". Only propose links that help with this question.{retry}"""


def _dash_evidence(d: Dashboard) -> list[tuple[str, Citation]]:
    """Dashboard items as citable evidence: (text, first verified citation)."""
    out: list[tuple[str, Citation]] = []

    def add(text: str, cits: list[Citation], every: bool = False):
        vs = [c for c in cits if c.verified]
        for c in (vs if every else vs[:1]):  # every: a fact citing both sides (e.g. defense IME) keeps both
            out.append((text, c))

    h = d.headline
    add(f"Case status ({h.stage}): {h.status_line}", h.status_citations)
    for f in d.injuries:
        add(f"Injury: {f.label}: {f.value}", f.citations, every=True)

    for a in d.actions:
        parts = [f"Open action: {a.title}", f"status {a.status}"]
        if a.due_date:
            parts.append(f"due {a.due_date}")
        if a.waiting_on:
            parts.append(f"waiting on {a.waiting_on}")
        add("; ".join(parts), a.citations)
    for e in d.timeline:
        add(f"Timeline {e.date}{' (upcoming)' if e.is_future else ''}: {e.label}", e.citations)
    k = d.kpis
    for f in [k.specials, k.firm_spent, k.case_value, *k.coverage, *k.liens, d.last_client_contact]:
        if f and f.verified:
            add(f"Dashboard KPI: {f.label}: {f.value}", f.citations, every=f in k.coverage)
    for t in d.treatment:
        bits = [f"Treatment: {t.provider}"]
        if t.first_visit:
            bits.append(f"first {t.first_visit}")
        if t.last_visit:
            bits.append(f"{'billed through' if t.last_visit_basis == 'billed_through' else 'last'} {t.last_visit}")
        if t.next_visit:
            bits.append(f"next scheduled {t.next_visit}")
        if t.billed:
            bits.append(f"billed {t.billed.value}")
        add("; ".join(bits), t.citations or (t.billed.citations if t.billed else []))
    return out


def _providers(matter_id: str) -> list[tuple[str, str]]:
    try:
        from app.share.providers import list_providers
        return [(p.contact_id, p.name) for p in list_providers(matter_id)]
    except Exception:
        return []


_SENT = re.compile(r"(?<=[.!?]|\])\s+(?=[A-Z*(-])")  # [n] markers stay with their sentence
_MARK = re.compile(r"\[(\d+)\]")


def _sentences(md: str) -> list[tuple[int, str]]:
    """(line index, sentence) for every sentence in the markdown."""
    out = []
    for li, line in enumerate(md.split("\n")):
        for s in _SENT.split(line):
            if s.strip():
                out.append((li, s))
    return out


def _verify(matter_id: str, md: str, ev_text: list[str]) -> tuple[list[tuple[int, str]], list[list[str]], list[str]]:
    """Sentences, their failures, and the judge's supported rewrite for each."""
    sents = _sentences(md)
    items, idx = [], []
    for i, (_, s) in enumerate(sents):
        ns = [int(n) for n in _MARK.findall(s) if 1 <= int(n) <= len(ev_text)]
        plain = _MARK.sub("", s).strip(" -*#>")
        if not plain:
            continue
        if ns:
            items.append((plain, [ev_text[n - 1] for n in ns]))
            idx.append(i)
    fails: list[list[str]] = [[] for _ in sents]
    safe: list[str] = [s for _, s in sents]
    judged = judge_claims(matter_id, items, purpose="verify_chat") if items else []
    for (plain, quotes), i, j in zip(items, idx, judged):
        f = check_tokens(plain, Corpus("\n".join(quotes))) + list(j.unsupported)
        fails[i] = f
        if f:
            marks = "".join(dict.fromkeys(_MARK.findall(sents[i][1])))
            safe[i] = (j.supported_text.strip() + " " + "".join(f"[{m}]" for m in marks)).strip() \
                if j.supported_text.strip() and not check_tokens(j.supported_text, Corpus("\n".join(quotes))) else ""
    for i, (_, s) in enumerate(sents):  # uncited sentences may not carry specifics
        if i in idx:
            continue
        plain = _MARK.sub("", s)
        toks = check_tokens(plain, Corpus(""))
        if toks:
            fails[i] = [f"uncited specifics: {', '.join(toks)}"]
            safe[i] = ""
    return sents, fails, safe


def _rebuild(md: str, sents: list[tuple[int, str]], safe: list[str]) -> str:
    lines = md.split("\n")
    by_line: dict[int, list[str]] = {}
    for (li, _), s in zip(sents, safe):
        by_line.setdefault(li, []).append(s)
    out = []
    for li, line in enumerate(lines):
        if li not in by_line:
            out.append(line)
            continue
        kept = [s for s in by_line[li] if _MARK.sub("", s).strip(" -*#>")]  # drop marker-only leftovers
        if not kept:
            continue
        prefix = re.match(r"^\s*(?:[-*]|\d+\.)\s+", line)
        text = " ".join(kept)
        if prefix and not text.lstrip().startswith(prefix.group(0).strip()):
            text = prefix.group(0) + text.lstrip(" -*")
        out.append(text)
    return "\n".join(out).strip()


def chat(matter_id: str, req: ChatRequest) -> ChatResponse:
    msgs = [m for m in req.messages if m.content.strip()]
    if not msgs or msgs[-1].role != "user":
        raise ValueError("last message must be the user's question")
    question = msgs[-1].content.strip()
    prev_q = next((m.content for m in reversed(msgs[:-1]) if m.role == "user"), "")
    history = "\n".join(f"{m.role}: {m.content[:400]}" for m in msgs[-7:-1]) or "(none)"

    d = dash.cached(matter_id)
    passages = search(matter_id, question, top_k=8)
    if prev_q:
        seen = {(p.citation.source_id, p.citation.char_start) for p in passages}
        for p in search(matter_id, f"{prev_q} {question}", top_k=4):
            if (p.citation.source_id, p.citation.char_start) not in seen:
                passages.append(p)
    evidence: list[tuple[str, Citation]] = [(p.citation.quote[:3000], p.citation) for p in passages
                                           if p.citation.verified]
    if d:
        evidence += _dash_evidence(d)
    if not evidence:
        return ChatResponse(answer_markdown="Nothing in the synced case file answers this.", citations=[], links=[])
    providers = _providers(matter_id)

    ev_block = "\n\n".join(
        fence(i + 1, f'title="{c.source_title[:100]}" date="{c.date or ""}"', text, cap=3000)
        for i, (text, c) in enumerate(evidence))
    base = dict(today=date.today().isoformat(), history=history, evidence=ev_block,
                sections=", ".join(sorted(SECTIONS)),
                providers="; ".join(f"{cid}: {n}" for cid, n in providers) or "none", question=question)
    key = "chat:" + hashlib.sha256((VERSION + json.dumps([m.model_dump() for m in msgs]) + ev_block).encode()).hexdigest()[:24]
    with connect() as conn:
        row = conn.execute("SELECT payload_json FROM digests WHERE matter_id = ? AND kind = ?", (matter_id, key)).fetchone()
    if row:
        return ChatResponse.model_validate_json(row["payload_json"])

    ev_text = [f"{c.source_title}\n{t}" for t, c in evidence]
    out = structured(MODEL_OPUS, ChatOut, SYSTEM, PROMPT.format(**base, retry=""), purpose="chat",
                     matter_id=matter_id, effort="low", max_tokens=3000)
    sents, fails, safe = _verify(matter_id, out.answer_markdown, ev_text)
    if any(fails):
        listed = "\n".join(f"- \"{_MARK.sub('', s)[:120]}\": {', '.join(f)}" for (_, s), f in zip(sents, fails) if f)
        retry = ("\n\nYour previous answer had statements the cited evidence does not support. Answer again, "
                 f"stating only what the cited evidence says:\n{listed}")
        out = structured(MODEL_OPUS, ChatOut, SYSTEM, PROMPT.format(**base, retry=retry), purpose="chat_retry",
                         matter_id=matter_id, effort="low", max_tokens=3000)
        sents, fails, safe = _verify(matter_id, out.answer_markdown, ev_text)
    answer = _rebuild(out.answer_markdown, sents, safe) or "The case file does not clearly answer this."

    # Renumber to the cited subset; markers pointing nowhere are removed.
    used: list[int] = []
    for m in _MARK.findall(answer):
        n = int(m)
        if 1 <= n <= len(evidence) and n not in used:
            used.append(n)
    canon: dict[tuple, int] = {}  # identical citations collapse to one chip
    alias: dict[int, int] = {}
    for n in used:
        c = evidence[n - 1][1]
        alias[n] = canon.setdefault((c.source_id, c.page, c.char_start, c.char_end, c.quote[:200]), n)
    used = list(dict.fromkeys(alias[n] for n in used))
    remap = {old: new for new, old in enumerate(used, 1)}
    remap.update({n: remap[a] for n, a in alias.items()})
    answer = _MARK.sub(lambda m: f"[{remap[int(m.group(1))]}]" if int(m.group(1)) in remap else "", answer)
    answer = re.sub(r"(\[\d+\])(?:\1)+", r"\1", answer)  # [1][1] -> [1]
    citations = [evidence[n - 1][1] for n in used]

    # Validate every proposed link against what actually exists.
    tl_dates = {e.date for e in d.timeline} if d else set()
    pids = {cid for cid, _ in providers}
    links: list[DeepLink] = []
    for l in out.links:
        k = l.kind
        if k == "section" and l.section in SECTIONS:
            links.append(DeepLink(label=l.label, kind="section", section=l.section))
        elif k == "source" and l.evidence in remap and l.evidence in alias:
            links.append(DeepLink(label=l.label, kind="source", citation=evidence[l.evidence - 1][1]))
        elif k == "timeline" and l.date in tl_dates:
            links.append(DeepLink(label=l.label, kind="timeline", date=l.date))
        elif k == "share" and l.contact_id in pids:
            links.append(DeepLink(label=l.label, kind="share", contact_id=l.contact_id))
        elif k == "route" and l.path in ROUTES:
            links.append(DeepLink(label=l.label, kind="route", path=l.path))
        if len(links) >= MAX_LINKS:
            break

    resp = ChatResponse(answer_markdown=answer, citations=citations, links=links)
    with connect() as conn:
        conn.execute("INSERT OR REPLACE INTO digests (matter_id, kind, input_hash, payload_json, model, created_at)"
                     " VALUES (?, ?, ?, ?, ?, datetime('now'))", (matter_id, key, key, resp.model_dump_json(), MODEL_OPUS))
    return resp
