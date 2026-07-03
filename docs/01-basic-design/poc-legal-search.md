# Bản Thiết Kế Dự Án & Master Prompt
*Ứng dụng Trợ lý Pháp lý Thông minh cho Đại đa số Người dân (PoC: Luật Nhà ở 2023)*

## 1. Tổng Quan Ý Tưởng & Mục Tiêu PoC

**Ý tưởng cốt lõi:** Xây dựng một Web Application tra cứu văn bản pháp luật tối giản, hướng tới đại đa số người dân phổ thông. Hệ thống giải quyết các rào cản của người dùng bằng cách cho phép tìm kiếm theo ngôn ngữ tự nhiên/tình huống đời sống thay vì số hiệu văn bản, đồng thời ứng dụng AI theo mô hình RAG để tóm tắt luật, trả lời trực diện và triệt tiêu hoàn toàn hiện tượng ảo giác (hallucination).

**Phạm vi bản PoC (Proof of Concept):** Thử nghiệm giới hạn trong lĩnh vực **Luật Nhà ở 2023 (Số 27/2023/QH15)** và **Nghị định 95/2024/NĐ-CP** để chứng minh tính khả thi trước khi mở rộng toàn hệ thống.

---

## 2. Kiến Trúc Hệ Thống & Định Hình Công Nghệ (Tech Stack)

| Thành phần | Công nghệ đề xuất | Vai trò trong dự án |
| :--- | :--- | :--- |
| **Frontend UI** | Next.js (App Router), Tailwind CSS, Lucide Icons | Giao diện tìm kiếm dạng Chat kết hợp bộ lọc tối giản, tối ưu hóa hiển thị di động và SEO tốt cho các trang điều luật. |
| **Data Pipeline** | Python (BeautifulSoup, python-docx), Ollama | Cào dữ liệu thô từ cổng thông tin chính thống (`vbpl.vn`), dùng mô hình ngôn ngữ nhỏ (Local LLM) để chuẩn hóa thành dữ liệu JSON cấu trúc. |
| **Vector Database** | ChromaDB (Local) hoặc pgvector (PostgreSQL) | Lưu trữ các đoạn luật (chunks) dưới dạng vector nhúng (embeddings) để phục vụ tra cứu ngữ nghĩa tốc độ cao. |
| **AI Orchestration** | LangChain hoặc LlamaIndex (Tùy chọn) | Quản lý luồng RAG (Retrieval-Augmented Generation): Kết nối Vector Store với LLM Prompt. |
| **Deployment** | Vercel (Frontend), Local/Docker (Backend & DB) | Đóng gói và triển khai nhanh bản PoC để kiểm thử hiệu năng và chia sẻ demo nội bộ. |

---

## 3. Quy Trình Chuẩn Hóa Dữ Liệu (Data Pipeline Spec)

Để AI không trả lời sai lệch, dữ liệu đầu vào cần đi qua luồng xử lý tự động gồm 4 giai đoạn:

1. **Ingestion (Thu thập):** Tải file văn bản gốc từ `vbpl.vn` (ưu tiên định dạng HTML hoặc `.docx`).
2. **Extraction (Trích xuất):** Loại bỏ nhiễu (Header, footer, căn cứ ban hành ban đầu) để lấy text nội dung cốt lõi.
3. **Structuring (Cấu trúc hóa):** Chuyển text thô thành file JSON có cấu trúc phân cấp nghiêm ngặt: *Số hiệu văn bản -> Chương -> Điều -> Khoản -> Điểm* bằng Local LLM.
4. **Chunking & Indexing:** Cắt nhỏ văn bản theo đơn vị từng `Điều`. Nhúng vector và lưu vào ChromaDB kèm metadata đầy đủ để truy vết.

---

## 4. Kịch Bản Kiểm Thử Thành Công (Test Cases cho PoC)

Bản PoC được coi là đạt yêu cầu (Definition of Done) nếu vượt qua 3 bài test sau với độ chính xác tuyệt đối:

| STT | Câu hỏi người dùng (Tình huống) | Kỳ vọng hành vi của AI Engine | Cơ sở pháp lý xác thực |
| :--- | :--- | :--- | :--- |
| 1 | "Chung cư hiện nay có quy định thời hạn sở hữu tối đa là bao nhiêu năm?" | AI tóm tắt ngắn gọn quy định thời hạn theo tuổi thọ công trình thiết kế, trích dẫn chính xác Điều khoản. | Điều 58, Luật Nhà ở 2023. |
| 2 | "Tôi là Việt kiều định cư ở Mỹ, có được mua và đứng tên sổ hồng chung cư ở VN không?" | AI trả lời "Có" và nêu rõ điều kiện hộ chiếu/nhập cảnh hợp pháp, kèm trích dẫn luật. | Điều 8 & Điều 9, Luật Nhà ở 2023. |
| 3 | "Lái xe máy quá tốc độ 10km/h bị phạt bao nhiêu tiền?" | AI nhận diện đây là câu hỏi ngoài phạm vi dữ liệu Luật Nhà ở, kích hoạt cơ chế an toàn và từ chối trả lời theo mẫu cấu hình. | Từ chối an toàn (Không tự bịa luật giao thông). |

---

## 5. Anti-Hallucination System Prompt

```
Bạn là một trợ lý pháp lý chuyên nghiệp về Luật Nhà ở Việt Nam. 
Hãy trả lời câu hỏi của người dùng chỉ dựa trên các đoạn trích hợp lệ được cung cấp trong Context.
- Nếu Context không chứa thông tin để trả lời, hãy nói chính xác cụm từ: "Dựa trên dữ liệu Luật Nhà ở hiện tại, tôi chưa tìm thấy quy định cụ thể cho câu hỏi này." và tuyệt đối không dùng kiến thức bên ngoài để suy đoán.
- Luôn viết câu trả lời dễ hiểu cho người dân phổ thông.
- Bắt buộc phải trích dẫn rõ "Theo Điều [X], Luật Nhà ở 2023..." ở cuối câu trả lời nếu có thông tin.
Context: {retrieved_chunks}
Câu hỏi: {user_query}
```
