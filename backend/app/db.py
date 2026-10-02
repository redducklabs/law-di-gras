"""SQLite schema shared by every stream. Our DB only; Clio is never written to.

Change only via a small `contract:` commit.
"""

import sqlite3

from app.config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS matters (
    id TEXT PRIMARY KEY,              -- Clio matter id
    display_number TEXT,
    description TEXT,
    client_name TEXT,
    client_photo_url TEXT,
    status TEXT,
    opened_date TEXT,
    raw_json TEXT,
    synced_at TEXT
);

-- One row per Clio item. id = "<kind>:<clio_id>".
-- kind: note|communication|task|calendar_entry|expense|document|custom_field|contact|matter
CREATE TABLE IF NOT EXISTS sources (
    id TEXT PRIMARY KEY,
    matter_id TEXT NOT NULL,
    kind TEXT NOT NULL,
    title TEXT,
    date TEXT,                        -- ISO date/datetime
    author TEXT,
    text TEXT,                        -- full text (PDFs: pages joined with \\f)
    content_hash TEXT,
    file_path TEXT,                   -- downloaded document, relative to FILES_DIR
    page_count INTEGER,
    raw_json TEXT,
    synced_at TEXT
);
CREATE INDEX IF NOT EXISTS sources_matter ON sources(matter_id, kind);

-- PDF pages. lines_json = [{text, char_start, char_end, x0, y0, x1, y1}],
-- boxes normalized 0..1 with top-left origin, char offsets into pages.text.
CREATE TABLE IF NOT EXISTS pages (
    source_id TEXT NOT NULL,
    page_no INTEGER NOT NULL,         -- 1-based
    width REAL,
    height REAL,
    text TEXT,
    ocr INTEGER DEFAULT 0,
    lines_json TEXT,
    PRIMARY KEY (source_id, page_no)
);

CREATE TABLE IF NOT EXISTS chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id TEXT NOT NULL,
    page_no INTEGER,                  -- NULL for non-PDF sources
    char_start INTEGER,               -- into pages.text (PDF) or sources.text
    char_end INTEGER,
    text TEXT NOT NULL,
    content_hash TEXT
);
CREATE INDEX IF NOT EXISTS chunks_source ON chunks(source_id);
CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(text, content='chunks', content_rowid='id');

CREATE TABLE IF NOT EXISTS vectors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chunk_id INTEGER NOT NULL,
    kind TEXT NOT NULL,               -- body|hyde
    text TEXT,
    embedding BLOB                    -- float32 little-endian
);
CREATE INDEX IF NOT EXISTS vectors_chunk ON vectors(chunk_id);

CREATE TABLE IF NOT EXISTS facts (
    id TEXT PRIMARY KEY,
    matter_id TEXT NOT NULL,
    category TEXT NOT NULL,
    label TEXT,
    value TEXT,
    amount REAL,
    date TEXT,
    source_id TEXT,
    page_no INTEGER,
    quote TEXT,
    char_start INTEGER,
    char_end INTEGER,
    rects_json TEXT,
    verified INTEGER DEFAULT 0,
    model TEXT,
    input_hash TEXT,
    created_at TEXT
);

CREATE TABLE IF NOT EXISTS digests (
    matter_id TEXT NOT NULL,
    kind TEXT NOT NULL,               -- 'dashboard' caches the whole Dashboard JSON
    input_hash TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    model TEXT,
    created_at TEXT,
    PRIMARY KEY (matter_id, kind)
);

CREATE TABLE IF NOT EXISTS share_settings (
    matter_id TEXT NOT NULL,
    contact_id TEXT NOT NULL,
    sections_json TEXT,
    source_ids_json TEXT,
    token TEXT UNIQUE,
    updated_at TEXT,
    PRIMARY KEY (matter_id, contact_id)
);

CREATE TABLE IF NOT EXISTS share_views (
    token TEXT NOT NULL,
    viewed_at TEXT NOT NULL,
    user_agent TEXT
);

CREATE TABLE IF NOT EXISTS llm_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    matter_id TEXT,
    model TEXT,
    purpose TEXT,
    input_tokens INTEGER,
    output_tokens INTEGER,
    cost_usd REAL,
    created_at TEXT
);
"""


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db() -> None:
    with connect() as conn:
        conn.executescript(SCHEMA)
