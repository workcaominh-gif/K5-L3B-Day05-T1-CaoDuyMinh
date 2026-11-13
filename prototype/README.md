# Prototype · T1 Y tế · Hỏi dược sĩ

- **File:** [`index.html`](index.html) (giao diện) và [`server.py`](server.py) (server nhỏ, chỉ để giữ key và gọi Claude; không đăng nhập, không cơ sở dữ liệu).
- **Chạy có Claude thật:** tạo `.env` ở gốc repo theo `.env.example` (`ANTHROPIC_API_KEY=...`; file này đã nằm trong `.gitignore`), rồi chạy `python3 server.py` trong thư mục này và vào <http://localhost:8767>.
- **Chạy không có key:** mở thẳng `index.html`. Trang tự dùng luật dự phòng, nhãn trên đầu báo "không gọi được".
- **Công cụ:** HTML/CSS/JS viết tay, có coding agent (Claude Code) hỗ trợ.
- **Lời gọi AI thật (bonus):** mỗi tin khách được gửi tới **Claude Haiku 5.5** qua `server.py` để **phân loại** (khẩn / kê đơn / hỏi liều / chuyển dược sĩ / sàng lọc / không phải thuốc) và trích câu làm bằng chứng. Key chỉ nằm ở server, không bao giờ xuống trình duyệt và không có trong repo.
  - Claude **chỉ được làm quyết định chặt hơn** bộ luật cứng trong trang, không bao giờ nới ra.
  - Claude **không viết câu gửi khách**: mọi câu khách đọc là mẫu cố định.
  - Câu trích nào không có trong tin của khách thì server bỏ đi.
  - Log của các lần gọi thật: [`ai-log.jsonl`](ai-log.jsonl) (13 lần gọi, tin dựng, không có key).
- **Phần mock:** màn hình dược sĩ, đồng hồ chờ, bản đồ cơ sở y tế và tên sản phẩm đều là dựng.

## Bấm qua ca khó

1. Chọn **"① Bé 2 tuổi sốt, li bì"**, rồi bấm tin nhắn gợi ý màu xanh. Trợ lý hiện khung đỏ đi khám / gọi 115 và không có thẻ sản phẩm. Bên phải, ca **KHẨN** vào màn hình dược sĩ, ghi rõ việc phải làm: gọi lại khách trong 2 phút.
2. Chọn **"② Mẹ 75 tuổi ho, khách gắt"**. Trợ lý hiện thẻ sàng lọc. Bấm câu trả lời gắt: trợ lý không hỏi lại, không "bán đại", mà chuyển dược sĩ kèm những gì khách đã kể.
3. Chọn **"④ Đau họng 2 ngày"**. Bấm câu điền sẵn thẻ sàng lọc để thấy gợi ý thuốc nằm ở trạng thái **chờ dược sĩ duyệt**. Có nút "giả lập quá 5 phút" để xem đường đi khi không ai duyệt. Bấm "Duyệt & gửi" bên màn hình dược sĩ, thẻ sản phẩm mới đến khách, kèm hỏi có lưu ghi chú sức khoẻ không.
4. **Ca lạ:** chọn "Ca lạ: tự gõ" và gõ bất kỳ câu nào. Có sẵn câu mẫu: thuốc kê đơn, bà bầu, hỏi liều.

## Ảnh có đánh số

| Ảnh | Ca |
|---|---|
| ![ca 1](screen-1.png) | `screen-1.png`: ca ①, bé 2 tuổi li bì. Thấy các số 1, 2, 3, 8, 9 |
| ![claude](screen-claude.png) | `screen-claude.png`: ca lạ "bé nằm im, không chịu bú". Luật từ khoá **không** bắt được, Claude thật bắt được và nâng lên khẩn (số 10) |
| ![ca 4](screen-4.png) | `screen-4.png`: ca ④, sau khi dược sĩ duyệt. Thấy các số 1, 2, 6 (nút đặt), 7, 8, 9 |

Số 4 (thẻ sàng lọc) và số 5 (đang chờ duyệt) hiện khi bấm ca ② hoặc ④ trên prototype. Ý nghĩa từng số nằm ở bảng chú thích bên phải màn hình và ở `spec.md` §5.
