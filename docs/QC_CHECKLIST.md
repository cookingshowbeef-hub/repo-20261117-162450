# Checklist duyệt phim

Chạy `python doc.py <dự án> qc` trước. Mọi dòng **FIX** trong `05_Renders/QC_REPORT.md` phải sửa xong rồi mới xem bằng mắt.

## A. Máy kiểm tra (QC_REPORT.md)

- [ ] Không có cảnh ngắn hơn 2,2 s. Tối đa 3 cảnh dài quá 6 s.
- [ ] Không có hình nào lặp lại trong cùng một khối. Clip dùng ≤ 2 lần, ảnh dùng ≤ 3 lần cả phim. Clip không quay lại trong vòng 60 s.
- [ ] Số hình khác nhau ≥ 75% số cảnh.
- [ ] Ảnh tĩnh nào cũng có chuyển động.
- [ ] Hình dưới lower third phải đúng thứ lower third gọi tên. Clip generic không được nằm dưới một tên riêng.
- [ ] Mật độ đồ họa 2,5–3/phút (50–60 cho phim 20 phút).
- [ ] Đồ họa toàn màn hình không đứng yên quá 6 s sau nhịp cuối.
- [ ] Giữa thẻ tựa và thẻ phần đầu có ≥ 1,5 s màn đen.
- [ ] Nhạc phủ ≥ 85% lời dẫn. Bản trộn cuối đạt −14 ±1 LUFS, true peak ≤ −1,5 dBFS.
- [ ] Phim xuất ra 1920×1080, đúng số khung hình.

## B. Mắt kiểm tra (xem hết phim, ghi lỗi kèm mốc thời gian)

**Hình**
- [ ] Hình có đúng nội dung câu đang nói không? (Nói về nhà văn thì phải là ảnh, sách, chữ ký của ông ấy, không phải một tấm ảnh lặp lại nhiều lần.)
- [ ] Có sai nơi chốn không? Kiểm tra cờ, biển báo, biển số xe, chữ viết khác ngôn ngữ, đồ vật không thuộc vùng đó.
- [ ] Có logo, watermark, chữ quảng cáo, giao diện ứng dụng nào lọt vào không?
- [ ] Có cảnh nào quay cận mặt trẻ em không? Nếu có thì bỏ.
- [ ] Có clip mờ, giật, rung, phơi sáng hỏng không?
- [ ] Ảnh đã gắn địa điểm có thật đúng nơi đó, đúng năm đó không? Ảnh lưu trữ phải có ngày trên màn hình.

**Nhịp**
- [ ] Hai phút đầu: cảnh có đều không, có chỗ nào quá nhanh hay quá lâu không?
- [ ] Có đoạn nào trên 10 s không có cắt cảnh và không có chuyển động không?
- [ ] Có hình nào chớp lộ ra giữa hai đồ họa toàn màn hình không?
- [ ] Thẻ tựa, khoảng đen rồi thẻ phần có đủ chỗ thở không?

**Đồ họa**
- [ ] Chữ có đúng chính tả không? Con số có khớp `FACT_CHECK.md` không?
- [ ] Đồ họa có xuất hiện đúng chữ đang nói không?
- [ ] Chữ có đè lên mặt người hoặc chi tiết quan trọng không? Có thiếu nền tối làm chữ khó đọc không?

**Âm thanh**
- [ ] Tiếng nền (động cơ, gió) có át giọng đọc không?
- [ ] Nhạc có đều dưới giọng không, có chỗ nào hụt hay đột ngột to lên không?
- [ ] Tên riêng có được đọc đúng không?
- [ ] Các chỗ im lặng có đúng là chủ ý không?

## C. Trước khi đăng

- [ ] `python doc.py <dự án> credits` đã chạy lại sau lần sửa cuối, và CREDITS.md đã dán vào phần mô tả.
- [ ] Đã xóa các bản `_prepatch.mp4` đã duyệt xong (tự tay xóa).
