# Demo video script

Fill this in once the concept is chosen. Keep it to the one path the video shows.

1. Opening problem (one sentence, from the organizers' pain point)
2. Steps on screen, each with what the viewer should notice
3. Closing line

Video is 90 seconds, on Sapini read live from Clio. Before recording: digestion
already cached in our database, clean start, browser zoom and window size fixed.

## Pitch notes (say these; not built)

- **Sync today:** on demand (`POST /api/matters/{id}/sync`). Incremental: about 24
  read-only Clio GETs, unchanged items skipped by content hash; only changed
  sources are re-chunked, re-embedded and re-digested (about $0.15–0.20 per
  refresh vs about $1.50 first digest).
- **Production: real time via Clio webhooks.** Subscribe to record-change
  events (notes, communications, tasks, calendar, documents, activities), then
  re-ingest just that item and re-digest just the affected facts in seconds.
  The same events drive "the case moved" updates to providers. Not built here,
  because creating a webhook subscription is a write to Clio and our build is
  strictly read-only.
