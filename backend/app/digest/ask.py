"""Cited Q&A: Opus answers only from retrieved passages, citing them as [n]."""

import re

from pydantic import BaseModel

from app.llm import MODEL_OPUS, structured
from app.retrieval.fence import FENCE_RULE, fence
from app.retrieval.search import search
from app.schemas import Answer

SYSTEM = (
    "You answer questions about a personal-injury case for the firm's attorneys, paralegals and case "
    "managers. Answer ONLY from the numbered passages. Cite every factual sentence with the passage "
    "number in square brackets, e.g. [2]. If the passages do not answer the question, say so plainly. "
    "Quote exact words when precision matters. Direct, professional, concise; markdown allowed. "
    + FENCE_RULE
)


class AskOut(BaseModel):
    answer_markdown: str


def ask(matter_id: str, question: str, k: int = 8) -> Answer:
    passages = search(matter_id, question, top_k=k)
    if not passages:
        return Answer(answer_markdown="Nothing in the synced case file matches this question.", citations=[])
    blocks = "\n\n".join(
        fence(i + 1, f'title="{p.citation.source_title[:120]}" date="{p.citation.date or ""}"',
              p.citation.quote, cap=4000)
        for i, p in enumerate(passages))
    out = structured(MODEL_OPUS, AskOut, SYSTEM, f"{blocks}\n\nQuestion: {question}", purpose="ask",
                     matter_id=matter_id, effort="low", max_tokens=3000)

    # Keep only markers that point at real passages; renumber to the cited subset.
    used: list[int] = []
    for m in re.findall(r"\[(\d+)\]", out.answer_markdown):
        n = int(m)
        if 1 <= n <= len(passages) and n not in used:
            used.append(n)
    remap = {old: new for new, old in enumerate(used, 1)}

    def sub(m: re.Match) -> str:
        n = int(m.group(1))
        return f"[{remap[n]}]" if n in remap else ""

    text = re.sub(r"\[(\d+)\]", sub, out.answer_markdown)
    return Answer(answer_markdown=text, citations=[passages[n - 1].citation for n in used])
