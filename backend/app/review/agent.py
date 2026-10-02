"""Agent loop: Opus reviews the whole Sapini file like a senior partner and submits cited findings.

Tools are read-only over our SQLite (search, read a source). `submit_finding` verifies on the
spot (verbatim quotes, token check, Sonnet claim judge) and tells the agent what failed, so the
agent can fix and resubmit once. Only verified findings are kept.
"""

import os
import re
import time
from datetime import date, datetime, timezone

import anthropic

from app.db import connect
from app.digest import dashboard
from app.digest.spans import locate
from app.digest.verify import Corpus, check_tokens, judge_claims
from app.llm import MODEL_OPUS, client, log_usage
from app.retrieval.fence import FENCE_RULE, clean, fence
from app.retrieval.search import search_hits
from app.review.checks import overreach, record_cites, same_source
from app.schemas import CaseReview, Citation, Dashboard, ReviewFinding

MAX_TURNS = int(os.getenv("REVIEW_MAX_TURNS", "40"))  # small values make a short test run
EXPECTED_TURNS = min(MAX_TURNS, 26)  # typical full run, for the progress bar
MAX_COST = 3.00
MAX_FINDINGS = 10
SEVERITY = {"high": 0, "medium": 1, "low": 2}
CATEGORIES = ["conflict", "gap", "stale", "risk", "inconsistency", "opportunity"]

SYSTEM = f"""You are a senior personal-injury trial partner doing a file review of one matter for the team.
The team already has a dashboard that lists the case item by item. Your job is to find what they miss
when they look item by item: the things that only show up when you read the whole file together.

Look for, at least:
- conflict: the record disagrees with itself (amounts, coverage, dates, who said what).
- inconsistency: client or witness accounts, mechanism, prior injuries or dates that don't line up.
- gap: something a PI file should have and this one doesn't (a key witness never interviewed or deposed,
  a record never obtained, an authorization never served, a scheduled event with no record it happened).
- stale: an open thread nobody has touched in a long time (unanswered requests, promised follow-ups).
- risk: coverage, policy limits, liens, collateral sources, deadlines, liability defenses, treatment gaps,
  defense experts versus treating findings.
- opportunity: leverage or damages the file supports that the demand or valuation does not use.

Rules:
- Every factual statement must come from the record and be backed by a VERBATIM quote (copied exactly,
  10-300 characters, from one place in one source) in `evidence`. Use search_record and read_source to
  find and copy quotes; never quote from memory or paraphrase inside a quote.
- No legal citations (statutes, rules, cases) unless quoted from the record.
- Absence claims ("nobody contacted X") are allowed only after you actually ran search_record for it.
  Phrase them exactly as "No record found of ...", list the queries you ran in `searched_for`, and cite
  the closest evidence (for example the document that names the witness).
- `facts`: 1-4 short factual statements, each fully supported by your quotes. They are checked one by one
  by a strict judge that sees only your quotes. The title must be a plain summary of these facts.
- `title`: one plain-language line of at most 16 words, supported by the quotes (or a "No record found of ..." line). The
  title and facts are checked strictly against the quotes: state what the quotes say, and put the
  connection or inference ("yet", "but the file still ...", "which means ...") in why_it_matters.
- No exclusivity or superlatives ("only", "never", "nobody", "sole") unless a quote says so, and no
  upcoming or scheduled event unless a cited calendar entry, task or quote shows it is scheduled.
- A conflict must hold up against the rest of the same documents; it is checked against their full text.
- Attribute a quote only as its source identifies itself (the checker sees each quote's source title).
- `why_it_matters`: one or two sentences of analysis for the attorney. Introduce no new dates, amounts or
  names that are not in your quotes.
- `suggested_next_step`: one concrete action the team can take this week.
- Do not repeat what the dashboard already says unless you add the connection the dashboard misses.
- Cover the spread: aim for a mix of categories (including stale threads, lien/coverage/deadline risk and
  unused damages or leverage) and severities, not only the top conflicts.
- Submit findings in parallel (several submit_finding calls in one turn) to save rounds.
- Quality over count: 6 to 10 findings a trial attorney would actually act on. Severity "high" only for
  things that can change the case outcome or value.
- submit_finding tells you if a finding failed verification and why. Fix it and resubmit (up to twice), or drop it.
- Work efficiently: you have about {MAX_TURNS - 5} tool rounds. You may call several tools in parallel.
  When you have submitted your findings, reply with a one-line summary and stop.

Output is a draft for attorney review. {FENCE_RULE}"""

TOOLS = [
    {
        "name": "search_record",
        "description": "Hybrid search (keyword + semantic) over every note, email, task, calendar entry and "
                       "document page in the matter. Returns the best passages with source_id and page.",
        "strict": True,
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "What to look for, in plain words."},
                "k": {"type": "integer", "description": "Number of passages, 1-10."},
            },
            "required": ["query", "k"],
            "additionalProperties": False,
        },
    },
    {
        "name": "read_source",
        "description": "Full text of one source. For a multi-page document pass `page` (1-based); with page "
                       "null you get a one-line index of every page plus page 1.",
        "strict": True,
        "input_schema": {
            "type": "object",
            "properties": {
                "source_id": {"type": "string"},
                "page": {"type": ["integer", "null"]},
            },
            "required": ["source_id", "page"],
            "additionalProperties": False,
        },
    },
    {
        "name": "submit_finding",
        "description": "Record one finding. It is verified immediately: every quote must be found verbatim in "
                       "its source, and title + facts are checked against the quotes. Returns accepted or "
                       "the reasons it was rejected.",
        "strict": True,
        "input_schema": {
            "type": "object",
            "properties": {
                "category": {"type": "string", "enum": CATEGORIES},
                "severity": {"type": "string", "enum": ["high", "medium", "low"]},
                "title": {"type": "string"},
                "facts": {"type": "array", "items": {"type": "string"}},
                "why_it_matters": {"type": "string"},
                "suggested_next_step": {"type": "string"},
                "evidence": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "source_id": {"type": "string"},
                            "page": {"type": ["integer", "null"]},
                            "quote": {"type": "string"},
                        },
                        "required": ["source_id", "page", "quote"],
                        "additionalProperties": False,
                    },
                },
                "searched_for": {"type": "array", "items": {"type": "string"},
                                 "description": "search_record queries you ran (absence claims only), else []."},
            },
            "required": ["category", "severity", "title", "facts", "why_it_matters", "suggested_next_step",
                         "evidence", "searched_for"],
            "additionalProperties": False,
        },
    },
]


# --- context ---------------------------------------------------------------

def _cits(cs: list[Citation]) -> str:
    ids = list(dict.fromkeys(c.source_id for c in cs if c.verified))[:3]
    return f" [{', '.join(ids)}]" if ids else ""


def _brief_text(d: Dashboard) -> str:
    """The dashboard the team already sees, compact, with source ids."""
    L = [f"Stage: {d.headline.stage}. Status: {d.headline.status_line}{_cits(d.headline.status_citations)}"]
    for f in d.headline.bullets:
        L.append(f"- {f.label}: {f.value}{_cits(f.citations)}")
    k = d.kpis
    for f in [k.specials, k.firm_spent, k.case_value, *k.coverage, *k.liens, d.last_client_contact]:
        if f:
            L.append(f"KPI {f.label}: {f.value}{_cits(f.citations)}")
    for a in d.actions:
        L.append(f"Action ({a.status}{', due ' + a.due_date if a.due_date else ''}"
                 f"{', waiting on ' + a.waiting_on if a.waiting_on else ''}): {a.title}{_cits(a.citations)}")
    for f in d.injuries:
        L.append(f"Injury {f.label}: {f.value}{_cits(f.citations)}")
    for t in d.treatment:
        L.append(f"Treatment {t.provider}: first {t.first_visit}, last {t.last_visit}, next {t.next_visit}, "
                 f"visits {t.visit_count}, billed {t.billed.value if t.billed else '?'}")
    for e in d.timeline:
        L.append(f"Timeline {e.date}{' (future)' if e.is_future else ''}: {e.label}{_cits(e.citations)}")
    return "\n".join(L)


def _record_text(matter_id: str) -> str:
    """Every short source in full (notes, emails, tasks, calendar, expenses, fields, contacts) plus an
    index of documents. Document pages are read through read_source."""
    with connect() as conn:
        rows = conn.execute("SELECT id, kind, title, date, author, text, page_count FROM sources"
                            " WHERE matter_id = ? ORDER BY kind, date, id", (matter_id,)).fetchall()
    short, docs = [], []
    for r in rows:
        if r["kind"] == "document":
            first = re.sub(r"\s+", " ", (r["text"] or "")[:200]).strip()
            docs.append(f"- {r['id']} | {(r['date'] or '')[:10]} | {r['title']} | {r['page_count']} pages | "
                        f"{r['author'] or ''} | starts: {first}")
        else:
            short.append(fence(r["id"], f'kind="{r["kind"]}" date="{(r["date"] or "")[:10]}"', r["text"] or "", 4000))
    return "DOCUMENTS (read with read_source):\n" + "\n".join(docs) + "\n\nALL OTHER RECORDS:\n" + "\n".join(short)


# --- tools -----------------------------------------------------------------

class Session:
    def __init__(self, matter_id: str):
        self.matter_id = matter_id
        self.searched: list[str] = []
        self.findings: list[ReviewFinding] = []
        self.rejected = 0
        with connect() as conn:
            rows = conn.execute("SELECT title, text FROM sources WHERE matter_id = ? AND kind IN"
                                " ('contact', 'matter')", (matter_id,)).fetchall()
            titles = conn.execute("SELECT title FROM sources WHERE matter_id = ?", (matter_id,)).fetchall()
        self.names = Corpus("\n".join([f"{r['title']}\n{r['text'] or ''}" for r in rows] +
                                      [t["title"] or "" for t in titles]))

    def search_record(self, query: str, k: int) -> str:
        self.searched.append(query)
        hits = search_hits(self.matter_id, query, top_k=max(1, min(k, 10)))
        if not hits:
            return "No passages matched."
        return "\n".join(fence(h.source_id, f'title="{h.title[:90]}" page="{h.page_no}"', h.text, 1500) for h in hits)

    def read_source(self, source_id: str, page: int | None) -> str:
        with connect() as conn:
            src = conn.execute("SELECT id, kind, title, date, text, page_count FROM sources WHERE id = ? AND"
                               " matter_id = ?", (source_id, self.matter_id)).fetchone()
            if src is None:
                return f"Unknown source_id {source_id}."
            pages = conn.execute("SELECT page_no, text FROM pages WHERE source_id = ? ORDER BY page_no",
                                 (source_id,)).fetchall()
        head = f'title="{src["title"]}" date="{(src["date"] or "")[:10]}"'
        if not pages:
            return fence(source_id, head, src["text"] or "", 12000)
        by = {p["page_no"]: p["text"] or "" for p in pages}
        if page is not None:
            if page not in by:
                return f"{source_id} has pages 1-{len(pages)}."
            return fence(source_id, head + f' page="{page}" of="{len(pages)}"', by[page], 12000)
        index = "\n".join(f"p{n}: {_gist(t)}" for n, t in by.items())
        return (f"{len(pages)} pages. Index:\n{clean(index, 15000)}\n\n" +
                fence(source_id, head + ' page="1"', by.get(1, ""), 8000))

    def submit_finding(self, f: dict) -> str:
        if len(self.findings) >= MAX_FINDINGS:
            return f"Rejected: you already have {MAX_FINDINGS} findings. Stop and summarize."
        problems: list[str] = []
        cits: list[Citation] = []
        with connect() as conn:
            for ev in f.get("evidence") or []:
                c = locate(conn, ev["source_id"], ev["quote"], ev.get("page"))
                if c is None:
                    problems.append(f"unknown source_id {ev['source_id']}")
                elif not c.verified:
                    problems.append(f"quote not found verbatim in {ev['source_id']}: \"{ev['quote'][:80]}\"")
                elif not any(x.source_id == c.source_id and x.char_start == c.char_start and x.page == c.page
                             for x in cits):
                    cits.append(c)
        if not cits:
            problems.append("no verified quote")
        absence = any("no record" in s.lower() for s in [f["title"], *f["facts"]])
        searched = [q for q in f.get("searched_for") or [] if q in self.searched]
        if absence and not searched:
            problems.append("absence claim without a search_record query you actually ran in searched_for")
        if problems:
            self.rejected += 1
            return "Rejected: " + "; ".join(problems)

        quotes = [f"[{_pretty(c.source_title)}{', ' + c.date[:10] if c.date else ''}] {c.quote}" for c in cits]
        if absence:
            quotes.append("[search log] The whole case file was searched for: " +
                          "; ".join(f'"{q}"' for q in searched) + ". Results are what the quotes above show.")
        corpus = Corpus("\n".join(quotes))
        for label, text in [("title", f["title"]), ("why_it_matters", f["why_it_matters"]),
                            ("suggested_next_step", f["suggested_next_step"]), *[("fact", x) for x in f["facts"]]]:
            bad = check_tokens(text, corpus, self.names)
            bad = [b for b in bad if not self._known_name(b, corpus)]
            if label in ("why_it_matters", "suggested_next_step"):  # analysis/action: only dates and amounts must trace
                bad = [b for b in bad if _DATE_OR_MONEY.search(b)]
            if bad:
                problems.append(f"{label} has tokens not in your quotes: {bad}")
        legal = unsourced_legal_cites([f["title"], f["why_it_matters"], f["suggested_next_step"], *f["facts"]], cits)
        if legal:
            problems.append(f"legal citations not inside any of your quotes (quote the span that states the rule, or remove it): {legal}")
        problems += overreach([f["title"], f["why_it_matters"], f["suggested_next_step"], *f["facts"]],
                              "\n".join(quotes), cits)
        if not problems:
            claims = list(f["facts"])  # title/analysis are token-checked; every fact is judged
            judged = judge_claims(self.matter_id, [(c, quotes) for c in claims], "review_verify")
            for c, j in zip(claims, judged):
                if j.unsupported:
                    problems.append(f'"{c[:80]}" unsupported parts: {j.unsupported}')
        if not problems and f["category"] in ("conflict", "inconsistency"):
            p = same_source(self.matter_id, "\n".join([f["title"], *f["facts"]]), cits)
            if p:
                problems.append(p)
        if not problems:
            extra, ps = record_cites(self.matter_id, list(f["facts"]), cits)
            problems += ps
            cits = cits + extra
        if problems:
            self.rejected += 1
            return "Rejected: " + "; ".join(problems) + ". Fix (better quotes, or narrower wording) and resubmit once."

        n = len(self.findings) + 1
        self.findings.append(ReviewFinding(
            id=f"bs{n}", category=f["category"], severity=f["severity"], title=f["title"].strip(),
            why_it_matters=f["why_it_matters"].strip(), suggested_next_step=f["suggested_next_step"].strip(),
            citations=cits, verified=True))
        return f"Accepted as bs{n} ({len(cits)} verified citations)."

    def _known_name(self, tok: str, corpus: Corpus) -> bool:
        """'Mr. Ferrara', "Ferrara's" → a surname the quotes or contacts contain. Dates/amounts never pass."""
        if re.search(r"\d|\$", tok):
            return False
        words = [w for w in re.sub(r"'s\b|’s\b", "", tok).split()
                 if w.lower().strip(".,") not in ("mr", "ms", "mrs", "dr", "the")]
        return bool(words) and all(corpus.has(w) or self.names.has(w) for w in words)

    def run_tool(self, name: str, inp: dict) -> str:  # noqa: D102
        if name == "search_record":
            return self.search_record(inp["query"], inp.get("k") or 6)
        if name == "read_source":
            return self.read_source(inp["source_id"], inp.get("page"))
        if name == "submit_finding":
            return self.submit_finding(inp)
        return f"Unknown tool {name}"


def _pretty(t: str) -> str:
    """'03-discovery__doc-40__defendants-response-demand.pdf' -> 'defendants response demand (03 discovery)'."""
    m = re.match(r"^(\d+-[a-z-]+)__(?:doc-\d+__|created__)?(.+?)\.\w+$", t or "")
    return f"{m.group(2).replace('-', ' ')} ({m.group(1).replace('-', ' ')})" if m else t


_LEGAL = re.compile(r"(?:§+|\bCPLR\b|\bsection\b|\bRule\b)\s*(\d+[\w.()-]*)|\b\w+ v\.? \w+", re.I)


def unsourced_legal_cites(texts: list[str], cits: list[Citation]) -> list[str]:
    """Statute/rule/case cites in the text whose number (or name) is not inside a cited QUOTE.
    No legal citations from model memory, and the highlighted span must show the rule itself."""
    blob = "\n".join(c.quote for c in cits if c.verified)
    bad = []
    for t in texts:
        for m in _LEGAL.finditer(t):
            key = m.group(1) or m.group(0)
            if key not in blob:
                bad.append(m.group(0))
    return list(dict.fromkeys(bad))


_DATE_OR_MONEY = re.compile(r"\$|\d{1,4}[-/]\d{1,2}|\b(19|20)\d{2}\b")
_HDR = re.compile(r"^(FILED:|INDEX NO|NYSCEF|RECEIVED NYSCEF|SUPREME COURT|COUNTY OF|-{5,})", re.I)


def _gist(t: str) -> str:
    """One line per page for the index: the page text minus the court-filing header."""
    lines = [ln for ln in (t or "").splitlines() if ln.strip() and not _HDR.match(ln.strip())]
    return re.sub(r"\s+", " ", " ".join(lines))[:140].strip()


# --- loop ------------------------------------------------------------------

def _cost(u) -> tuple[int, float]:
    """(input tokens priced as full input, USD) for one Opus response, cache writes/reads included."""
    eff = (u.input_tokens + 1.25 * (u.cache_creation_input_tokens or 0) + 0.1 * (u.cache_read_input_tokens or 0))
    return int(eff), (eff * 4.0 + u.output_tokens * 20.0) / 1_000_000


def _noop(stage: str, pct: int) -> None:
    pass


def run(matter_id: str, log=print, progress=_noop) -> CaseReview:
    progress("Reading the record", 3)
    d = dashboard.cached(matter_id)
    if d is None:
        raise LookupError("no dashboard yet for this matter")
    s = Session(matter_id)
    user = (f"Today is {date.today().isoformat()}. Matter: {d.matter.title} ({d.matter.display_number}), "
            f"client {d.matter.client_name}.\n\nWHAT THE DASHBOARD ALREADY SHOWS:\n{_brief_text(d)}\n\n"
            f"THE RECORD:\n{_record_text(matter_id)}\n\n"
            "Review the whole file now. Read the key documents you need (pleadings, discovery responses, "
            "the subpoena, the expert reports, bills) and submit your findings.")
    messages: list = [{"role": "user", "content": user}]
    progress("Reviewing the file", 8)
    cost, t0 = 0.0, time.time()
    for turn in range(MAX_TURNS):
        try:
            resp = client().messages.create(
                model=MODEL_OPUS, max_tokens=16000, system=SYSTEM, tools=TOOLS, messages=messages,
                thinking={"type": "adaptive"}, output_config={"effort": "high"},
                cache_control={"type": "ephemeral"}, tool_choice={"type": "auto"})
        except (anthropic.RateLimitError, anthropic.APIConnectionError, anthropic.InternalServerError) as e:
            log(f"turn {turn}: transient {type(e).__name__}, retrying")
            time.sleep(5)
            continue
        eff_in, c = _cost(resp.usage)
        cost += c
        log_usage(MODEL_OPUS, "review", eff_in, resp.usage.output_tokens, matter_id)
        messages.append({"role": "assistant", "content": resp.content})
        uses = [b for b in resp.content if b.type == "tool_use"]
        log(f"turn {turn}: {resp.stop_reason}, {len(uses)} tools "
            f"[{', '.join(b.name for b in uses)}], ${cost:.2f}, {time.time() - t0:.0f}s, "
            f"{len(s.findings)} findings")
        progress(f"Reviewing the file (round {turn + 1}, {len(s.findings)} verified findings)",
                 8 + int(80 * min(1.0, (turn + 1) / EXPECTED_TURNS)))
        if resp.stop_reason != "tool_use" or not uses:
            break
        results = []
        for b in uses:
            try:
                out = s.run_tool(b.name, b.input)
            except Exception as e:  # a bad tool call should not end the review
                out = f"Tool error: {e}"
            if b.name == "submit_finding":
                log(f"  submit [{b.input.get('severity')}/{b.input.get('category')}] {b.input.get('title')}: {out[:300]}")
            results.append({"type": "tool_result", "tool_use_id": b.id, "content": out})
            if b.name == "submit_finding":
                progress(f"Verifying findings ({len(s.findings)} accepted)", 0)
        if turn >= MAX_TURNS - 4 or cost > MAX_COST:
            results.append({"type": "text", "text": "Budget nearly exhausted: submit any remaining findings "
                                                    "now, then stop."})
        if cost > MAX_COST * 1.3:
            break
        messages.append({"role": "user", "content": results})

    progress("Verifying findings", 90)
    judge_cost = _judge_cost(matter_id, t0)
    findings = sorted(s.findings, key=lambda f: SEVERITY[f.severity])
    for i, f in enumerate(findings, 1):
        f.id = f"bs{i}"
    log(f"done: {len(findings)} findings, {s.rejected} rejections, ${cost + judge_cost:.2f}, {time.time() - t0:.0f}s")
    return CaseReview(matter_id=matter_id, generated_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
                      cost_usd=round(cost + judge_cost, 4), model=MODEL_OPUS, findings=findings)


def _judge_cost(matter_id: str, since: float) -> float:
    ts = datetime.fromtimestamp(since, timezone.utc).isoformat()
    with connect() as conn:
        row = conn.execute("SELECT COALESCE(SUM(cost_usd), 0) FROM llm_usage WHERE matter_id = ? AND"
                           " purpose = 'review_verify' AND created_at >= ?", (matter_id, ts)).fetchone()
    return float(row[0])


# --- cache -----------------------------------------------------------------

KIND = "review"


def cached(matter_id: str) -> CaseReview | None:
    with connect() as conn:
        row = conn.execute("SELECT payload_json FROM digests WHERE matter_id = ? AND kind = ?",
                           (matter_id, KIND)).fetchone()
    return CaseReview.model_validate_json(row["payload_json"]) if row else None


def build(matter_id: str, force: bool = False, log=print, progress=_noop) -> CaseReview:
    """Cached by the dashboard input hash; runs the agent only when the record changed or force."""
    h = dashboard.input_hash(matter_id)
    with connect() as conn:
        row = conn.execute("SELECT input_hash, payload_json FROM digests WHERE matter_id = ? AND kind = ?",
                           (matter_id, KIND)).fetchone()
    if row and row["input_hash"] == h and not force:
        return CaseReview.model_validate_json(row["payload_json"])
    review = run(matter_id, log, progress)
    progress("Saving", 97)
    if not review.findings and row:
        raise RuntimeError("the review produced no verified findings; previous review kept")
    with connect() as conn:
        conn.execute("INSERT OR REPLACE INTO digests (matter_id, kind, input_hash, payload_json, model, created_at)"
                     " VALUES (?, ?, ?, ?, ?, ?)", (matter_id, KIND, h, review.model_dump_json(), MODEL_OPUS,
                                                    review.generated_at))
    return review
