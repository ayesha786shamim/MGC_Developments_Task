import os
import re
from dataclasses import dataclass
from pathlib import Path

import httpx
from dotenv import load_dotenv

from rag.embeddings import SearchIndex
from rag.loader import Chunk, load_chunks

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env", override=True)

SYSTEM_PROMPT = """You are the MGC sales assistant for Aurora Heights.

Use ONLY the CONTEXT below. Do not invent facts.

Rules:
- If two docs disagree, show both answers and say to confirm with management.
- If the answer is NOT in the CONTEXT, say clearly that it is not in the MGC documents and they should ask the marketing manager. Do not invent. Do NOT cite any source.
- If something is unconfirmed in the CONTEXT, say it is unconfirmed and cite that source.
- For prices with floor/corner/Margalla premiums, add the % premiums then multiply base.
- Keep answers short.
- Only when the CONTEXT supports the answer: end with Sources: document + section. If two documents conflict, cite both.
- If the answer is not in the CONTEXT, do not write a Sources line.

CONTEXT:
{context}
"""

NOT_IN_DOCS_MARKERS = [
    "not in the document",
    "not in the mgc document",
    "not found in the document",
    "not mentioned in the document",
    "do not have that in",
    "don't have that in",
    "i do not have that",
    "i don't have that",
    "no information in the",
    "not covered in the",
    "isn't in the document",
    "is not in the document",
    "cannot find that in",
    "could not find that in",
    "outside the document",
    "not available in the document",
]


@dataclass
class Answer:
    answer: str
    sources: list[dict]
    confidence: str
    mode: str


def make_sources(hits: list[tuple[Chunk, float]], max_sources: int = 2) -> list[dict]:
    """Keep only the strongest unique document sections."""
    best_by_section = {}
    for chunk, score in hits:
        key = (chunk.document, chunk.section)
        if key not in best_by_section or score > best_by_section[key][1]:
            best_by_section[key] = (chunk, score)

    ranked = sorted(best_by_section.values(), key=lambda x: x[1], reverse=True)
    sources = []
    for chunk, score in ranked[:max_sources]:
        excerpt = chunk.text.replace("\n", " ").strip()
        if len(excerpt) > 280:
            excerpt = excerpt[:280] + "..."
        sources.append(
            {
                "document": chunk.document,
                "section": chunk.section,
                "file": chunk.file,
                "score": round(score, 3),
                "excerpt": excerpt,
            }
        )
    return sources


def make_context(hits: list[tuple[Chunk, float]]) -> str:
    blocks = []
    for i, (chunk, score) in enumerate(hits, start=1):
        blocks.append(
            f"[Passage {i} | {chunk.document} | {chunk.section} | score {score:.3f}]\n"
            f"{chunk.text}"
        )
    return "\n\n---\n\n".join(blocks)


def answer_not_in_docs(text: str) -> bool:
    """True when the model says the docs do not contain the answer."""
    lowered = text.lower()
    return any(marker in lowered for marker in NOT_IN_DOCS_MARKERS)


def strip_source_footer(text: str) -> str:
    """Remove a trailing Sources: line from the model answer."""
    cleaned = re.sub(
        r"\n*\s*sources?\s*:.*$",
        "",
        text.strip(),
        flags=re.IGNORECASE | re.DOTALL,
    )
    return cleaned.strip()


def call_gemini(question: str, context: str) -> str:
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("Set GEMINI_API_KEY in your .env file")

    model = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")
    prompt = SYSTEM_PROMPT.format(context=context) + f"\n\nUser question: {question}"
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:generateContent"
    )
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.1},
    }

    with httpx.Client(timeout=90.0) as client:
        res = client.post(url, params={"key": api_key}, json=body)

        if res.status_code == 429:
            raise RuntimeError(
                "Gemini rate limit hit (429 Too Many Requests). "
                "Wait about a minute, then try again. "
                "Free-tier keys only allow a limited number of calls per minute/day."
            )
        if res.status_code >= 400:
            raise RuntimeError(
                f"Gemini request failed (HTTP {res.status_code}). "
                "Check your API key, model name, and quota in Google AI Studio."
            )

        parts = res.json()["candidates"][0]["content"]["parts"]
        text = "".join(p.get("text", "") for p in parts if not p.get("thought")).strip()
        if not text:
            text = "".join(p.get("text", "") for p in parts).strip()
        if not text:
            raise RuntimeError("Gemini returned an empty answer")
        return text


def source_limit(question: str) -> int:
    """Most answers need 1 source; conflicts need 2."""
    q = question.lower()
    if "transfer" in q and "fee" in q:
        return 2
    return 1


class DocumentRAG:
    """Search docs, then answer with Gemini only."""

    def __init__(self):
        self.chunks = load_chunks()
        self.index = SearchIndex(self.chunks)

    def ask(self, question: str) -> Answer:
        q = question.strip()
        if not q:
            return Answer(
                "Please ask a question about the MGC documents.",
                [],
                "low",
                "empty",
            )

        hits = self.index.search(q, top_k=4)
        context = make_context(hits) if hits else ""
        text = call_gemini(q, context)
        model = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")

        top = hits[0][1] if hits else 0.0
        if top >= 0.25:
            confidence = "high"
        elif top >= 0.1:
            confidence = "medium"
        else:
            confidence = "low"

        grounded = (
            bool(hits)
            and top >= 0.05
            and not answer_not_in_docs(text)
        )

        if grounded:
            sources = make_sources(hits, max_sources=source_limit(q))
            answer_text = text
        else:
            sources = []
            answer_text = strip_source_footer(text)

        return Answer(answer_text, sources, confidence, f"rag-gemini:{model}")


_assistant = None


def get_assistant() -> DocumentRAG:
    global _assistant
    if _assistant is None:
        _assistant = DocumentRAG()
    return _assistant
