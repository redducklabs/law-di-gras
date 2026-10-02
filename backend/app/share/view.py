"""Share settings storage and the server-side ProviderView builder.

Everything the provider sees is filtered here. Rules (slide 10): status
changes, bills and records yes; strategy, attorney notes and unrelated
confidential material never. Concretely:
  - status line is a template over stage + dates, never the AI headline;
  - sections the attorney turned off are returned as null;
  - citations survive only when they point at a document the attorney shared,
    so no note/email text leaks through a quote;
  - requests and treatment are limited to this provider.
"""

import json
import re
import secrets
from datetime import date, datetime, timedelta, timezone

from app.db import connect
from app.schemas import (
    ActionItem, Citation, Dashboard, Fact, Provider, ProviderView, SharedDocument,
    ShareSections, ShareSettings, TimelineEvent, TreatmentLine,
)
from app.share.providers import contact_key, list_providers, load_dashboard, matches_provider, names_match

ACTIVE_STATUSES = {"open", "pending"}
# Timeline kinds a provider may see (communications can carry strategy).
PROVIDER_TIMELINE_KINDS = {"incident", "treatment", "legal", "deadline"}
# "Since you last checked": past case milestones only (future deadlines are firm tasks).
UPDATE_KINDS = {"incident", "treatment", "legal"}
UPDATES_FALLBACK_DAYS = 30


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# ---------- settings ----------

def last_viewed(token: str | None) -> str | None:
    if not token:
        return None
    with connect() as conn:
        row = conn.execute("SELECT MAX(viewed_at) AS v FROM share_views WHERE token=?", (token,)).fetchone()
    return row["v"] if row else None


def get_settings(matter_id: str, contact_id: str) -> ShareSettings:
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM share_settings WHERE matter_id=? AND contact_id=?", (matter_id, contact_id)
        ).fetchone()
    if not row:
        return ShareSettings(contact_id=contact_id)
    return ShareSettings(
        contact_id=contact_id,
        sections=ShareSections.model_validate_json(row["sections_json"] or "{}"),
        source_ids=json.loads(row["source_ids_json"] or "[]"),
        token=row["token"],
        last_viewed_at=last_viewed(row["token"]),
    )


def save_settings(matter_id: str, contact_id: str, s: ShareSettings) -> ShareSettings:
    existing = get_settings(matter_id, contact_id)
    token = existing.token or secrets.token_urlsafe(18)  # stable link once minted
    shareable = {d["id"] for d in matter_documents(matter_id)}
    source_ids = [sid for sid in s.source_ids if sid in shareable]
    with connect() as conn:
        conn.execute(
            """INSERT INTO share_settings(matter_id, contact_id, sections_json, source_ids_json, token, updated_at)
               VALUES(?,?,?,?,?,?)
               ON CONFLICT(matter_id, contact_id) DO UPDATE SET
                 sections_json=excluded.sections_json, source_ids_json=excluded.source_ids_json,
                 token=excluded.token, updated_at=excluded.updated_at""",
            (matter_id, contact_id, s.sections.model_dump_json(), json.dumps(source_ids), token, _now()),
        )
    return get_settings(matter_id, contact_id)


def settings_by_token(token: str) -> tuple[str, ShareSettings] | None:
    with connect() as conn:
        row = conn.execute("SELECT matter_id, contact_id FROM share_settings WHERE token=?", (token,)).fetchone()
    if not row:
        return None
    return row["matter_id"], get_settings(row["matter_id"], row["contact_id"])


def log_view(token: str, user_agent: str | None) -> None:
    with connect() as conn:
        conn.execute("INSERT INTO share_views(token, viewed_at, user_agent) VALUES(?,?,?)",
                     (token, _now(), (user_agent or "")[:300]))


# ---------- documents ----------

def matter_documents(matter_id: str) -> list[dict]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT id, title, date FROM sources WHERE matter_id=? AND kind='document' ORDER BY date DESC, title",
            (matter_id,),
        ).fetchall()
    return [dict(r) for r in rows]


def documents_for_panel(matter_id: str, provider: Provider | None, dash: Dashboard | None) -> list[dict]:
    """All matter documents, with the ones tied to this provider flagged as suggested."""
    cited: set[str] = set()
    if provider and dash:
        for t in _provider_treatment(dash, provider):
            cited |= {c.source_id for c in t.citations}
            if t.billed:
                cited |= {c.source_id for c in t.billed.citations}
    docs = []
    for d in matter_documents(matter_id):
        suggested = d["id"] in cited or bool(provider and matches_provider(provider, d["title"]))
        docs.append({**d, "suggested": suggested})
    return sorted(docs, key=lambda d: (not d["suggested"], d["title"] or ""))


# ---------- view ----------

def _keep_citations(cits: list[Citation], allowed: set[str]) -> list[Citation]:
    return [c for c in cits if c.source_kind == "document" and c.source_id in allowed]


def _fact(f: Fact, allowed: set[str]) -> Fact:
    return f.model_copy(update={"citations": _keep_citations(f.citations, allowed)})


def _provider_treatment(dash: Dashboard, provider: Provider) -> list[TreatmentLine]:
    """Treatment lines for this provider: contact id, then own name, then a role alias
    (an alias match loses to any other provider whose own name matches)."""
    key = contact_key(provider.contact_id)
    others = [p for p in list_providers(dash.matter.id) if p.contact_id != provider.contact_id]
    out = []
    for t in dash.treatment:
        if t.contact_id:
            if contact_key(t.contact_id) == key:
                out.append(t)
            continue
        if names_match(provider.name, t.provider):
            out.append(t)
        elif matches_provider(provider, t.provider) and not any(names_match(o.name, t.provider) for o in others):
            out.append(t)
    return out


_OWED_BY = re.compile(r"^\s*by\s+([^:]{2,80}):\s*([^\-–—(]+)?", re.I)


def _owed_by(title: str) -> list[str]:
    """Who owes an item, from the 'By <party>: ...' convention. Also covers
    'By medical provider: <party> - ...' by returning the head after the colon."""
    m = _OWED_BY.match(title or "")
    return [g.strip() for g in m.groups() if g and g.strip()] if m else []


def _provider_requests(dash: Dashboard, provider: Provider) -> list[ActionItem]:
    """Items the firm is waiting on this provider for: waiting_on, or the 'By <party>:' title
    convention. Internal tasks that merely mention the provider never qualify."""
    return [a for a in dash.actions
            if matches_provider(provider, a.waiting_on) or any(matches_provider(provider, p) for p in _owed_by(a.title))]


def _provider_liens(dash: Dashboard, provider: Provider) -> list[Fact]:
    return [f for f in (dash.kpis.liens or [])
            if matches_provider(provider, f.label)]  # lien holder name only


def _last_activity(matter_id: str) -> str | None:
    today = date.today().isoformat()
    with connect() as conn:
        row = conn.execute(
            "SELECT MAX(substr(date,1,10)) AS d FROM sources WHERE matter_id=? AND date IS NOT NULL AND substr(date,1,10)<=?",
            (matter_id, today),
        ).fetchone()
    return row["d"] if row else None


def _fmt_date(d: str | None) -> str | None:
    if not d:
        return None
    try:
        dt = date.fromisoformat(d[:10])
        return f"{dt:%b} {dt.day}, {dt.year}"
    except ValueError:
        return d


def _updates(dash: Dashboard | None, since: str | None, allowed: set[str]) -> tuple[list[TimelineEvent], str]:
    """Major past milestones after `since`; if none, the last 30 days. Returns (events, cutoff date)."""
    today = date.today().isoformat()
    fallback = (date.today() - timedelta(days=UPDATES_FALLBACK_DAYS)).isoformat()

    def pick(cutoff: str) -> list[TimelineEvent]:
        return [
            TimelineEvent(date=e.date, label=e.label, kind=e.kind, is_future=False, major=True,
                          citations=_keep_citations(e.citations, allowed))
            for e in sorted(dash.timeline if dash else [], key=lambda e: e.date, reverse=True)
            if e.major and e.kind in UPDATE_KINDS and not e.is_future and cutoff < e.date[:10] <= today
        ]

    if since:
        events = pick(since[:10])
        if events or since[:10] <= fallback:
            return events, since[:10]
    return pick(fallback), fallback


def build_view(matter_id: str, provider: Provider, s: ShareSettings, since: str | None = None) -> ProviderView:
    """since: this link's previous view (ISO); updates fall back to the last 30 days."""
    with connect() as conn:
        m = conn.execute("SELECT * FROM matters WHERE id=?", (matter_id,)).fetchone()
    dash = load_dashboard(matter_id)
    if not m and not dash:
        raise LookupError("matter not found")

    matter_title = (dash.matter.title if dash else None) or (m["description"] if m else "") or ""
    client_name = (dash.matter.client_name if dash else None) or (m["client_name"] if m else "") or ""
    status = (dash.matter.status if dash else None) or (m["status"] if m else "") or ""
    case_active = status.strip().lower() in ACTIVE_STATUSES
    stage = (dash.headline.stage if dash else "") or status or "Open"
    last = _last_activity(matter_id)

    sec = s.sections
    allowed = set(s.source_ids) if sec.documents else set()

    if sec.status:
        parts = [f"Case is {'active' if case_active else 'closed'}", f"current stage: {stage}"]
        if last:
            parts.append(f"last activity on the file {_fmt_date(last)}")
        status_line = "; ".join(parts) + "."
    else:
        status_line = f"Case is {'active' if case_active else 'closed'}."

    view = ProviderView(
        matter_title=matter_title,
        client_name=client_name,
        provider_name=provider.name,
        stage=stage if sec.status else "",
        status_line=status_line,
        case_active=case_active,
        last_activity_date=last if sec.status else None,
    )
    # Sections the attorney enabled are always lists (empty before the digest exists).
    view.coverage = [] if sec.coverage else None
    view.requests = [] if sec.requests else None
    view.treatment = [] if sec.treatment else None
    view.liens = [] if sec.treatment else None
    view.timeline = [] if sec.timeline else None
    if dash:
        if sec.coverage:
            view.coverage = [_fact(f, allowed) for f in dash.kpis.coverage]
        if sec.requests:
            view.requests = [a.model_copy(update={"citations": _keep_citations(a.citations, allowed)})
                             for a in _provider_requests(dash, provider)]
        if sec.treatment:
            view.treatment = [t.model_copy(update={
                "citations": _keep_citations(t.citations, allowed),
                "billed": _fact(t.billed, allowed) if t.billed else None,
            }) for t in _provider_treatment(dash, provider)]
            view.liens = [_fact(f, allowed) for f in _provider_liens(dash, provider)]
        if sec.timeline:
            view.timeline = [
                TimelineEvent(date=e.date, label=e.label, kind=e.kind, is_future=e.is_future, major=e.major,
                              citations=_keep_citations(e.citations, allowed))
                for e in dash.timeline if e.kind in PROVIDER_TIMELINE_KINDS
            ]
    if sec.status:
        view.updates, view.updates_since = _updates(dash, since, allowed)
    if sec.documents:
        titles = {d["id"]: d["title"] for d in matter_documents(matter_id)}
        view.documents = [SharedDocument(source_id=sid, title=titles[sid] or sid)
                          for sid in s.source_ids if sid in titles]
    return view
