"""Convert vbpl.vn "body_content" HTML export into clean legal plain text.

The official documents on vbpl.vn download as Word-exported HTML with list
bullet prefixes (·, o) on headings. This script flattens the HTML into the
line-oriented plain text expected by ``chunk_legal_text`` — one heading per
line: ``Chương <roman>`` / ``Điều <n>. <title>`` followed by body lines.

Usage:
    uv run python scripts/html_to_legal_text.py <input.html> <output.txt>
"""

from __future__ import annotations

import html as html_lib
import re
import sys
from pathlib import Path

# Block-level tags whose close (or self) should become a line break.
_BLOCK_BREAK = re.compile(
    r"</(p|div|li|tr|h[1-6]|table|ul|ol|blockquote)>|<br\s*/?>",
    re.IGNORECASE,
)
_TAG = re.compile(r"<[^>]+>")
# Leading list-bullet artefacts from the Word export (·, o, §, •, -, *).
_BULLET_PREFIX = re.compile(r"^[·o§•*\-•]\s*")
_WS = re.compile(r"[ \t ]+")

ARTICLE_RE = re.compile(r"^Điều\s+\d+\.")
CHAPTER_RE = re.compile(r"^Chương\s+[IVXLCDM]+\b")


def _to_lines(raw_html: str) -> list[str]:
    text = _BLOCK_BREAK.sub("\n", raw_html)
    text = _TAG.sub("", text)
    text = html_lib.unescape(text)
    lines: list[str] = []
    for line in text.split("\n"):
        line = _WS.sub(" ", line).strip()
        line = _BULLET_PREFIX.sub("", line).strip()
        if line:
            lines.append(line)
    return lines


def _article_number(line: str) -> int:
    return int(re.match(r"^Điều\s+(\d+)\.", line).group(1))


def _strip_table_of_contents(lines: list[str]) -> list[str]:
    """Drop a leading mục lục (table of contents), if present.

    The vbpl export lists every ``Điều`` title once as a ToC and then repeats
    the full sequence as the body. Article numbers climb 1..N in the ToC then
    reset to 1 at the body — detect that reset and keep only the body, backing
    up to include the chapter heading that opens it.
    """
    article_positions = [
        (i, _article_number(line))
        for i, line in enumerate(lines)
        if ARTICLE_RE.match(line)
    ]
    if not article_positions:
        return lines

    reset_index: int | None = None
    previous = 0
    for line_index, number in article_positions:
        if number < previous:  # sequence restarted → body begins here
            reset_index = line_index
            break
        previous = number

    if reset_index is None:
        return lines  # single run, no ToC

    body_start = reset_index
    for back in range(reset_index - 1, max(-1, reset_index - 4), -1):
        if CHAPTER_RE.match(lines[back]):
            body_start = back
            break
    return lines[body_start:]


def html_to_legal_text(raw_html: str) -> str:
    """Flatten HTML into ``Chương``/``Điều`` line-oriented plain text."""
    lines = _strip_table_of_contents(_to_lines(raw_html))

    out: list[str] = []
    for line in lines:
        if CHAPTER_RE.match(line) or ARTICLE_RE.match(line):
            out.append("")
            out.append(line)
        else:
            out.append(line)

    cleaned = "\n".join(out)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()
    return cleaned + "\n"


def main() -> None:
    if len(sys.argv) != 3:
        print(__doc__)
        raise SystemExit(2)

    src = Path(sys.argv[1])
    dst = Path(sys.argv[2])
    raw = src.read_text(encoding="utf-8")
    result = html_to_legal_text(raw)
    dst.write_text(result, encoding="utf-8")

    lines = result.split("\n")
    articles = sum(1 for line in lines if ARTICLE_RE.match(line))
    chapters = sum(1 for line in lines if CHAPTER_RE.match(line))
    print(f"Wrote {dst} — {articles} articles, {chapters} chapters, {len(result)} chars")


if __name__ == "__main__":
    main()
