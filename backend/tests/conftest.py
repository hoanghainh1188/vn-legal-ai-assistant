import pytest


@pytest.fixture
def sample_legal_text() -> str:
    return """Chương I
NHỮNG QUY ĐỊNH CHUNG

Điều 1. Phạm vi điều chỉnh
Luật này quy định về sở hữu, phát triển nhà ở.

Điều 2. Đối tượng áp dụng
Luật này áp dụng đối với tổ chức, cá nhân.

Chương II
SỞ HỮU NHÀ Ở

Điều 8. Đối tượng được sở hữu nhà ở
1. Tổ chức, hộ gia đình, cá nhân trong nước.
2. Người Việt Nam định cư ở nước ngoài.

Điều 9. Điều kiện người Việt Nam định cư ở nước ngoài
1. Phải có giấy tờ chứng minh quốc tịch Việt Nam.
2. Phải có hộ chiếu còn giá trị."""


@pytest.fixture
def sample_document_id() -> str:
    return "27/2023/QH15"
