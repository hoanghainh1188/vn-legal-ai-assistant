"""Vietnamese legal text chunker — splits by Điều (Article) boundaries."""

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class LegalChunk:
    article_number: int
    article_title: str
    document_id: str
    chapter: str
    content: str


ARTICLE_PATTERN = re.compile(r"^Điều\s+(\d+)\.\s*(.*)", re.MULTILINE)
CHAPTER_PATTERN = re.compile(r"^Chương\s+([IVXLCDM]+)\b[.\s]*(.*)", re.MULTILINE)


def _find_chapter_at(text: str, position: int) -> str:
    best = ""
    for match in CHAPTER_PATTERN.finditer(text):
        if match.start() <= position:
            best = match.group(1).strip()
        else:
            break
    return best


def chunk_legal_text(text: str, document_id: str) -> list[LegalChunk]:
    matches = list(ARTICLE_PATTERN.finditer(text))
    if not matches:
        return []

    chunks: list[LegalChunk] = []
    for i, match in enumerate(matches):
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        content = text[start:end].strip()
        article_number = int(match.group(1))
        article_title = match.group(2).strip()
        chapter = _find_chapter_at(text, start)

        chunks.append(
            LegalChunk(
                article_number=article_number,
                article_title=article_title,
                document_id=document_id,
                chapter=chapter,
                content=content,
            )
        )

    return chunks


def chunk_file(file_path: str, document_id: str) -> list[LegalChunk]:
    with open(file_path, encoding="utf-8") as f:
        text = f.read()
    return chunk_legal_text(text, document_id)
