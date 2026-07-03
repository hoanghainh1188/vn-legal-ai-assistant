from dataclasses import dataclass

from pydantic import BaseModel, Field


@dataclass(frozen=True)
class LegalChunk:
    article_number: int
    article_title: str
    document_id: str
    chapter: str
    content: str


class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=500)


class SourceDocument(BaseModel):
    article_number: int
    article_title: str
    document_id: str
    content: str
    relevance_score: float


class SearchSourcesEvent(BaseModel):
    type: str = "sources"
    data: list[SourceDocument]


class SearchTokenEvent(BaseModel):
    type: str = "token"
    data: str


class SearchDoneEvent(BaseModel):
    type: str = "done"
    data: str = ""
