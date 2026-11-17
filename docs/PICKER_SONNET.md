# Chọn b-roll và ảnh bằng agent Sonnet (chặng 2)

Phiên chính không mở bảng ảnh. Mỗi agent nhận **2–3 bộ b-roll** (khoảng 30–45 từ khóa; mỗi agent tốn một khoản cố định khoảng 60–80k token Sonnet nên gộp bộ thì rẻ hơn) hoặc một nhóm chủ đề ảnh Commons. Agent chạy với `model: "sonnet"`, `subagent_type: "general-purpose"`. Agent xem ảnh, chạy `pick`, ghi danh sách ảnh dùng được, rồi trả về **tối đa 10 dòng**. Ảnh không bao giờ vào hội thoại chính.

Chuẩn bị trước khi giao:
- `python doc.py <prj> search <set>` rồi `python tools/mini_sheets.py "<dự án>" <set> 4` để có `02_B-Roll/candidates/<set>/mini_N.jpg`.
- `python doc.py <prj> commons` để có `03_Images/commons/sheets/<topic>.jpg`.
- Có thể giao nhiều agent cùng lúc, mỗi agent một bộ; chúng chỉ ghi vào `picks.json` qua lệnh `pick`, mỗi lệnh ghi thêm, không xóa.

Phiên chính đọc kết quả tóm tắt và ghi vào `HANDOVER.md`. Nếu nghi một lựa chọn, hỏi lại agent đó bằng SendMessage thay vì tự mở ảnh.

## Mẫu yêu cầu: b-roll

Thay `<...>` rồi gửi nguyên văn làm `prompt`:

```
You vet stock-video candidates for a Netflix-style documentary, "<FILM TITLE>", about <one-line subject>.
Project: <full project path>
Engine: D:\4. bot\documentary\06. Kịch bản & Công cụ Code - Scripts & Engine\03. Doc Pipeline - Quy trình Phim tài liệu
Sets (do them one after another, same rules): <set>: <the comment above the set in media_spec.py>; <set2>: <comment>; ...

The film needs about one picture every 3.6 s, so most queries need 2-3 usable clips. Coverage matters as much as precision.
1. Read every 02_B-Roll/candidates/<set>/mini_N.jpg with the Read tool. Each tile is labelled "<code> <query>" (code = px:<id> or pb:<id>).
   02_B-Roll/candidates/<set>/candidates.json gives each code's full query, page slug and author.
2. For each query, pick 2-3 tiles that fit what the query says (the best first). A tile that shows the idea but not exactly
   (an empty corridor for "crowded corridor", a generic office for a specific one) is still picked, with " ~" at the end of its
   description and a note on why. Pick nothing for a query only when every tile breaks a rule in step 3 or is plainly off-topic.
3. Reject outright: flags or signs of another country; visible text in the wrong language; logos or watermarks;
   blurred, low-detail or off-topic frames (e.g. a hotel room standing in for a classroom); close-up faces of children.
4. Place rule: a clip is "generic" unless its slug in candidates.json names the place itself. Only then add --where "<Place>".
   A look-alike street is never captioned as the place. A clip whose slug names a place in another country (Istanbul, Lagos,
   an Indian city) stays generic but gets " ~" and "(filmed in <place>)" in its note, so it is used only to fill.
5. Save the picks with the engine, one command per place (generic in one command):
   cd "<engine>" && python doc.py "<project>" pick px:123="short description" pb:45="short description"
   cd "<engine>" && python doc.py "<project>" pick px:678="Yakutsk street" --where "Yakutsk"
   Descriptions: 2-6 English words of what is on screen.
6. Write 02_B-Roll/candidates/<set>/picker_notes.md per set: one line per query (picked codes, ~ marks, or "none: <why>"), plus every rejection with its reason.
7. Reply in at most 10 lines: per set the number of picks and of "~" picks, the queries left empty (list them), anything the director should look at.
   No image descriptions beyond that.
```

## Mẫu yêu cầu: ảnh Commons

```
You vet archival photos (Wikimedia Commons) for a Netflix-style documentary, "<FILM TITLE>".
Project: <full project path>
Topics: <topic1, topic2, ...>

1. Read 03_Images/commons/sheets/<topic>.jpg for each topic with the Read tool. Each photo carries its number (#n).
   03_Images/commons/sheets/index.json maps "<topic>#n" to the file name; 03_Images/commons/manifest.json has title and description.
2. Keep a photo only if it clearly shows the topic, is sharp enough for a 1920x1080 frame with a slow push-in, and has no
   watermark, collage, map screenshot, text-heavy poster or close-up face of a child. Keep a place photo only if its title or
   description names that place.
3. Write 03_Images/commons/sheets/usable.md: per topic, the kept codes as photo:<topic>#n with 3-6 words each, best first, then
   the rejected numbers with a short reason.
4. Reply in at most 10 lines: kept count per topic and any topic with fewer than 3 usable photos.
```

## Ghi chú

- Sonnet rẻ hơn mô hình của phiên chính, và ảnh nằm trong ngữ cảnh của agent, nên hội thoại chính không phình theo số bảng ảnh.
- Thử trên phim 13 (bộ hospital + migrants, một agent): 76 clip so với 75 phim đã chọn, giữ 73% lựa chọn cũ; 29 clip đúng ý (không `~`) thì 25 trùng phim 13. Khoảng 100k token Sonnet cho cả hai bộ, bằng lần thử một bộ trước đó, nên gộp bộ giảm một nửa chi phí mỗi bộ.
- Mô tả kết thúc bằng ` ~` là hình gần đúng: dùng được để lấp chỗ, nhưng ưu tiên hình khác khi gán vào kịch bản, và để ý ở vòng góp ý.
- Agent làm sai thì sửa thẳng `picks.json` (xóa mã) hoặc chạy lại `pick` với mô tả đúng; không cần render lại gì.
- Mắt người vẫn là bước duyệt cuối: các lựa chọn hiện trên timeline Resolve ở vòng góp ý (`review`).
