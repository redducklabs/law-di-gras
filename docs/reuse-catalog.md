# Reuse catalog

These are patterns worth copying from two earlier Red Duck Labs legal projects. Nothing has been copied yet. Once the challenge is known, pick what fits, copy it in, and simplify it for the prototype.

**The source repos are read-only. Never edit them.**

- `A:` means `C:\Repos\aurolegal.ai\backend\src\`.
- `R:` means `C:\Repos\redducklaw\`.
- Line numbers were accurate on 2026-10-01 and may drift.

## Fit for trial attorneys

The users are trial attorneys, so redducklaw is the closer match: it was built
for litigators (summary judgment, deposition page:line cites, separate
statements). Its citation chip, quote finding, citation verification and
litigation citation parser (R2, R7, R8, R10) are high-value. From aurolegal.ai,
take the grounding machinery (A1–A4, A6–A8, A12) and skip the consumer-facing
pieces: UPL judges (A5, except `merge_verdict`), the standing gates, and the
traffic-specific retrieval scoping (A10).

## Lift order if the challenge involves AI over case materials

1. Grounding prompt block (A1)
2. Forced tool-call helper (A6)
3. Ungrounded-citation detector plus regenerate-once-then-scrub (A2, A3)
4. Findings-only judges with a correction addendum (A4)
5. Verbatim quote checking and prompt fencing (A7, A8)
6. Citation chip and viewer, upgraded to real highlights (R1–R3, plus the gaps listed under PDF viewing). For attorneys, verifiable source highlighting is likely the core of the demo, so consider moving this up.

---

## Anti-hallucination and grounding (aurolegal.ai)

Background reading:

- `C:\Repos\aurolegal.ai\claude_help\product-goals.md` sets the priority order: no hallucination, then legal accuracy, then argument strength, then convenience. Its key line is "prompt instructions are not a control".
- `C:\Repos\aurolegal.ai\docs\design\ai-pipeline.md` covers retrieval (around line 131), tool use (around line 515), the three UPL layers (around lines 611–668) and the relevance judge (around line 669).

| # | Pattern | What it does | Where | How portable |
|---|---|---|---|---|
| A1 | `[N]` marker convention and grounding prompt | Retrieved chunks are numbered `[1]..[N]`, and the model may cite only those numbers. If no chunk supports a point, the model leaves the point out instead of filling it from memory. Each `[N]` sits beside a short verbatim quote. | `A:services/contest_letter/prompts.py` L279–334 (`_CITATION_GROUNDING`); `A:services/rag_service.py` L492 (`_assemble_context`); `A:services/contest_letter/citations.py` L44 (`_MARKER_RE`) and L371 (`scan_markers`) | High. It is a prompt string and a regex; copy it almost word for word. |
| A2 | Deterministic ungrounded-citation detector | Regexes find statutes and case names, normalize each to a canonical key, and flag any that were not in that generation's retrieval. | `A:services/contest_letter/citations.py` L836 (`find_ungrounded_citations`); `citation_patterns.py`; `A:services/citation_keys.py` (`canonical_section_key`) | The logic is portable. The regex patterns cover only CA, TX and FL, so write new ones for your jurisdiction. |
| A3 | Regenerate once, then scrub | Regenerate once with a correction listing the bad citations. Anything still ungrounded is removed, either the whole paragraph or the reference itself, which becomes "the applicable law". | Cleanest template: `A:services/improvement_chat_grounding.py` L159 (`ground_chat_reply`). Also `citations.py` L1154 (`scrub_hallucinated_citations`) and `A:services/citation_scrub.py` L59 (`scrub_ungrounded_law`) | High. Pure functions over text plus a regenerate callback. |
| A4 | Findings-only judges | A cheap judge returns typed findings, never rewritten text. The findings become a capped correction addendum for one regeneration. The fact judge looks for fabricated, contradicted or invented details. The substance judge checks that a cited source actually supports the claim it is cited for. | `A:services/contest_letter/fact_grounding_judge.py` L138 (prompt), L259, L344 (addendum); `A:services/contest_letter/citation_substance_judge.py` L116, L187 | High. Needs only the output text, the facts and the source text. |
| A5 | UPL judge and `merge_verdict` | The UPL judge flags outcome predictions and advice phrasing. Judges run in parallel and fail closed. `merge_verdict` combines them into accept, regenerate or fallback. | `A:services/contest_letter/upl_judge.py` L142; `A:services/upl_llm_judge.py` L256; `A:services/conversational_judge.py` L78 (`merge_verdict`) | Skip the UPL judges (users are attorneys). `merge_verdict` is still a useful pure function. |
| A6 | Forced `tool_choice` with a validation retry | Uses `tool_choice` with a schema and validates the result with Pydantic. On failure it sends back an error `tool_result` and retries up to 3 times. | `A:services/tool_validation.py` L263 (`invoke_with_tool_validation`) | High. Swap its internal router for the Anthropic SDK. |
| A7 | Verbatim span verification | A fact the model extracts is accepted only if it is a verbatim slice of the source. Each citation resolves to a highlight range inside its source section. | `A:services/intake/fact_evidence.py` L100 (`find_verbatim_span`); `citations.py` L493 (`_resolve_chunk_span`) and L512 (`_compute_highlight_range`) | Very high. Pure string code. This connects directly to PDF highlighting. |
| A8 | Prompt-injection fencing | Strips invisible characters, caps length, and wraps user data in `<captured_facts>` / `<intake_transcript>` tags that the prompt says are data, not instructions. | `A:services/intake/prompt_facts.py` L339, L383, L474 | High. |
| A9 | `lookup_law` tool | The model can verify a citation that was not in context. If the citation is found, its verbatim text counts as grounded. If not, the model must not cite it. | `A:services/contest_letter/lookup_law.py` L23, L52 | Medium. The handler queries a database table. |
| A10 | Retrieval scoping and fact-gated provisions | Each case type maps to the sources it is allowed to use. Provisions that need a particular fact are withheld from results unless the case has that fact. | `A:services/retrieval_scope.py` L210; `A:services/contest_letter/fact_gated_provisions.py` L222 | Rebuild as a plain Python dict. |
| A11 | Central grounding floor | A single fail-loud check runs after every generator and before anything is saved. | `A:services/deliverables/grounding_floor.py` L244 (`enforce_grounding`) | Medium. The idea is worth copying; the types are not. |
| A12 | Citation-support grader | An evaluation step that requires a verbatim supporting quote before a citation counts as supported. Useful for a demo slide on accuracy. | `A:eval/scenario/judge/citation_support.py` L73 | High. |

Skip these: the CA/TX/FL citation regexes, the database-backed citation resolution, the standing pre-flight gates, and the ~$2–3/run benchmark harness. They are too specific to aurolegal.

---

## PDF viewing and highlighting (redducklaw)

**redducklaw does not actually highlight inside PDFs.** It shows PDFs in an `<iframe>` with `#page=N`, and its footer says line highlighting is not available.

Its stack is Vite, React 18, TypeScript and Tailwind 3 on the frontend, and FastAPI, Postgres, Celery, Qdrant and S3 on the backend. What is worth reusing is the citation user interface and the backend pipeline that turns a quote into a page and line.

| # | Pattern | What it does | Where | How portable |
|---|---|---|---|---|
| R1 | Iframe viewer with page jump | A modal that opens a presigned URL and jumps to `#page=N`. Images and downloads are also handled. | `R:frontend\src\components\DocumentViewer.tsx` (L49–63 `getViewerUrl`, iframe at L185) | Copy as a day-one fallback. It cannot highlight, and Safari ignores `#page`. |
| R2 | Citation chip | An inline button labelled "Doc • p. N • lines a–b" that opens the viewer at that spot. | `R:frontend\src\components\CitationLink.tsx`; used in `R:frontend\src\pages\FactAnalysis.tsx` L398 | High. Its props map straight onto a richer viewer's jump-to API. |
| R3 | Turning document IDs in AI text into links | Finds UUIDs in model output with a regex and replaces each with a clickable document name. | `R:frontend\src\components\DocumentLinkedText.tsx` L9–61 | High. Pure React. |
| R4 | Presigned view URL | Uses two boto3 clients, an internal one and a browser-reachable one, for Docker setups. | `R:backend\app\api\documents.py` L276; `R:backend\app\services\storage.py` L28–39 | High if you use S3 or MinIO. |
| R5 | Ingestion with OCR fallback | Tries the Unstructured `partition()` strategies in order (hi_res, ocr_only, fast, auto) and warns when OCR was used. | `R:backend\app\services\ingestion.py` L69–129; `R:backend\app\services\statement_parser.py` L112–240 | Heavy dependencies (tesseract, poppler). Unstructured returns `metadata.coordinates`, which this code currently discards; keeping them gives cheap highlight boxes. |
| R6 | Chunks tagged with page and line | Tags each chunk with its page and with line numbers taken from the margin numbering in depositions. | `R:backend\app\services\ingestion.py` L164–232 | The line-number heuristic only works for depositions. |
| R7 | Finding a quote | Exact substring match first, then `rapidfuzz.partial_ratio` (threshold 0.8 or higher), after vector search and Cohere rerank. | `R:backend\app\services\search.py` L124–170 (`find_quote_in_documents`) | Easy. Add `partial_ratio_alignment` to get character offsets for highlights. |
| R8 | Three-layer citation verification | Finds the quote, then runs NLI entailment (a contradiction means reject), then checks embedding similarity. The result is approved, warning or rejected. | `R:backend\app\services\citation.py` L59–239; thresholds in `R:backend\app\config.py` L44–51 | Torch is heavy; for the hackathon, swap the NLI step for an LLM judge (A4). |
| R9 | Agent tool that forces citations | `search_evidence` plus a `cite_evidence` tool required for every factual claim, routed through R8. | `R:backend\app\services\agent.py` L59, L184 | High as a design. |
| R10 | Legal citation parser and formatter | Regexes for formats such as "Ex. A (Jones Depo.) at 45:12-46:8", "Decl. ¶ 5" and "Exhibit A, p. 5", plus a formatter that writes them back out. | `R:backend\app\services\statement_parser.py` L60–86, L642–709; `R:backend\app\services\export.py` L14 | Pure Python; copy directly. |

### Gaps to build new if the demo needs real highlights

- **A renderer with a text layer.** Use `react-pdf` or `pdfjs-dist` with a worker. `react-pdf-highlighter` is the fastest route to drawing highlights.
- **Text extraction that keeps positions.** PyMuPDF's `page.search_for(quote)` returns rectangles directly. `page.get_text("words")` returns word boxes.
- **A path from quote to rectangles.** Find the quote with R7 or A7, then turn it into rectangles, stored on the citation as `rects: [{page, x0, y0, x1, y1}]` normalized to 0–1.
- **Scrolling to the highlight**, not just to the page.
