"""Claude access shared by every stream: model ids, structured output, cost logging.

Opus 5.5 and Sonnet 5.5 reject forced `tool_choice` (400), so structured output
uses `messages.parse(output_format=<Pydantic model>)`: schema-validated, no
regex or json.loads on free text. Every call logs tokens + cost to llm_usage
for the "cost per case" submission answer.
"""

from datetime import datetime, timezone
from typing import TypeVar

import anthropic
from pydantic import BaseModel

from app.db import connect

MODEL_HAIKU = "claude-haiku-4-5"     # bulk ingestion: HyDE questions, OCR cleanup
MODEL_SONNET = "claude-sonnet-5-5"   # fact extraction
MODEL_OPUS = "claude-opus-5-5"       # headline brief, cited Q&A

# USD per 1M tokens (input, output)
PRICES = {
    MODEL_HAIKU: (1.00, 5.00),
    MODEL_SONNET: (2.00, 10.00),
    MODEL_OPUS: (4.00, 20.00),
    "text-embedding-3-large": (0.13, 0.0),
}

T = TypeVar("T", bound=BaseModel)

_client: anthropic.Anthropic | None = None


def client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY loaded by app.config
    return _client


def log_usage(model: str, purpose: str, input_tokens: int, output_tokens: int,
              matter_id: str | None = None) -> float:
    price_in, price_out = PRICES.get(model, (0.0, 0.0))
    cost = (input_tokens * price_in + output_tokens * price_out) / 1_000_000
    with connect() as conn:
        conn.execute(
            "INSERT INTO llm_usage (matter_id, model, purpose, input_tokens, output_tokens, cost_usd, created_at)"
            " VALUES (?, ?, ?, ?, ?, ?, ?)",
            (matter_id, model, purpose, input_tokens, output_tokens, cost,
             datetime.now(timezone.utc).isoformat()),
        )
    return cost


def structured(
    model: str,
    schema: type[T],
    system: str,
    content: str | list,
    *,
    purpose: str,
    matter_id: str | None = None,
    effort: str | None = None,
    max_tokens: int = 16000,
    retries: int = 2,
) -> T:
    """One Claude call whose output is validated against `schema`.

    `content` is the user turn: a string or a list of content blocks (e.g. a
    PDF document block). Wrap case text in tags and tell the model it is data,
    not instructions (catalog A8).
    """
    kwargs: dict = {}
    if effort and model != MODEL_HAIKU:
        kwargs["output_config"] = {"effort": effort}
    last_err: Exception | None = None
    for _ in range(retries + 1):
        try:
            resp = client().messages.parse(
                model=model,
                max_tokens=max_tokens,
                system=system,
                messages=[{"role": "user", "content": content}],
                output_format=schema,
                **kwargs,
            )
        except anthropic.BadRequestError:
            raise
        except (anthropic.RateLimitError, anthropic.APIConnectionError, anthropic.InternalServerError) as e:
            last_err = e
            continue
        log_usage(model, purpose, resp.usage.input_tokens, resp.usage.output_tokens, matter_id)
        if resp.stop_reason == "refusal":
            raise RuntimeError(f"{purpose}: model refused ({resp.stop_details})")
        if resp.parsed_output is not None:
            return resp.parsed_output
        last_err = ValueError(f"{purpose}: no parsed output (stop_reason={resp.stop_reason})")
    raise RuntimeError(f"{purpose}: failed after {retries + 1} attempts") from last_err


def matter_cost(matter_id: str) -> float:
    with connect() as conn:
        row = conn.execute(
            "SELECT COALESCE(SUM(cost_usd), 0) FROM llm_usage WHERE matter_id = ?", (matter_id,)
        ).fetchone()
    return float(row[0])
