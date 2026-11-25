# Phong cách edit (style)

Mỗi phong cách là một file `styles/<tên>.json`. Phim chọn phong cách bằng một dòng trong `film.json`:

```json
"style": "warm-vintage"
```

Thứ tự áp dụng: **mặc định của engine ← style ← `film.json`**. Style quyết định "chất" của cả phim. Muốn chỉnh riêng một phim (ví dụ màu nhấn khác, cắt chậm hơn), ghi đè đúng khóa đó trong `film.json`. Phim không có `"style"` (phim cũ đến phim 17) chạy như trước, không đổi gì.

## Người dùng đưa kịch bản kèm file style

```
python doc.py new "18. Tên (20 Phút) - slug" "TITLE" --script kich_ban.md --style style_cua_toi.json
```

| `--style` là | Engine làm gì |
|---|---|
| bỏ trống | Dùng mặc định `netflix-cold` (template mẫu) |
| tên preset (`noir-crime`) | Dùng preset trong `styles/` |
| file `.json` | Kiểm tra (JSON hợp lệ, khóa gõ sai, mã màu), chép thành `04_Scripts_Code/style.json`; `film.json` ghi `"style": "style.json"` |
| file mô tả `.md/.txt/.docx/.pdf` hoặc ảnh | Chép thành `04_Scripts_Code/STYLE_BRIEF.<ext>`; phim tạm dùng `netflix-cold` đến khi Claude viết `style.json` từ brief |

`--script`: file `.md/.txt` vào thẳng `Narration.md`; file khác (`.docx`, `.pdf`) giữ là `SCRIPT_SOURCE.<ext>` để Claude chuyển.

**Tự viết file style:** chép [`styles/_template.json`](../styles/_template.json), sửa giá trị, xóa dòng không cần (dòng bị xóa lấy từ style trong `"extends"`). Các khóa bắt đầu bằng `_` chỉ là ghi chú.

## Lệnh khác

```
python doc.py styles                         # các preset có sẵn
python doc.py <prj> style                    # style của phim và mọi thông số nó cho ra
python doc.py <prj> style set warm-vintage   # đổi sang preset
python doc.py <prj> style set D:\style.json  # đổi sang file của người dùng (chép vào 04_Scripts_Code/style.json)
python doc.py <prj> style set style.json     # dùng style.json đã có trong 04_Scripts_Code (sau khi Claude viết từ brief)
```

Đổi style giữa chừng thì chạy lại theo thứ tự `lint` → `build` → `gfx stills --all` (duyệt) → `gfx` → `audio final` → `premiere`. Style mới có thể đổi nhịp nghỉ (`timing`), nên `lint` có thể báo đồ họa chồng nhau; dời mốc trong `overlay_spec.py` cho hết lỗi.

## Có sẵn

| Style | Hợp với | Chất |
|---|---|---|
| `netflix-cold` | mặc định, khoa học, thiên nhiên, địa lý | Tối, lạnh, giảm bão hòa; Jost mảnh + Georgia nghiêng; nhấn xanh băng; 2,5–3 đồ họa/phút; nhạc ≥ 85% |
| `warm-vintage` | lịch sử, tiểu sử, hoài niệm | Ấm như phim nhựa, hạt rõ; serif Lora; nhấn hổ phách; cảnh 4,4 s; 1,8–2,5 đồ họa/phút; piano và dây |
| `clean-explainer` | giải thích, kinh tế, công nghệ | Sáng, bão hòa cao; chữ hiện nhanh, không mờ; nhấn vàng; cảnh 2,9 s; 3–4 đồ họa/phút; nhạc 95–115 bpm |
| `noir-crime` | true crime, bí ẩn, chiến tranh | Gần đen trắng, tương phản cao, **letterbox 2.39**; chữ mono; nhấn đỏ; cảnh 4,2 s; nhạc 70%, drone |

## Cấu trúc một file style

Mọi khóa đều không bắt buộc. `"extends"` lấy một style khác làm nền, rồi chỉ ghi những gì khác.

```jsonc
{
 "extends": "netflix-cold",
 "label": "Tên hiển thị", "description": "Một câu tả chất của style",

 // ---- gộp thẳng vào thông số phim (cùng khóa với film.json)
 "timing":  {"gap_line": 0.75, "gap_block": 1.8, "act_card": 5.5, "end_text": 20},   // nhịp nghỉ giữa câu, giữa ý, thẻ tên phần
 "edit":    {"target": 3.6, "min": 2.5, "max": 5.0, "fade": 0.45},                  // độ dài cảnh (giây)
 "overlay": {"full_hold": 6.0},                                                      // đồ họa toàn màn hình đứng tối đa
 "render":  {"grade": {
     "contrast": 0.2,    // độ cong S-curve (0 = phẳng, 0,35 = gắt)
     "lift": 3,          // nâng đen (0–12; cao = mờ như phim cũ)
     "cool": 0.03,       // ngả xanh
     "warm": 0.0,        // ngả cam (ngược với cool)
     "saturation": 0.9,  // 1 = giữ nguyên, 0,45 = gần đen trắng
     "vignette": 0.22,   // tối bốn góc
     "letterbox": 0      // 0 = tắt; 2.39 hoặc 2.0 = viền đen trên dưới
 }},
 "audio":   {"lufs": -14, "duck_db": 6},

 // ---- đồ họa Remotion (engine ghi ra 06_Graphics/remotion/src/style.json)
 "gfx": {
  "palette": {"text": "#EEF1F4", "dim": "#AEB8C2", "accent": "#6FAEDB", "accent_text": "#A9D6F5",
              "danger": "#E0563F", "danger_text": "#EE6A50", "warm": "#E8A15A", "bg": "#0B0E12", "land": "#1E252D", "sea": "#0B0E12"},
  "fonts": {"sans":  {"family": "Jost", "fallback": "sans-serif", "files": [{"file": "fonts/Jost-wght.ttf", "weight": "100 900"}]},
            "serif": {"family": "Georgia", "fallback": "serif", "files": []},          // files rỗng = font hệ thống
            "mono":  {"family": "Courier New", "fallback": "monospace", "files": []}},
  "fonts_vi": { ... },   // thay fonts khi voice.language = "vi" (Be Vietnam Pro + Lora, đủ dấu)
  "motion": {"ease_out": [0.16, 1, 0.3, 1], "ease_inout": [0.65, 0, 0.35, 1],
             "rise": {"dy": 22, "blur": 7, "len": 0.9},   // chữ trồi lên: quãng (px), độ mờ lúc đầu, thời gian (s)
             "tracking": 1.0},                            // nhân độ giãn chữ (0,6 = sát hơn)
  "text_shadow": "0 2px 22px rgba(0,0,0,0.75), 0 1px 3px rgba(0,0,0,0.6)",
  "grain": 0.06,         // hạt phim trên thẻ toàn màn hình (0 = tắt)
  "scrim": 1.0           // độ tối của lớp nền sau chữ trên footage
 },

 // ---- luật nhà: lint và audio báo theo các số này (cảnh báo, không chặn)
 "rules": {"gfx_per_min": [2.5, 3.0], "music_coverage": 0.85, "music_under_voice_db": 15, "suno_cues": [4, 6]},

 // ---- hướng dẫn cho Claude ở từng chặng
 "notes": {"narration": "...", "broll": "...", "graphics": "...", "music": "... (giọng điệu prompt Suno)", "sound": "..."}
}
```

Font phải có trong `templates/remotion/public/fonts` (file `.ttf`/`.woff2`) hoặc là font hệ thống Windows. Thêm font mới: chép file vào thư mục đó, rồi khai trong `gfx.fonts.<sans|serif|mono>.files`.

## Tạo style mới

Người dùng có thể nói:
- "phim này dùng style X", hoặc "chỉnh style cho ấm hơn hoặc cắt nhanh hơn" → Claude sửa `film.json` hoặc `04_Scripts_Code/style.json` (một phim), hoặc preset trong `styles/` (mọi phim dùng nó);
- "tạo style mới giống video Y" (gửi link, ảnh chụp hoặc brief) → Claude viết `04_Scripts_Code/style.json` cho phim đó, với `"extends"` từ style gần nhất, chỉ ghi phần khác. Muốn dùng lại cho phim sau thì chép vào `styles/<tên>.json` thành preset.

Cách làm:
1. Chọn style nền gần nhất, ghi `grade`, `palette`, `fonts`, `motion`, nhịp cắt, `rules` và `notes`.
2. Thử trên một phim có sẵn mà không đụng phim đó: chép `06_Graphics/remotion` của phim sang thư mục tạm, ghi `src/style.json` cho style mới, chạy `node render_ov.mjs stills` với `DOC_OUT` trỏ tới một `overlays.json` vài đồ họa, rồi xem ảnh ghép. Grade xem bằng LUT `grade.cube` do `premiere` tạo.
3. Người dùng duyệt xong thì commit file style vào repo.

## Giới hạn hiện tại

- Bản đồ và các hình minh họa riêng (núi, nhiệt kế…) có vài màu vẽ cứng trong JSX; chỉ đường viền và chữ đổi theo `palette`.
- Cỡ chữ và độ đậm từng loại đồ họa nằm trong JSX; style chỉ đổi font, độ giãn và chuyển động.
- Chuyển cảnh giữa các shot vẫn là cắt thẳng (fade chỉ ở thẻ tựa và thẻ phần).
- Phim cũ có bản `Film.jsx` riêng với hằng số màu; chúng không đọc `style.json` (engine bỏ qua khi thiếu `src/style.js`).
