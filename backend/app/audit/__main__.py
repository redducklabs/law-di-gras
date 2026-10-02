"""uv run python -m app.audit [--checks 1,3,4,5,6] [--no-llm] [--no-clio] [--ocr]

Writes docs/audit/auto-report.md and docs/audit/auto-findings.json (in this checkout).
Read-only: never POSTs /digest or /sync, never writes to Clio or the dashboard cache.
"""

import argparse
import json
from dataclasses import asdict
from datetime import datetime, timezone

from app import config
from app.audit import chat_check, checks, ingest_check, record_check
from app.audit.items import flatten, load_dashboard
from app.db import connect

OUT_DIR = config.BACKEND_DIR.parent / "docs" / "audit"
SEV_ORDER = {"critical": 0, "major": 1, "minor": 2, "info": 3}
TITLES = {
    "1-code": "Check 1a. Fact support: code checks (quote spans, dates, amounts)",
    "1-judge": "Check 1b/2. Fact support + headline: Sonnet judge (findings only)",
    "2-record": "Check 2b. Headline, injury and recent claims vs the whole record (retrieval + Sonnet)",
    "3-kpi": "Check 3. KPI reconciliation",
    "4-ingest": "Check 4. Ingestion vs Clio and documents",
    "4-ocr": "Check 4b. OCR quality on scanned pages",
    "5-timeline": "Check 5. Timeline semantics",
    "6-provider": "Check 6. Provider views",
    "7-chat": "Check 7. Ask-the-case chat",
}


def cell(s, n: int = 400) -> str:
    s = str(s if s is not None else "").replace("\n", " ").replace("|", "\\|").strip()
    return s if len(s) <= n else s[: n - 1] + "…"


def table(rows: list[dict]) -> str:
    if not rows:
        return "_none_\n"
    keys = list(rows[0].keys())
    lines = ["| " + " | ".join(keys) + " |", "|" + "---|" * len(keys)]
    lines += ["| " + " | ".join(cell(r.get(k), 200) for k in keys) + " |" for r in rows]
    return "\n".join(lines) + "\n"


def matter_id() -> str:
    with connect() as conn:
        row = conn.execute("SELECT matter_id FROM digests WHERE kind='dashboard' ORDER BY created_at DESC").fetchone()
    return row["matter_id"]


def cost_since(start: str) -> float:
    with connect() as conn:
        r = conn.execute("SELECT COALESCE(SUM(cost_usd),0) FROM llm_usage WHERE purpose LIKE 'audit:%' AND created_at>=?",
                         (start,)).fetchone()
    return float(r[0])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--checks", default="1,2,3,4,5,6")
    ap.add_argument("--no-llm", action="store_true")
    ap.add_argument("--no-clio", action="store_true")
    ap.add_argument("--suffix", default="", help="write auto-report<suffix>.md")
    ap.add_argument("--ocr", action="store_true", help="vision-transcribe the OCR pages (~$0.15)")
    a = ap.parse_args()
    want = set(a.checks.split(","))
    start = datetime.now(timezone.utc).isoformat()
    mid = matter_id()
    dash, cached_at = load_dashboard(mid)
    items = flatten(dash)
    findings: list[checks.Finding] = []
    extras: dict[str, str] = {}

    if "1" in want:
        findings += checks.fact_support_code(items, [dash.kpis.specials, dash.kpis.firm_spent, *dash.kpis.liens])
        if not a.no_llm:
            findings += checks.fact_support_judge(items, mid)
        print("check 1 done")
    if "2" in want and not a.no_llm:
        f, rows = record_check.record_support(items, mid)
        findings += f
        extras["2-record"] = "Every claim checked against the whole record:" + chr(10) + chr(10) + table(rows)
        print("check 2 done")
    if "7" in want and not a.no_llm:
        f, tr = chat_check.chat_audit(mid)
        findings += f
        extras["7-chat"] = chr(10).join(f"**Q:** {t['question']}" + chr(10) + chr(10) + f"> " + t["answer"].replace(chr(10), chr(10) + "> ")
                                        + chr(10) + chr(10) + f"Citations {t['citations']}; links: {', '.join(t['links']) or 'none'}" + chr(10)
                                        for t in tr)
        print("check 7 done")
    if "3" in want:
        f, t = checks.kpi_reconcile(dash, mid)
        findings += f
        extras["3-kpi"] = "Billed per provider (dashboard) vs Clio expense entries, and itemized-bill PDF total lines:\n\n" + table(t)
        print("check 3 done")
    if "4" in want:
        f, docs = ingest_check.local_checks(mid)
        findings += f
        extras["4-ingest"] = "Document dates (header shows `clio_date`):\n\n" + table(docs)
        if not a.no_clio:
            f, counts = ingest_check.clio_compare(mid)
            findings += f
            extras["4-ingest"] = "Source counts, Clio (GET) vs our DB:\n\n" + table(counts) + "\n" + extras["4-ingest"]
        if a.ocr and not a.no_llm:
            f, rows = ingest_check.ocr_quality(mid)
            findings += f
            extras["4-ocr"] = table(rows)
        print("check 4 done")
    if "5" in want:
        findings += checks.timeline_semantics(dash)
        print("check 5 done")
    if "6" in want:
        f, t = checks.provider_views(mid)
        findings += f
        extras["6-provider"] = table([{**r, "other_provider_names": ", ".join(r["other_provider_names"]),
                                       "strategy_terms": ", ".join(r["strategy_terms"])} for r in t])
        print("check 6 done")

    findings.sort(key=lambda f: (f.check, SEV_ORDER[f.severity], f.item))
    cost = cost_since(start)
    counts = {s: sum(1 for f in findings if f.severity == s) for s in SEV_ORDER}
    md = [f"# Auto audit report: {dash.matter.display_number}",
          "",
          f"Generated {datetime.now().isoformat(timespec='minutes')} by `uv run python -m app.audit` "
          f"(checks {a.checks}{', no LLM' if a.no_llm else ''}{', OCR' if a.ocr else ''}). "
          f"Dashboard cached {cached_at}, generated_at {dash.generated_at}. Audit LLM cost ${cost:.2f}.",
          "",
          f"**Findings:** {counts['critical']} critical, {counts['major']} major, {counts['minor']} minor. "
          f"Items audited: {len(items)}.",
          "",
          "Severity: critical = wrong number/date/party/tense on screen; major = unsupported or misleading; minor = cosmetic.",
          ""]
    for key, title in TITLES.items():
        fs = [f for f in findings if f.check == key]
        if not fs and key not in extras:
            continue
        md += [f"## {title}", ""]
        if fs:
            md += ["| Sev | Item | On screen | Cited quote | What's wrong | Owner |", "|---|---|---|---|---|---|"]
            md += [f"| {f.severity} | {cell(f.item, 60)} | {cell(f.on_screen, 300)} | {cell(f.quote, 200)} | "
                   f"{cell(f.problem, 500)} | {f.owner} |" for f in fs]
            md.append("")
        if key in extras:
            md += [extras[key], ""]
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / f"auto-report{a.suffix}.md").write_text("\n".join(md), encoding="utf-8")
    (OUT_DIR / f"auto-findings{a.suffix}.json").write_text(json.dumps([asdict(f) for f in findings], indent=1), encoding="utf-8")
    print(f"{counts} cost ${cost:.2f} -> {OUT_DIR / f"auto-report{a.suffix}.md"}")


if __name__ == "__main__":
    main()
