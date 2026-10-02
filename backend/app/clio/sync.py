"""Pull one Clio matter into our SQLite (read-only on Clio; writes only our DB).

Run: cd backend && uv run python -m app.clio.sync [matter_id]
One `sources` row per Clio item, id "<kind>:<clio_id>". Unchanged items
(same content_hash) keep their pages/chunks so S2's embeddings stay valid.
"""

import hashlib
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

from app import config
from app.clio.client import client
from app.db import connect, init_db
from app.ingest import chunk, pdf

log = logging.getLogger("clio.sync")

MATTER_FIELDS = (
    "id,display_number,description,status,open_date,close_date,pending_date,location,created_at,updated_at,"
    "client{id,name,type},practice_area{name},matter_stage{name},responsible_attorney{name},originating_attorney{name},"
    "statute_of_limitations{id},custom_field_values{id,value,field_name,field_type,custom_field}"
)
CONTACT_FIELDS = (
    "id,name,type,first_name,last_name,title,prefix,date_of_birth,company{name},avatar,"
    "email_addresses{address,name},phone_numbers{number,name},"
    "addresses{name,street,city,province,postal_code,country},custom_field_values{id,value,field_name}"
)
ENDPOINTS = {
    # kind: (endpoint, fields, extra params)
    "note": ("notes.json", "id,subject,detail,date,created_at,updated_at,author{name},type", {"type": "Matter"}),
    "communication": ("communications.json",
                      "id,subject,body,date,received_at,type,created_at,updated_at,user{name},senders,receivers", {}),
    "task": ("tasks.json", "id,name,description,status,priority,due_at,completed_at,created_at,updated_at,"
                           "assignee{name,type},assigner{name}", {}),
    "calendar_entry": ("calendar_entries.json", "id,summary,description,start_at,end_at,all_day,location,"
                                                "created_at,updated_at,calendar_owner{name},attendees", {}),
    "expense": ("activities.json", "id,type,date,quantity,price,total,note,created_at,updated_at,"
                                   "activity_description{name},expense_category{name},user{name},non_billable", {}),
    "document": ("documents.json", "id,name,content_type,created_at,updated_at,received_at,filename,size,"
                                   "document_category{name},parent{name},"
                                   "latest_document_version{id,size,content_type,filename}", {}),
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _sha(*parts) -> str:
    return hashlib.sha256(json.dumps(parts, sort_keys=True, default=str).encode()).hexdigest()


def _lines(*pairs) -> str:
    """'Label: value' lines for non-empty values."""
    return "\n".join(f"{k}: {v}" for k, v in pairs if v not in (None, "", []))


def _names(people) -> str:
    return ", ".join(p.get("name") or p.get("identifier") or "" for p in (people or []))


def _money(x) -> str | None:
    return None if x is None else f"${x:,.2f}"


# --- per-kind rendering: (title, date, author, text) ------------------------

def render(kind: str, r: dict) -> tuple[str, str | None, str | None, str]:
    if kind == "note":
        head = _lines(("Note", r.get("subject")), ("Date", r.get("date")), ("Author", (r.get("author") or {}).get("name")))
        return r.get("subject") or "Note", r.get("date"), (r.get("author") or {}).get("name"), f"{head}\n\n{r.get('detail') or ''}".strip()
    if kind == "communication":
        sender = _names(r.get("senders"))
        head = _lines(("Subject", r.get("subject")), ("Type", (r.get("type") or "").replace("Communication", "")),
                      ("Date", r.get("date") or r.get("received_at")), ("From", sender), ("To", _names(r.get("receivers"))))
        return r.get("subject") or "Communication", r.get("date") or r.get("received_at"), sender or None, f"{head}\n\n{r.get('body') or ''}".strip()
    if kind == "task":
        text = _lines(("Task", r.get("name")), ("Status", r.get("status")), ("Priority", r.get("priority")),
                      ("Due", r.get("due_at")), ("Completed", r.get("completed_at")),
                      ("Assignee", (r.get("assignee") or {}).get("name")), ("Assigned by", (r.get("assigner") or {}).get("name")),
                      ("Description", r.get("description")))
        return r.get("name") or "Task", r.get("due_at"), (r.get("assigner") or {}).get("name"), text
    if kind == "calendar_entry":
        text = _lines(("Event", r.get("summary")), ("Start", r.get("start_at")), ("End", r.get("end_at")),
                      ("All day", "yes" if r.get("all_day") else None), ("Location", r.get("location")),
                      ("Attendees", _names(r.get("attendees"))), ("Description", r.get("description")))
        return r.get("summary") or "Calendar entry", r.get("start_at"), (r.get("calendar_owner") or {}).get("name"), text
    if kind == "expense":
        note = r.get("note") or ""
        title = note.split("\n", 1)[0][:120] or (r.get("activity_description") or {}).get("name") or r.get("type")
        text = _lines(("Entry", "Expense" if r.get("type") == "ExpenseEntry" else "Time entry"), ("Date", r.get("date")),
                      ("Amount", _money(r.get("total"))), ("Quantity", r.get("quantity")), ("Rate", _money(r.get("price"))),
                      ("Category", (r.get("expense_category") or {}).get("name")),
                      ("Activity", (r.get("activity_description") or {}).get("name")),
                      ("Non-billable", "yes" if r.get("non_billable") else None), ("Entered by", (r.get("user") or {}).get("name")))
        return title, r.get("date"), (r.get("user") or {}).get("name"), f"{text}\n\n{note}".strip()
    raise ValueError(kind)


# --- sync --------------------------------------------------------------------

def resolve_matter(matter_id: str | None = None) -> dict:
    c = client()
    if matter_id and str(matter_id).isdigit():
        return c.get(f"matters/{matter_id}.json", {"fields": MATTER_FIELDS})["data"]
    found = list(c.paginate("matters.json", {"query": config.MATTER_QUERY, "fields": "id"}))
    if not found:
        raise LookupError(f"no Clio matter matches {config.MATTER_QUERY!r}")
    return c.get(f"matters/{found[0]['id']}.json", {"fields": MATTER_FIELDS})["data"]


class Sync:
    def __init__(self, conn, matter_id: str):
        self.conn, self.matter_id = conn, matter_id
        self.seen: set[str] = set()
        self.counts: dict[str, int] = {}
        self.errors: list[str] = []
        self.synced_at = _now()

    def upsert(self, sid: str, kind: str, title, date, author, text, raw, content_hash=None,
               file_path=None, page_count=None) -> bool:
        """Store a source; return True if it is new or changed (needs re-chunking)."""
        self.seen.add(sid)
        self.counts[kind] = self.counts.get(kind, 0) + 1
        content_hash = content_hash or _sha(title, date, author, text)
        old = self.conn.execute("SELECT content_hash FROM sources WHERE id=?", (sid,)).fetchone()
        self.conn.execute(
            "INSERT OR REPLACE INTO sources(id, matter_id, kind, title, date, author, text, content_hash, file_path,"
            " page_count, raw_json, synced_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (sid, self.matter_id, kind, title, date, author, text, content_hash, file_path, page_count,
             json.dumps(raw), self.synced_at),
        )
        return not old or old[0] != content_hash

    def text_source(self, sid, kind, title, date, author, text, raw):
        if self.upsert(sid, kind, title, date, author, text, raw):
            chunk.delete_chunks(self.conn, sid)
            chunk.chunk_source(self.conn, sid, text)

    def document(self, r: dict):
        sid = f"document:{r['id']}"
        ver = r.get("latest_document_version") or {}
        ctype = (ver.get("content_type") or r.get("content_type") or "").lower()
        title = r.get("name") or r.get("filename") or "Document"
        date = r.get("received_at") or r.get("created_at")
        folder = (r.get("parent") or {}).get("name")
        h = _sha("document", ver.get("id"), ver.get("size"), title, date, pdf.__name__, pdf.MIN_TEXT_CHARS)
        rel = f"{r['id']}.pdf"
        path = config.FILES_DIR / rel
        old = self.conn.execute("SELECT content_hash FROM sources WHERE id=?", (sid,)).fetchone()
        if old and old[0] == h and path.exists():
            self.seen.add(sid)
            self.counts["document"] = self.counts.get("document", 0) + 1
            self.conn.execute("UPDATE sources SET raw_json=?, synced_at=? WHERE id=?", (json.dumps(r), self.synced_at, sid))
            return
        data = client().download(f"documents/{r['id']}/download")
        if "pdf" not in ctype and not data[:5] == b"%PDF-":
            ext = (ver.get("filename") or r.get("filename") or "").rsplit(".", 1)[-1].lower()
            try:
                data = pdf.to_pdf(data, ext or ctype.split("/")[-1])
            except Exception as e:
                # Not convertible (e.g. docx): keep a text-less source so it still lists.
                self.errors.append(f"{sid} ({ctype}): not convertible to PDF: {e}")
                self.upsert(sid, "document", title, date, folder, "", r, content_hash=h)
                chunk.delete_chunks(self.conn, sid)
                return
        path.write_bytes(data)
        pages = pdf.extract(str(path))
        self.conn.execute("DELETE FROM pages WHERE source_id=?", (sid,))
        chunk.delete_chunks(self.conn, sid)
        for p in pages:
            self.conn.execute(
                "INSERT INTO pages(source_id, page_no, width, height, text, ocr, lines_json) VALUES (?,?,?,?,?,?,?)",
                (sid, p.page_no, p.width, p.height, p.text, int(p.ocr), json.dumps(p.lines)),
            )
            chunk.chunk_source(self.conn, sid, p.text, p.page_no)
        self.upsert(sid, "document", title, date, folder, "\f".join(p.text for p in pages), r,
                    content_hash=h, file_path=rel, page_count=len(pages))
        log.info("document %s: %d pages (%d OCR)", title, len(pages), sum(p.ocr for p in pages))


def sync_matter(matter_id: str | None = None) -> dict:
    init_db()
    c = client()
    m = resolve_matter(matter_id)
    mid = str(m["id"])
    conn = connect()
    s = Sync(conn, mid)
    try:
        # Contacts: the client plus every related contact (role = relationship description).
        related = [(m.get("client") or {}).get("id"), "Client"]
        contacts = [tuple(related)] if related[0] else []
        try:
            for rel in c.paginate("relationships.json", {"matter_id": mid, "fields": "id,description,contact{id}"}):
                contacts.append(((rel.get("contact") or {}).get("id"), rel.get("description")))
        except Exception as e:
            s.errors.append(f"relationships: {e}")
        client_photo = None
        for cid, role in contacts:
            if not cid:
                continue
            try:
                ct = c.get(f"contacts/{cid}.json", {"fields": CONTACT_FIELDS})["data"]
            except Exception as e:
                s.errors.append(f"contact {cid}: {e}")
                continue
            if role == "Client":
                client_photo = ct.get("avatar")
            text = _lines(
                ("Contact", ct.get("name")), ("Role on matter", role), ("Type", ct.get("type")),
                ("Title", ct.get("title")), ("Company", (ct.get("company") or {}).get("name")),
                ("Date of birth", ct.get("date_of_birth")),
                ("Email", ", ".join(e.get("address", "") for e in ct.get("email_addresses") or [])),
                ("Phone", ", ".join(p.get("number", "") for p in ct.get("phone_numbers") or [])),
                ("Address", "; ".join(", ".join(filter(None, [a.get("street"), a.get("city"), a.get("province"),
                                                              a.get("postal_code")])) for a in ct.get("addresses") or [])),
                *[(cf.get("field_name"), cf.get("value")) for cf in ct.get("custom_field_values") or []],
            )
            s.text_source(f"contact:{cid}", "contact", ct.get("name") or "Contact", None, None, text,
                          {**ct, "role": role})

        # Matter row + matter source + custom fields.
        stage = (m.get("matter_stage") or {}).get("name")
        client_name = (m.get("client") or {}).get("name") or ""
        conn.execute(
            "INSERT OR REPLACE INTO matters(id, display_number, description, client_name, client_photo_url, status,"
            " opened_date, raw_json, synced_at) VALUES (?,?,?,?,?,?,?,?,?)",
            (mid, m.get("display_number"), m.get("description"), client_name, client_photo, m.get("status"),
             m.get("open_date"), json.dumps(m), s.synced_at),
        )
        mtext = _lines(
            ("Matter", m.get("display_number")), ("Description", m.get("description")), ("Client", client_name),
            ("Status", m.get("status")), ("Stage", stage), ("Practice area", (m.get("practice_area") or {}).get("name")),
            ("Opened", m.get("open_date")), ("Pending", m.get("pending_date")), ("Closed", m.get("close_date")),
            ("Location", m.get("location")), ("Responsible attorney", (m.get("responsible_attorney") or {}).get("name")),
            ("Originating attorney", (m.get("originating_attorney") or {}).get("name")),
        )
        s.text_source(f"matter:{mid}", "matter", m.get("display_number") or "Matter", m.get("open_date"), None, mtext, m)
        for cf in m.get("custom_field_values") or []:
            if cf.get("value") in (None, ""):
                continue
            name = cf.get("field_name") or "Custom field"
            val = cf.get("value")
            s.text_source(f"custom_field:{cf['id']}", "custom_field", name,
                          val if cf.get("field_type") == "date" else None, None, f"{name}: {val}", cf)

        # Item lists.
        for kind, (ep, fields, extra) in ENDPOINTS.items():
            try:
                rows = list(c.paginate(ep, {"matter_id": mid, "fields": fields, **extra}))
            except Exception as e:
                s.errors.append(f"{ep}: {e}")
                continue
            for r in rows:
                try:
                    if kind == "document":
                        s.document(r)
                    else:
                        title, date, author, text = render(kind, r)
                        s.text_source(f"{kind}:{r['id']}", kind, title, date, author, text, r)
                except Exception as e:
                    log.exception("failed %s %s", kind, r.get("id"))
                    s.errors.append(f"{kind}:{r.get('id')}: {e}")
            conn.commit()

        # Drop items that no longer exist in Clio (only for kinds we fetched fully).
        failed = {e.split(":")[0] for e in s.errors}
        for (sid, kind) in conn.execute("SELECT id, kind FROM sources WHERE matter_id=?", (mid,)).fetchall():
            if sid not in s.seen and ENDPOINTS.get(kind, ("",))[0] not in failed:
                chunk.delete_chunks(conn, sid)
                conn.execute("DELETE FROM pages WHERE source_id=?", (sid,))
                conn.execute("DELETE FROM sources WHERE id=?", (sid,))

        chunk.rebuild_fts(conn)
        conn.commit()
        totals = {
            "sources": conn.execute("SELECT COUNT(*) FROM sources WHERE matter_id=?", (mid,)).fetchone()[0],
            "pages": conn.execute("SELECT COUNT(*) FROM pages p JOIN sources s ON s.id=p.source_id WHERE s.matter_id=?", (mid,)).fetchone()[0],
            "chunks": conn.execute("SELECT COUNT(*) FROM chunks c JOIN sources s ON s.id=c.source_id WHERE s.matter_id=?", (mid,)).fetchone()[0],
            "ocr_pages": conn.execute("SELECT COUNT(*) FROM pages p JOIN sources s ON s.id=p.source_id WHERE s.matter_id=? AND p.ocr=1", (mid,)).fetchone()[0],
        }
        return {"matter_id": mid, **totals, "by_kind": s.counts, "errors": s.errors}
    finally:
        conn.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")
    print(json.dumps(sync_matter(sys.argv[1] if len(sys.argv) > 1 else None), indent=1))
