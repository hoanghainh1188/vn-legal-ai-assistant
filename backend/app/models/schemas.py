from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=500)
    # Lọc theo lĩnh vực (Feature #8); None/không gửi = "Tất cả" (không lọc).
    domain: str | None = Field(default=None, max_length=100)


class SourceDocument(BaseModel):
    article_number: int
    article_title: str
    document_id: str
    content: str
    relevance_score: float
    # Metadata hiệu lực CẤP VĂN BẢN (Feature #7) — hiển thị nhãn + cảnh báo ở UI.
    document_name: str | None = None
    eff_status: str | None = None
    eff_date: str | None = None
    # Lĩnh vực pháp luật (Feature #8).
    domain: str | None = None


class SearchSourcesEvent(BaseModel):
    type: str = "sources"
    data: list[SourceDocument]


class SearchTokenEvent(BaseModel):
    type: str = "token"
    data: str


class SearchDoneEvent(BaseModel):
    type: str = "done"
    data: str = ""


class SearchErrorEvent(BaseModel):
    """Phát khi provider lỗi giữa chừng stream (FR-011)."""

    type: str = "error"
    data: str
