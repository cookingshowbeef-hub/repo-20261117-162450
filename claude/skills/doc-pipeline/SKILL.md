---
name: doc-pipeline
description: Làm phim tài liệu lời dẫn AI theo nhiều phong cách edit (style preset: Netflix lạnh, ấm cổ điển, explainer, noir...) bằng engine doc.py (Aral V2 / Pagpag / Oymyakon) - kịch bản, giọng đọc, b-roll, đồ họa Remotion, nhạc, rồi dựng sẵn timeline Adobe Premiere Pro (phim mới) hoặc DaVinci Resolve (phim cũ) để người dùng xem, chỉnh và tự xuất bản cuối. Use for any documentary film task in "D:\4. bot\documentary": new film, edit style (doc.py styles / style set, styles/*.json), voice, b-roll search, graphics, audio mix, Premiere timeline (premiere), Resolve review timeline (review/notes/push/pull), QC, credits, or when the user mentions doc.py, timeline.xml, timeline.fcpxml, Premiere, a film number like "phim 12", or Resolve markers/EDL.
---

# Doc pipeline - phim tài liệu lời dẫn AI

Engine nằm ở `D:\4. bot\documentary\06. Kịch bản & Công cụ Code - Scripts & Engine\03. Doc Pipeline - Quy trình Phim tài liệu\` (gọi tắt là ENGINE). Ổ đĩa có thể khác trên máy khác: tìm thư mục chứa `doc.py`.

**Đọc trước khi làm việc:**
- `ENGINE/docs/QUY_TRINH.md`: từng bước, các luật dựng.
- `ENGINE/docs/STYLES.md`: phong cách edit (style), khi chọn, chỉnh hoặc tạo style.
- `ENGINE/docs/QC_CHECKLIST.md`: duyệt phim.

Nếu máy chưa cài xong, làm theo `ENGINE/SETUP_CLAUDE.md` và chạy `python setup_check.py`.

## Phân vai (người dùng đã chốt)

- **Người dùng** viết và sửa lời dẫn (`04_Scripts_Code/Narration.md`). Họ cũng mở timeline Claude dựng sẵn (phim mới: Adobe Premiere Pro; phim cũ đến số 15: DaVinci Resolve), chỉnh, và tự xuất bản cuối với cấu hình riêng.
- **Claude** lo mọi việc còn lại:
  - kịch bản hình (`script_template.md`), kiểm chứng số liệu;
  - giọng đọc, tìm và chọn b-roll, ảnh;
  - đồ họa motion (Remotion), nhạc và tiếng động;
  - dựng file timeline đầy đủ (Premiere `timeline.xml`, hoặc Resolve `timeline.fcpxml` cho phim cũ), đọc góp ý, sửa và dựng vòng mới;
  - QC trên bản cuối.
- **Không render phim cuối bằng ffmpeg trừ khi được yêu cầu.** Bản cuối do Premiere (hoặc Resolve với phim cũ) xuất.

## Vòng làm việc

Lệnh chạy từ ENGINE; `<prj>` là số thư mục dự án, ví dụ `12`.

```
python doc.py styles                                   # các phong cách có sẵn (styles/*.json)
python doc.py new "12. Tên phim (20 Phút) - slug" "FILM TITLE" [style]   # style mặc định netflix-cold
python doc.py <prj> style [set <tên>]                  # xem / đổi phong cách của phim
python doc.py <prj> voice | timeline | script
python doc.py <prj> search <set> | pick px:ID="mô tả" ... | fetch | commons | freesound ...
python doc.py <prj> overlays | gfx stills | gfx
python doc.py <prj> lint           # mọi lỗi kế hoạch trong một lần, không ghi gì; sửa đến khi sạch
python doc.py <prj> build          # timeline + overlays + edit, khi lint đã sạch
python doc.py <prj> audio final
python doc.py <prj> premiere       # phim mới -> 05_Renders/premiere/timeline.xml (tự đủ: hình, vignette, đồ họa, HUD, âm thanh, marker)
python doc.py <prj> review         # = premiere nếu film.json có "editor": "premiere"; phim cũ -> 05_Renders/review/timeline.fcpxml
```

**Phim cũ, người dùng mở timeline Resolve:**
1. Trong Resolve: **File › Import › Timeline…**, chọn `timeline.fcpxml`.
2. Tick **Automatically import source clips into media pool** và **Use sizing information**.
3. Ở trang Color, gắn LUT `docpipe › <TITLE>_grade` cho các clip hình. Đó là track hình thấp nhất có clip, thường là V2 vì Resolve để V1 trống.

**Góp ý và bản cuối:**
- Người dùng xuất góp ý bằng **File › Export › Timeline Markers to EDL**.
- Claude chạy `python doc.py <prj> notes <file.edl>` để ra `REVIEW_NOTES.md`, sửa kế hoạch rồi chạy lại `review`.
- Khi người dùng gửi file đã xuất: `python doc.py <prj> qc "<file>"` rồi `credits`.

**Phim mới (từ 11/2026) giao bằng Adobe Premiere Pro.** `film.json` của phim mới có `"editor": "premiere"`, nên `review` chạy `premiere`:
```
python doc.py <prj> premiere       # -> 05_Renders/premiere/timeline.xml (XML FCP7: đủ shot, vignette, đồ họa, HUD, âm thanh, marker)
```
1. Trong Premiere: **File › Import…**, chọn `timeline.xml`. Sequence nằm trong bin mới.
2. Grade, làm một lần: **File › New › Adjustment Layer**, đặt lên **V2** phủ cả phim (V2 để trống sẵn cho việc này), rồi **Lumetri Color › Creative › Look** chọn `docpipe_<TITLE>_grade`. LUT đã được chép vào `%APPDATA%\Adobe\Common\LUTs\Creative`. Nếu không thấy, chọn Browse tới `05_Renders/premiere/grade.cube`.
3. Khi xuất, bật **Effects › Loudness Normalization** (true peak −1) nếu engine báo peak vượt −1 dBTP.
Phim cũ (đến phim 15) vẫn ở Resolve và không xuất lại. Vòng góp ý trên Premiere (đọc marker) chưa làm: người dùng tự chỉnh trên timeline.

`push`/`pull` chỉ là tùy chọn: chúng cần bridge `resolve_bridge` đang chạy trong Resolve. Import bằng script trên Resolve 21 beta hay bị hủy, nên mở tay là cách chính.

## Luật cứng (người dùng đã yêu cầu)

**Xuất bản và nguồn hình**
- Xuất **1080p**. Chỉ làm 4K khi người dùng yêu cầu.
- **Không dùng OpenAI để tạo ảnh.**
- **Stock trả phí** chỉ dùng khi người dùng đồng ý.

**Phong cách (style): mỗi phim chọn một, không cố định**
- Phong cách là file `ENGINE/styles/<tên>.json`; `film.json` ghi `"style": "<tên>"`. Thứ tự: mặc định engine ← style ← `film.json` (khóa trong `film.json` đè lên style). Có sẵn: `netflix-cold` (mặc định), `warm-vintage`, `clean-explainer`, `noir-crime`. Chi tiết: `docs/STYLES.md`.
- **Hỏi phong cách ở câu hỏi đầu tiên của chặng 1**, cùng lúc với ngôn ngữ phim (liệt kê bằng `doc.py styles`). Người dùng không nói thì dùng `netflix-cold`.
- Style quyết định: grade (contrast, lift, cool/warm, saturation, vignette, letterbox), độ dài cảnh, nhịp nghỉ, ducking; màu, font, chuyển động chữ, hạt phim của đồ họa Remotion; `rules` (đồ họa mỗi phút, độ phủ nhạc, số dB dưới giọng, số cue Suno); `notes` cho từng chặng (giọng, b-roll, đồ họa, prompt nhạc, tiếng động). **Ở mỗi chặng đọc `doc.py <prj> style` và làm theo `rules` + `notes` của style đó**, không áp con số của `netflix-cold` cho phim style khác.
- Người dùng muốn chỉnh chất một phim → ghi đè trong `film.json` (`render.grade`, `edit`, `gfx.palette`...). Muốn một phong cách mới ("giống video Y", "ấm hơn, cắt nhanh hơn") → tạo `styles/<tên>.json` với `"extends"` từ style gần nhất, render thử vài still để người dùng duyệt (cách làm trong `STYLES.md`), rồi mới áp vào phim.
- Không sửa hằng số màu/font trong `Film.jsx`/`Overlays.jsx` của phim mới: chúng đọc `src/style.json` do `gfx` ghi từ style. Phim cũ (không có `src/style.js`) giữ nguyên.
- Luôn giữ: lời dẫn AI, không phỏng vấn quay thật; đồ họa gắn đúng chữ trong lời dẫn.
- Mặc định `netflix-cold` (đã chốt với người dùng): đồ họa 2,5–3 mỗi phút (50–60 cho phim 20 phút), nhạc gần như liên tục (≥ 85% thời lượng lời dẫn), khoảng 15 dB dưới giọng.
- Nguồn nhạc (mọi style): cue chính tạo bằng Suno qua AI33 (`doc.py <prj> music make <cue> "<prompt>"`, ~3.600 credit AI33, 2 bản không lời), phần nối lấy từ kho 244 bài có sẵn (`music lib <từ khóa>`). **Không dùng vidIQ để tạo nhạc nữa** (17/11/2026). Chi tiết: `QUY_TRINH.md` mục 7.
- **B-roll** phải đúng nội dung từng câu và không lặp lại. Clip `generic` không bao giờ được gọi tên là một địa danh (luật trung thực địa điểm).

**Bảo mật**
- Key API đọc lúc chạy (biến môi trường, rồi `%USERPROFILE%\.docpipe\keys.env`). Thiếu key thì hỏi người dùng và thêm vào `keys.env`, không ghi vào file nào khác. **Không bao giờ in, ghi hay commit key.**
- Không đưa email hay thông tin cá nhân của người dùng ra dịch vụ ngoài.

**Thao tác cần hỏi trước**
- Hỏi trước khi xóa file. Ưu tiên di chuyển thay vì xóa. Không sửa kho footage gốc.
- Không cập nhật DaVinci Resolve lên 21.1 trở lên: bản Free sẽ mất Python và bridge.

## Một chặng = một session (bắt buộc)

Phim 12 tốn ~44% hạn mức 5 giờ của gói Pro. Phim 13 làm trọn trong một session nên tốn ~70–110%: hội thoại phình tới 373k token và mỗi lệnh lại gửi lại toàn bộ. Mục tiêu là ≤ 25% cho cả phim. Cách làm: **mỗi chặng chạy trong một session mới**, chỉ đọc file của chặng đó. Hết chặng thì ghi bàn giao và dừng; không làm tiếp chặng sau trong cùng session.

| Chặng | Đọc | Lệnh | Xong khi có |
|---|---|---|---|
| **1. Kịch bản + giọng** | kịch bản của người dùng, `QUY_TRINH.md` mục 0–2, `film.json` của phim mẫu, `doc.py styles` | `new ... <style>`, viết `Narration.md`, `film.json` (sections, `hold_after` theo chỗ nghỉ), `FACT_CHECK.md`, `voice`, `timeline` | `01_Voice/narration.json`, `05_Renders/timeline.json` |
| **2. Hình** | `media_spec.py`, `01_Voice/narration.json` (chỉ id + câu) | `search` từng bộ, `mini_sheets.py`, `commons`, rồi **giao agent Sonnet chọn** (`docs/PICKER_SONNET.md`), `fetch` | `02_B-Roll/candidates/picks.json` đủ hình; `03_Images/commons/sheets/usable.md`; tóm tắt của agent ghi vào bàn giao |
| **3. Dựng** | bàn giao chặng 2, `narration.json`, `picks.json`, `overlay_spec.py`/`audio_spec.py` của phim mẫu | `visuals.py` + `gen_template.py`, `lint` → `build`, `overlays`, `gfx stills` → `gfx`, `music make`/`music lib`, `audio_spec.py`, `audio final`, `premiere` (phim cũ: `review`) | `05_Renders/premiere/timeline.xml` (phim cũ: `review/timeline.fcpxml`) đã parse bằng minidom, không thiếu file |
| **4. Góp ý** (mỗi vòng một session) | file `.edl`, `REVIEW_NOTES.md` | `notes`, sửa spec, `build`, `review` | `timeline.fcpxml` mới |

Chặng 3 nặng nhất. Nếu cần, tách tiếp thành **3a** (đồ họa + nhạc, chạy song song được với chặng 2 vì chỉ cần `timeline.json`) và **3b** (kế hoạch hình, build, review).

**Bàn giao giữa các chặng**
- Cuối mỗi chặng, ghi `05_Renders/HANDOVER.md` trong dự án, tối đa ~20 dòng: đã xong gì, quyết định của người dùng (phong cách, ngôn ngữ, cách xử lý phỏng vấn, độ dài), file nào là đầu vào của chặng sau, việc còn lại, chỗ cần kiểm tra. Session đến từ session khác thì chép thêm một bản vào thư mục notes chung.
- Session mới **chỉ đọc `HANDOVER.md` và các file trong cột "Đọc"**. Không đọc lại `QUY_TRINH.md` hay toàn văn kịch bản nếu bàn giao đã đủ.
- Cuối chặng, gợi ý người dùng mở session mới cho chặng sau (thẻ "New task" kèm brief ngắn trỏ tới `HANDOVER.md`). Không tự làm tiếp.
- Chặng 1 tốn credit giọng; chặng 2 có thể cần stock trả phí; chặng 3 tốn credit AI33 cho nhạc Suno (kiểm tra `music credits` trước). Hỏi người dùng ở đầu chặng đó, không hỏi dồn từ trước.

**Trong một chặng vẫn giữ tiết kiệm**
- Trong lúc lệnh nền chạy, làm việc khác của cùng chặng (phim 13: viết `media_spec.py` và `overlay_spec.py` trong lúc tạo giọng).
- Không `ls` thư mục ứng viên (phim 13 in ra hàng nghìn tên file): dùng `wc -l` hoặc `grep -c`.
- Sửa spec bằng Python có `assert` chuỗi gốc, hoặc viết lại cả khối. Phim 13: một regex sửa gain trong `audio_spec.py` đã thay nhầm mốc thời gian.

**Tiết kiệm token**
- **Kịch bản người dùng đưa nên đúng định dạng engine** (ngôn ngữ đích, mỗi dòng 1 câu thoại, `## ` mỗi phần). Hỏi ngôn ngữ phim và phong cách ngay câu hỏi đầu tiên, cùng lúc xác nhận file kịch bản.
- **Duyệt hình bằng bảng ảnh nhỏ**: tối đa 4 ứng viên mỗi từ khóa, ô 240×135, 48 ô mỗi bảng: `python ENGINE/tools/mini_sheets.py "<thư mục dự án>" intro,birth 4` → `02_B-Roll/candidates/<set>/mini_N.jpg`. Không mở bảng `sheet_N.jpg` cỡ lớn của engine.
- **Phiên chính không tự xem bảng ảnh** (b-roll lẫn Commons): mỗi agent `model: "sonnet"` nhận 2–3 bộ theo mẫu trong `docs/PICKER_SONNET.md`. Agent xem ảnh, chạy `pick`, ghi `picker_notes.md` / `usable.md`, trả về ≤ 10 dòng. Nghi lựa chọn nào thì hỏi lại agent bằng SendMessage, không mở ảnh ở phiên chính.
- **Viết file lớn một lần**: tạo `script_template.md` bằng script Python sinh từ một dict `{line_id: "mã hình"}` (mẫu: `ENGINE/tools/per_line_template_film12.py`, sửa dict V, JOIN, ACTS cho phim mới), không viết tay rồi sửa nhiều lần. Không dán lại toàn văn lời dẫn vào hội thoại.
- **Đồ họa**: `gfx stills` chỉ render đồ họa mới hoặc đã sửa và gộp riêng chúng vào `stills/_review_N.jpg` (16 khung mỗi ảnh). Chỉ xem các ảnh `_review`, không mở từng PNG, không xem lại khung đã duyệt.
- **Lint trước build**: sửa template hoặc spec xong thì chạy `lint` (in khoảng 15 dòng, gom mọi lỗi và file thiếu), sửa hết rồi mới `build`. Không chạy `build` liên tục để dò lỗi từng cái một. `overlays` chỉ in bảng đồ họa khi có `-v`.
- **Lệnh chạy lâu chạy nền** (`commons`, `search`, `fetch`, `gfx`, `review`); không thăm dò log liên tục.
- Đọc ít: `tail`/`grep` thay vì in cả file JSON hay log.
- Góp ý nên đi qua EDL marker, hạn chế ảnh chụp màn hình.
- Không dò lỗi Resolve bằng cách đẩy hàng loạt file thử: parse FCPXML bằng Python (`xml.dom.minidom`) trước khi giao.

**Kế hoạch hình phải khớp lời** (lỗi người dùng bắt ở phim 12)
- **Phim mới dùng `"edit": {"mode": "timed"}`** (người dùng chọn): mỗi hình lên đúng mốc (`@"cụm từ"`, `@+giây` tính từ đầu khối, hoặc đầu câu), kéo dài đến mốc sau. Engine không tự dời, bỏ hay lấp hình; mốc lỗi thì `edit` dừng và in danh sách câu cần sửa. Sửa mốc trong dict V của script sinh template rồi chạy lại. Gửi người dùng `05_Renders/shots.csv` khi cần duyệt thời điểm. Chi tiết: `QUY_TRINH.md` mục 4.
- Chế độ cũ: `edit` chia đều thời gian khối cho các hình. Khối 2–3 câu làm hình lệch khỏi câu nói về nó.
- **Mỗi câu thoại là một khối `{{id}}`** (câu ≤ 2 s gộp với câu kế). Giữ nhịp nghỉ cũ bằng `timing.gap_block = gap_line`, cộng phần chênh vào `hold_after` của câu cuối mỗi ý và trừ khỏi `act_card`.
- **Neo hình vào chữ** cho mọi hình minh họa một chữ cụ thể ở giữa câu: `px:123@"double rainbow"` (cụm từ đúng như bản ghi Whisper). Không neo thì hình chỉ theo thứ tự, chia đều thời gian câu, và có thể lên trước hoặc sau chữ vài giây.
- **Mỗi khối ghi đủ số hình** ≈ (thời lượng câu + 0,75 s) / 3,6, đúng thứ tự lời nói. Thiếu hình thì engine bốc clip bất kỳ trong pool của cả phần (lạc đề); thừa thì hình cuối bị bỏ.

## Bài học Premiere (engine đã xử lý, nhớ khi gặp lại)

| Triệu chứng | Nguyên nhân | Cách engine xử lý |
|---|---|---|
| Import xong không có track âm thanh nào (phim 12) | Track stereo thiếu `currentExplodedTrackIndex`/`totalExplodedTrackCount`, Premiere bỏ cả phần audio | `premiere.py` ghi đủ thuộc tính như Premiere tự xuất |
| Premiere không mở được FCPXML | Premiere chỉ đọc XML FCP7 (xmeml) | `premiere.py` ghi xmeml riêng, dùng chung tính toán với `resolve.py` |
| Người dùng dán đường dẫn rút gọn (`12. ...born_in_north_korea\...`) | Premiere báo "Path does not exist" | Luôn đưa đường dẫn đầy đủ |

Premiere không tự fit clip khi import: Scale tính theo kích thước gốc (cover = max(W/w, H/h)·100). Center là phần của khung tính từ giữa, x sang phải, y xuống dưới.

## Bài học Resolve (engine đã xử lý, nhớ khi gặp lại)

| Triệu chứng | Nguyên nhân | Cách engine xử lý |
|---|---|---|
| "N clips were not yet found" | File ảnh tên toàn số (`000000.png`) bị đọc thành chuỗi ảnh | Plate đặt tên `plate_<n>_solid.png` |
| Một cảnh Media Offline giữa timeline | Timecode drop-frame (`;`) bị tính lệch | Remux không timecode `links/*_notc.mp4` |
| Resolve không nhận clip 25/29.97 fps hoặc có TC | Khai format sai | Mỗi asset một `<format>` theo file gốc (`src_info`) |
| Ảnh tĩnh bị viền đen | Resolve bỏ qua `adjust-conform`, luôn fit | Scale nhân thêm tỉ lệ cover/fit |
| Marker trên clip bị mất | Resolve bỏ marker gắn vào clip | Marker gắn vào gap (marker timeline) |
| Ghi PNG thất bại im lặng trên đường dẫn tiếng Việt | `cv2.imwrite` không ghi được đường dẫn Unicode | `cv2.imencode(...)[1].tofile(path)` |
| Tên file có chữ Nga/dấu, đường dẫn ≥ 240 byte | Resolve có thể không tìm thấy | Hardlink tên ASCII trong `review/links` |
| "DOM parser error. Line N" khi import | Câu thoại có dấu `"` ghi thẳng vào `note=` của marker | `escape()` trong `resolve.py` escape cả `"` (đã sửa, phim 12) |

## Bài học engine khác (phim 12)

| Triệu chứng | Nguyên nhân | Đã sửa |
|---|---|---|
| `audio final` lỗi `'NoneType' has no attribute 'rindex'` | stderr của ffmpeg có đường dẫn tiếng Việt, Python giải mã bằng cp1258 thì luồng đọc chết | `subprocess.run(..., encoding="utf-8", errors="replace")` trong audio/qc/render/resolve/voice |
| `commons` chờ "throttled 615s" liên tục | Xin ảnh thu nhỏ 2560 px, không phải cỡ chuẩn của Wikimedia | `iiurlwidth=1920`; giữ số ảnh mỗi chủ đề ≤ 30 |
| `geo_build.py` báo không thấy file Natural Earth | Đường dẫn `..\..\..` vượt MAX_PATH | `os.path.normpath` (đã sửa trong template) |
| Suno (AI33) trả lỗi bộ lọc nội dung | Prompt nhắc chủ đề nhạy cảm | Không gửi lại nguyên prompt; tả cảm xúc trung tính hơn hoặc lấy bài trong kho (`music lib`) |
| Tải nhạc Suno bị 403 | CDN Suno chặn trình tải mặc định | `music.py` đã gửi header trình duyệt; tự tải thì thêm `User-Agent` |
| Nhạc chỉ thấp hơn giọng 10–13 dB | Gain đặt theo LUFS của file | Đo bằng stems (`audio.mix(..., stems=dir)`), chỉnh gain từng đoạn cho chênh ≈ 15 dB |

**Muốn biết Resolve không tìm thấy file nào:** quét `src=` trong FCPXML, rồi so với file thật và quy tắc đặt tên. Đừng thử từng clip một trong Resolve.

## Sửa engine

- Lỗi chung thì sửa trong `ENGINE/docpipe/`, không sửa bản chép trong từng dự án.
- Đặt `DOC_OUT=<thư mục tạm>` để chạy thử mà không đụng `05_Renders` của dự án.
- Phim mẫu đã kiểm chứng là dự án `11` (Oymyakon): `DOC_OUT=<tạm> python doc.py 11 build` phải chạy được trong vài giây.
- Thông số chung của phong cách thì sửa trong `styles/`, không đưa vào `ctx.DEFAULTS` (DEFAULTS giữ đúng như cũ để phim không có `"style"` không đổi). Grade, vignette và letterbox dùng chung `docpipe/style.py` (`curve`, `vignette`) cho render, LUT và PNG vignette.
