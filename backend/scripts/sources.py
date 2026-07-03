"""Declarative manifest of legal documents in the corpus.

Add a new document by finding its ItemID on vbpl.vn (the number at the end of
the detail URL, e.g. .../luat-nha-o-so-27-2023-qh15--169032) and appending one
entry here. The pipeline fetches the full text from the Ministry of Justice
open API automatically — no browser, no manual download. No code changes.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class LegalSource:
    vbpl_id: int  # vbpl.vn ItemID — used to fetch full text from the MOJ API
    html: str  # cached source HTML filename in data/raw_html/
    text: str  # generated plain-text filename in data/raw/
    document_id: str  # official number, used as citation id
    name: str  # human-readable label


SOURCES: list[LegalSource] = [
    LegalSource(
        vbpl_id=169032,
        html="luat-nha-o-2023.html",
        text="luat-nha-o-2023.txt",
        document_id="27/2023/QH15",
        name="Luật Nhà ở 2023",
    ),
    LegalSource(
        vbpl_id=169709,
        html="nghi-dinh-95-2024.html",
        text="nghi-dinh-95-2024.txt",
        document_id="95/2024/ND-CP",
        name="Nghị định 95/2024/NĐ-CP",
    ),
]
