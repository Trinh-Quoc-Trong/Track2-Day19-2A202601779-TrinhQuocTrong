# Lab 19 Reflection
**Họ và tên:** Trịnh Quốc Trọng
**MSSV:** 2A202601779


**1. Which mode wins on what queries and why?**
- **Keyword (BM25)** vượt trội với **exact match**. Thuật toán tối ưu cho việc tìm kiếm chính xác các từ khóa đặc thù (mã định danh, thuật ngữ kỹ thuật) dựa trên tần suất (TF-IDF), không gây ra hiện tượng hallucination sang các từ đồng nghĩa.
- **Semantic (Vector)** vượt trội với **paraphrase**. Mô hình biểu diễn văn bản trong latent space, cho phép tìm kiếm dựa trên ngữ nghĩa tổng thể (topic/intent) ngay cả khi không có sự trùng lặp từ vựng (zero lexical overlap) giữa câu truy vấn và văn bản.
- **Hybrid (RRF)** chiến thắng ở **mixed queries** và đạt hiệu suất trung bình cao nhất. Thuật toán dung hòa điểm mạnh của cả hai phương pháp: duy trì độ chính xác của Keyword và mở rộng recall của Semantic.

**2. When would you not use hybrid?**
Không sử dụng Hybrid trong các trường hợp:
- **Ngân sách độ trễ (Latency) cực thấp:** Hybrid yêu cầu tính toán song song hai luồng tìm kiếm và kết hợp kết quả (RRF), làm tăng đáng kể P99 latency.
- **Giới hạn tài nguyên:** Quá trình embedding realtime ở phía client/server tiêu tốn nhiều CPU/GPU và RAM so với inverted index của hệ thống BM25 truyền thống.
- **Dữ liệu cấu trúc/Đặc thù cao:** Các hệ thống tra cứu mã số, log file, hoặc database có cấu trúc cố định chỉ cần Keyword/SQL lookup để đạt 100% accuracy.
