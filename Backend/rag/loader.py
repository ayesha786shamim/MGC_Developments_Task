from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOCS_DIR = ROOT / "docs"

DOC_FILES = [
    ("01_mgc_aurora_heights_brochure.md", "Project Brochure"),
    ("02_price_list_payment_plan.md", "Price List & Payment Plan"),
    ("03_booking_policy_faq.md", "Booking Policy & Sales FAQ"),
]


@dataclass
class Chunk:
    """One piece of a document we can search and send to the LLM."""

    file: str
    document: str
    section: str
    text: str
    id: int


def split_by_heading(text: str) -> list[tuple[str, str]]:
    """Split markdown into (section title, section body) pairs."""
    lines = text.splitlines()
    sections = []
    title = "Overview"
    body_lines = []

    for line in lines:
        if line.startswith("## "):
            if body_lines:
                sections.append((title, "\n".join(body_lines).strip()))
            title = line[3:].strip()
            body_lines = []
        else:
            body_lines.append(line)

    if body_lines:
        sections.append((title, "\n".join(body_lines).strip()))

    return [(t, b) for t, b in sections if b]


def load_chunks() -> list[Chunk]:
    """Read all docs in /docs and split them into searchable chunks."""
    chunks = []
    next_id = 0

    for filename, document_name in DOC_FILES:
        full_text = (DOCS_DIR / filename).read_text(encoding="utf-8")

        for section, body in split_by_heading(full_text):
            if len(body) <= 700:
                chunks.append(Chunk(filename, document_name, section, body, next_id))
                next_id += 1
                continue

            parts = [p.strip() for p in body.split("\n\n") if p.strip()]
            current = ""
            for part in parts:
                joined = f"{current}\n\n{part}".strip() if current else part
                if len(joined) > 700 and current:
                    chunks.append(
                        Chunk(filename, document_name, section, current, next_id)
                    )
                    next_id += 1
                    current = part
                else:
                    current = joined
            if current:
                chunks.append(
                    Chunk(filename, document_name, section, current, next_id)
                )
                next_id += 1

    return chunks
