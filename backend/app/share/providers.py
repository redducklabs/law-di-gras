"""Find the treating medical providers on a matter.

Reads S1's `sources` rows (kind='contact', raw Clio JSON kept) and the cached
Dashboard's treatment lines. Generic keyword matching only; no case content.
"""

import json
import re

from app.db import connect
from app.schemas import Dashboard, Provider

# Words that mark a Clio contact, relationship or custom field as medical.
MEDICAL_WORDS = (
    "medical", "physician", "doctor", "dr.", "md", "d.c.", "chiropract", "clinic",
    "hospital", "health", "therap", "rehab", "orthop", "radiolog", "imaging",
    "mri", "surgery", "surgical", "neurolog", "pain", "urgent care", "provider",
    "treating", "ambulance", "emergency", "pharmac", "acupunct", "spine",
)
# Contacts that are clearly not providers even if a medical word appears.
NOT_PROVIDER_WORDS = ("insurance", "adjuster", "attorney", "law firm", "lawyer", "esq", "court", "defendant")

_word_re = {w: re.compile(r"(?<![a-z])" + re.escape(w) + r"(?![a-z])") for w in MEDICAL_WORDS}


def _has_medical_word(text: str) -> bool:
    t = text.lower()
    return any(r.search(t) for r in _word_re.values())


def norm_name(name: str) -> str:
    t = re.sub(r"[^a-z0-9 ]", " ", (name or "").lower())
    t = re.sub(r"\b(dr|md|do|dc|pc|llc|inc|pllc|the|of|and)\b", " ", t)
    return " ".join(t.split())


def names_match(a: str, b: str) -> bool:
    """Loose match between a contact name and a provider name from the digest."""
    na, nb = norm_name(a), norm_name(b)
    if not na or not nb:
        return False
    if na in nb or nb in na:
        return True
    ta, tb = set(na.split()), set(nb.split())
    overlap = ta & tb
    return len(overlap) >= 2 or (len(overlap) == 1 and min(len(ta), len(tb)) == 1 and len(next(iter(overlap))) > 3)


def contact_key(contact_id: str | None) -> str:
    """Normalize 'contact:123' and '123' to the same key."""
    return (contact_id or "").split(":", 1)[-1]


def _role_from(raw: dict, text: str) -> str | None:
    for key in ("relationship", "role", "description"):
        v = raw.get(key)
        if isinstance(v, str) and v.strip():
            return v.strip()
        if isinstance(v, dict) and isinstance(v.get("description"), str):
            return v["description"].strip()
    rels = raw.get("relationships")
    if isinstance(rels, list):
        for r in rels:
            if isinstance(r, dict) and r.get("description"):
                return str(r["description"]).strip()
    return None


def load_dashboard(matter_id: str) -> Dashboard | None:
    with connect() as conn:
        row = conn.execute(
            "SELECT payload_json FROM digests WHERE matter_id=? AND kind='dashboard'", (matter_id,)
        ).fetchone()
    if not row:
        return None
    try:
        return Dashboard.model_validate_json(row["payload_json"])
    except Exception:
        return None


def list_providers(matter_id: str) -> list[Provider]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT id, title, text, raw_json FROM sources WHERE matter_id=? AND kind='contact' ORDER BY title",
            (matter_id,),
        ).fetchall()
    dash = load_dashboard(matter_id)
    treated = [t.provider for t in (dash.treatment if dash else [])]
    treated_ids = {contact_key(t.contact_id) for t in (dash.treatment if dash else []) if t.contact_id}

    out: list[Provider] = []
    seen: set[str] = set()
    for r in rows:
        try:
            raw = json.loads(r["raw_json"] or "{}")
        except Exception:
            raw = {}
        name = r["title"] or raw.get("name") or ""
        blob = " ".join([name, r["text"] or "", r["raw_json"] or ""])
        role = _role_from(raw, blob)
        cid = contact_key(r["id"])
        in_treatment = cid in treated_ids or any(names_match(name, t) for t in treated)
        role_blob = " ".join(filter(None, [name, role or ""])).lower()
        excluded = any(w in role_blob for w in NOT_PROVIDER_WORDS)
        if excluded and not in_treatment:
            continue
        if in_treatment or _has_medical_word(blob):
            out.append(Provider(contact_id=r["id"], name=name, role=role))
            seen.add(norm_name(name))

    # Fallback: providers named in treatment facts with no matching contact.
    for t in dash.treatment if dash else []:
        if not any(names_match(t.provider, s) for s in seen):
            out.append(Provider(contact_id=f"provider:{norm_name(t.provider).replace(' ', '-')}",
                                name=t.provider, role="Treating provider"))
            seen.add(norm_name(t.provider))

    # Providers that appear in treatment first.
    def rank(p: Provider) -> tuple[int, str]:
        return (0 if any(names_match(p.name, t) for t in treated) else 1, p.name)

    return sorted(out, key=rank)


def provider_by_id(matter_id: str, contact_id: str) -> Provider | None:
    return next((p for p in list_providers(matter_id) if p.contact_id == contact_id), None)
