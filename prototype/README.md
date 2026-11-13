# Prototype · T1 Y tế · Hỏi dược sĩ

- **File:** [`index.html`](index.html) (giao diện) và [`server.py`](server.py) (server nhỏ, chỉ để giữ key và gọi Claude; không đăng nhập, không cơ sở dữ liệu).
- **Chạy có Claude thật:** tạo `.env` ở gốc repo theo `.env.example` (`ANTHROPIC_API_KEY=...`; file này đã nằm trong `.gitignore`), rồi chạy `python3 server.py` trong thư mục này và vào <http://localhost:8767>.
- **Chạy không có key:** mở thẳng `index.html`. Trang tự dùng luật dự phòng, nhãn trên đầu báo "không gọi được".
- **Công cụ:** HTML/CSS/JS viết tay, có coding agent (Claude Code) hỗ trợ.
- **Lời gọi AI thật (bonus):** mỗi tin khách được gửi tới **Claude Haiku 5.5** qua `server.py` để **phân loại** (khẩn / kê đơn / hỏi liều / chuyển dược sĩ / sàng lọc / không phải thuốc) và trích câu làm bằng chứng. Key chỉ nằm ở server, không bao giờ xuống trình duyệt và không có trong repo.
  - Claude **chỉ được làm quyết định chặt hơn** bộ luật cứng trong trang, không bao giờ nới ra.
  - Claude **không viết câu gửi khách**: mọi câu khách đọc là mẫu cố định.
  - Câu trích nào không có trong tin của khách thì server bỏ đi.
  - Log của các lần gọi thật: [`ai-log.jsonl`](ai-log.jsonl) (33 lần gọi, tin dựng, không có key).
- **Phần mock:** màn hình dược sĩ, đồng hồ chờ, bản đồ cơ sở y tế và tên sản phẩm đều là dựng.

## So sánh trước / sau trên cùng một trang

Hàng nút **"So sánh trước / sau"** ở đầu trang chạy lại **cùng một ca** theo ba cách:

| Chế độ | Là gì | Ca ① bé li bì ra sao |
|---|---|---|
| **A · Hôm nay** | Sản phẩm thật hôm nay: AI chỉ trả lời giá, khuyến mãi; câu chuyên môn vào một hàng chờ chung | "Vui lòng chờ", vị trí 7; dược sĩ nhận ca "thường", không có tóm tắt |
| **B · AI làm theo lời khách** | Tích hợp sâu nhưng mọi tool ở mức tự làm, không có luật chạy trước | Thẻ "Hạ sốt trẻ em" + Đặt mua; tự lưu hồ sơ sức khoẻ |
| **C · Thiết kế của nhóm** | Spec §3–§4 | Khung đỏ đi khám / 115 ngay, dược sĩ nhận ca KHẨN |

Khung **"Chỗ trong code vừa chạy"** (trên cùng bên phải) hiện đúng nhánh code vừa chạy cho tin đó, kèm số dòng `index.html:NNN` đọc từ chính file đang chạy. Đỏ là cách đã loại (A, B), xanh là thiết kế của nhóm (C).

**Xem cả ba cột cùng lúc:** bấm **"Xem A · B · C song song"** (góc trên phải), hoặc mở `?view=compare`. Ba cột A · B · C chạy cạnh nhau; một ô nhập ở trên gửi **cùng một tin** cho cả ba. Mỗi cột có khung chat, khung code vừa chạy và màn hình dược sĩ của riêng nó. Chỉ cột C gọi Claude.

Ảnh: `compare-abc-1.png` (ca ① song song) · `compare-abc-2.png` (ca ② song song) · `compare-today.png` / `compare-naive.png` / `compare-ours.png` (từng chế độ, đủ màn hình).

## Kịch bản demo 4 phút

1. **(30") Lát cắt:** đọc câu lát cắt; chỉ nhãn số 1.
2. **(60") Ca ① ở màn hình song song** (`?view=compare`), bấm tin mẫu một lần: A: khách bé li bì nằm hàng chờ vị trí 7. B: AI bán hạ sốt. C: khung đỏ, 115, ca KHẨN bên dược sĩ. Mỗi lần đổi chế độ, chỉ khung code: dòng vàng là chỗ khác nhau.
3. **(60") Ca ② ở chế độ C:** khách gắt, AI không hỏi lại, chuyển dược sĩ. Chỉ dòng "Claude (AI thật)" (số 10) và nhánh code `routeFromAngry`.
4. **(40") Mức tự chủ:** ca ④, gợi ý thuốc nằm ở "chờ dược sĩ duyệt" (số 5). Trả lời câu "sai thì ai mất gì".
5. **(50") Ca lạ:** chọn "Ca lạ: tự gõ", gõ câu TA đưa, đọc khung code để nói nhánh nào chạy và vì sao.

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
