# Prototype · T1 Y tế · Hỏi dược sĩ

- **File:** [`index.html`](index.html). Một file HTML, không backend, không đăng nhập, không gọi API.
- **Chạy:** mở trực tiếp `index.html`, hoặc `python3 -m http.server 8767` trong thư mục này rồi vào <http://localhost:8767>.
- **Công cụ:** HTML/CSS/JS viết tay, có coding agent (Claude Code) hỗ trợ.
- **Phần mock:** quyết định của trợ lý do một bộ luật sàng lọc trong file chạy, không phải model, để mỗi lần demo bấm ra cùng một kết quả. Màn hình dược sĩ, đồng hồ chờ, bản đồ cơ sở y tế và tên sản phẩm đều là dựng.
- **Lời gọi AI thật:** không có.

## Bấm qua ca khó

1. Chọn **"① Bé 2 tuổi sốt, li bì"**, rồi bấm tin nhắn gợi ý màu xanh. Trợ lý hiện khung đỏ đi khám / gọi 115 và không có thẻ sản phẩm. Bên phải, ca **KHẨN** vào màn hình dược sĩ, ghi rõ việc phải làm: gọi lại khách trong 2 phút.
2. Chọn **"② Mẹ 75 tuổi ho, khách gắt"**. Trợ lý hiện thẻ sàng lọc. Bấm câu trả lời gắt: trợ lý không hỏi lại, không "bán đại", mà chuyển dược sĩ kèm những gì khách đã kể.
3. Chọn **"④ Đau họng 2 ngày"**. Bấm câu điền sẵn thẻ sàng lọc để thấy gợi ý thuốc nằm ở trạng thái **chờ dược sĩ duyệt**. Có nút "giả lập quá 5 phút" để xem đường đi khi không ai duyệt. Bấm "Duyệt & gửi" bên màn hình dược sĩ, thẻ sản phẩm mới đến khách, kèm hỏi có lưu ghi chú sức khoẻ không.
4. **Ca lạ:** chọn "Ca lạ: tự gõ" và gõ bất kỳ câu nào. Có sẵn câu mẫu: thuốc kê đơn, bà bầu, hỏi liều.

## Ảnh có đánh số

| Ảnh | Ca |
|---|---|
| ![ca 1](screen-1.png) | `screen-1.png`: ca ①, bé 2 tuổi li bì. Thấy các số 1, 2, 3, 8, 9 |
| ![ca 4](screen-4.png) | `screen-4.png`: ca ④, sau khi dược sĩ duyệt. Thấy các số 1, 2, 6 (nút đặt), 7, 8, 9 |

Số 4 (thẻ sàng lọc) và số 5 (đang chờ duyệt) hiện khi bấm ca ② hoặc ④ trên prototype. Ý nghĩa từng số nằm ở bảng chú thích bên phải màn hình và ở `spec.md` §5.
