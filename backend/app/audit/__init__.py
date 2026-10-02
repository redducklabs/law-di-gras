"""S6 data audit: checks what the dashboard shows for a matter against the record.

Read-only: reads our SQLite DB and Clio (GET via app.clio.client). Never digests,
never syncs, never writes the dashboard. Run: `uv run python -m app.audit`.
"""
