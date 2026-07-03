"""Fetch full legal text from the Ministry of Justice open API.

vbpl.vn's web UI is behind reCAPTCHA, but its backend API
(apipacs.moj.gov.vn) serves the full document text (`vbpqToanVan`) as public,
unauthenticated JSON — keyed by the vbpl.vn ItemID. This replaces the former
manual browser download: the corpus is now fully reproducible with a command.

    uv run python scripts/fetch_sources.py          # refresh all cached HTML
"""

import sys
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.sources import SOURCES, LegalSource

API_URL = "https://apipacs.moj.gov.vn/api/vbpl/document"
RAW_HTML = Path(__file__).resolve().parent.parent / "data" / "raw_html"


def fetch_toanvan(vbpl_id: int) -> str:
    """Return the full-text HTML (`vbpqToanVan`) for a vbpl.vn ItemID."""
    response = httpx.get(
        API_URL,
        params={"id": vbpl_id},
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=60.0,
    )
    response.raise_for_status()
    data = response.json().get("data") or {}
    html = data.get("vbpqToanVan")
    if not html:
        raise ValueError(f"API returned no vbpqToanVan for id={vbpl_id}")
    return html


def ensure_html(source: LegalSource, refresh: bool = False) -> Path:
    """Ensure the cached HTML for a source exists (fetching if needed)."""
    RAW_HTML.mkdir(parents=True, exist_ok=True)
    dest = RAW_HTML / source.html
    if dest.exists() and not refresh:
        return dest
    html = fetch_toanvan(source.vbpl_id)
    dest.write_text(html, encoding="utf-8")
    return dest


def main() -> None:
    for source in SOURCES:
        dest = ensure_html(source, refresh=True)
        size = dest.stat().st_size
        print(f"✓ {source.name} (id={source.vbpl_id}) → {dest.name} ({size} bytes)")


if __name__ == "__main__":
    main()
