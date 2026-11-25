# Quy trình làm phim tài liệu (rút từ Aral V2, Pagpag, Oymyakon)

Phong cách: phim tài liệu kiểu Netflix, **lời dẫn AI**, không phỏng vấn quay thật. Tư liệu là stock miễn phí (Pexels, Pixabay), ảnh Wikimedia Commons, ảnh NASA và đồ họa Remotion. Mặc định xuất **1080p**; chỉ xuất 4K khi được yêu cầu.

Mọi bước chạy bằng một lệnh, từ thư mục engine:

```
cd "D:\4. bot\documentary\06. Kịch bản & Công cụ Code - Scripts & Engine\03. Doc Pipeline - Quy trình Phim tài liệu"
python doc.py <dự án> <bước> [tham số]
```

`<dự án>` có thể là số thư mục (`11`), một phần tên (`Oymyakon`) hoặc đường dẫn đầy đủ. Gõ `python doc.py` không kèm gì để xem danh sách bước.

---

## 0. Tạo dự án

```
python doc.py new "12. Tên phim (20 Phút) - slug" "FILM TITLE" [style]
python doc.py styles                       # các phong cách có sẵn
```

**Chọn phong cách trước tiên** (hỏi người dùng cùng lúc với ngôn ngữ phim). Phong cách là một file `styles/<tên>.json`, quyết định grade, letterbox, nhịp cắt, nhịp nghỉ, màu, font và chuyển động đồ họa, mật độ đồ họa, độ phủ nhạc, cùng ghi chú cho từng chặng (`notes`: b-roll, đồ họa, prompt nhạc). Mặc định là `netflix-cold`. Đổi sau: `doc.py <prj> style set <tên>`; xem thông số: `doc.py <prj> style`. Chi tiết và cách tạo phong cách mới: `docs/STYLES.md`. **Mọi con số "mục tiêu" bên dưới là của `netflix-cold`; phim dùng style khác thì theo `rules` và `notes` của style đó.**

Lệnh này tạo các thư mục `01_Voice … 07_Audio` và chép file mẫu vào `04_Scripts_Code`. Nó cũng tạo `06_Graphics/remotion`, có thư viện đồ họa và `node_modules` dùng chung qua junction.

| File trong `04_Scripts_Code` | Bạn viết gì |
|---|---|
| `film.json` | Tên phim, `style`, tag các phần, chỗ nghỉ riêng (`hold_before/after`); khóa nào ghi ở đây sẽ đè lên style |
| `Narration.md` | Lời dẫn: mỗi dòng là một câu thoại |
| `script_template.md` | Kịch bản hình: khối V.O. và mã hình cho từng khối |
| `overlay_spec.py` | Đồ họa gắn vào chữ trong lời dẫn |
| `audio_spec.py` | Nhạc và tiếng động |
| `media_spec.py` | Từ khóa tìm b-roll, chủ đề ảnh Commons |
| `pools_example.py` → `pools.py` | (Tùy chọn) hình dự phòng cho từng phần |
| `geo_build.py` | (Tùy chọn) dựng dữ liệu bản đồ từ Natural Earth |
| `FACT_CHECK.md` | Nguồn của mọi con số và mọi câu khẳng định |

## 1. Kịch bản và kiểm chứng (trước khi làm giọng)

1. Chia phim thành **cold open, 4–6 phần, closing**. Mỗi phần đặt ra một câu hỏi và trả lời nó. Phim cần một "động cơ" xuyên suốt; ví dụ Oymyakon có bộ đếm nhiệt độ hạ dần từ −38 xuống −60.
2. Viết `Narration.md`. Mỗi heading `## ` là một phần, theo đúng thứ tự `sections` trong `film.json`. Mỗi dòng có chữ là một câu thoại (`c0_01`, `a1_03`…), dài 1–3 câu.
3. Viết số bằng chữ đúng như người đọc sẽ nói ("minus sixty", "nineteen thirty-seven").
4. Ghi nguồn cho mọi con số vào `FACT_CHECK.md`. Ưu tiên nguồn gốc (WMO, NASA, thống kê nhà nước, báo lớn) và ghi ngày đọc.
5. Viết `script_template.md`. Mỗi `{{c0_01 c0_02}}` là một khối V.O. Dòng `**VISUAL:**` phía trên khối liệt kê hình theo đúng thứ tự lời nói. Dòng `**GFX:**`, `**SFX:**`, `**MUSIC:**` là ghi chú.

## 2. Giọng đọc

```
python doc.py 12 voice            # tạo mọi câu còn thiếu + mốc thời gian từng chữ (faster-whisper)
python doc.py 12 voice a2_04      # làm lại một câu (bản cũ được giữ dưới đuôi .old)
python doc.py 12 timeline         # xếp các câu lên trục thời gian của phim
python doc.py 12 script           # xuất kịch bản đọc được, có lời thoại và GFX đã đánh số
```

- Giọng mặc định là người đọc của Amazon, Pagpag và Oymyakon (AI33/ElevenLabs), tốc độ 0.95.
- Nghe lại cả bài. Câu nào đọc sai tên riêng thì sửa chữ trong `Narration.md` cho dễ đọc rồi chạy `voice <id>` để làm lại câu đó.
- Khoảng nghỉ: 0,75 s giữa các câu, 1,8 s giữa các khối, 5,5 s cho thẻ phần.
- Chỗ cần im lặng có chủ ý thì thêm vào `hold_after`. Ví dụ Oymyakon: tựa đề phim cần 7,9 s (5,5 s thẻ tựa, khoảng đen, rồi Part One hiện lên), còn khoảnh khắc −60 có 3,5 s im lặng.

## 3. Tìm tư liệu

**Nguyên tắc chính: tìm hình theo nội dung câu nói, không chỉ theo tên địa danh.** Câu nhắc cái xe cút kít thì tìm "wheelbarrow". Câu nói nước sôi hắt lên hóa băng thì tìm "boiling water thrown in freezing air".

```
python doc.py 12 search intro                 # tìm trên Pexels + Pixabay -> 02_B-Roll/candidates/intro/sheet_N.jpg
python doc.py 12 pick px:123="truck at night" pb:45="campfire"   # chỉ chọn clip đã xem bằng mắt
python doc.py 12 pick px:678="Yakutsk street" --where "Yakutsk"   # clip thật sự quay ở nơi đó
python doc.py 12 fetch                         # tải clip đã chọn
python doc.py 12 commons                       # ảnh Commons theo media_spec.TOPICS + bảng ảnh có đánh số
python doc.py 12 freesound list "ice cracking" 2 30   /   freesound get ice_cracking 12345
```

- **Người xem bảng ảnh là agent Sonnet**, không phải phiên chính: làm bảng nhỏ bằng `python tools/mini_sheets.py "<dự án>" <set> 4`, rồi giao 2–3 bộ (hoặc một nhóm chủ đề Commons) cho mỗi agent theo mẫu trong [PICKER_SONNET.md](PICKER_SONNET.md). Agent chạy `pick`, ghi ghi chú vào `candidates/<set>/picker_notes.md` và `commons/sheets/usable.md`, chỉ trả về tóm tắt ngắn.
- Khi xem bảng ảnh (agent làm theo đúng danh sách này), loại ngay những cảnh sau:
  - cờ hoặc biển báo của nước khác;
  - chữ viết sai ngôn ngữ ("BACK TO SCHOOL" trong phim về Siberia);
  - logo hoặc watermark;
  - hình mờ, hình lệch đề tài (phòng khách sạn dùng làm lớp học);
  - mặt trẻ em được quay cận.
- **Luật địa điểm:**
  - Clip `generic` không bao giờ được chú thích hay gọi là một địa danh.
  - Làng tuyết trông giống nơi đó cũng không được đặt dưới câu gọi tên nơi đó.
  - Ảnh Commons chỉ được giữ khi tiêu đề hoặc mô tả có nhắc tên nơi đó (regex trong `TOPICS`).
- Số trên bảng ảnh (`topic#n`) không bao giờ đổi, vì ảnh mới luôn được thêm vào cuối. Mã trong kịch bản vì vậy không bị lệch.
- Chỉ dùng stock trả phí khi được đồng ý.

## 4. Gán hình vào kịch bản

Trong dòng `**VISUAL:**`, ghi mã hình theo thứ tự lời nói: `photo:shalamov#3`, `px:40463888`, `pb:192778`, `nasa:batagaika`, `file:media/x.mp4`.

- **Mỗi câu thoại là một khối** `{{a1_03}}` (câu ≤ 2 s gộp với câu kế), để hình nằm đúng dưới câu nói về nó. Khối nhiều câu chia đều thời gian nên hình bị lệch lời (phim 12). Giữ nhịp nghỉ: `timing.gap_block = gap_line`, phần chênh cộng vào `hold_after` câu cuối mỗi ý, trừ khỏi `act_card`.
- Cần khoảng **1 hình cho mỗi 3,6 giây** của khối. Khối 15 giây cần 4 hình khác nhau. Khối thiếu hình thì engine giữ hình của chính câu đó lâu hơn (tối đa `edit.max_own` = 7 s) trước khi bốc clip trong pool.
- **Neo hình vào chữ** khi câu nhắc tới một hình cụ thể ở giữa câu: `px:29130948@"double rainbow"`. Hình đó lên 0,15 s trước khi chữ được đọc; các hình không neo chia đều quãng giữa hai điểm neo. Cụm từ phải đúng như bản ghi Whisper (`01_Voice/lines/<id>.words.json`; Whisper viết số bằng chữ số, chính tả Mỹ). Hình đầu tiên của câu không cần neo. Hai điểm neo cách nhau ít nhất 2,1 s; neo quá sát thì engine dời muộn lại, hết chỗ thì bỏ hình neo cuối. Bài học phim 12: cầu vồng đôi lên ngay đầu câu 12 s, đến chữ "double rainbow" đã chuyển cảnh.
- **Chế độ mốc cố định (nên dùng cho phim mới):** đặt `"edit": {"mode": "timed", ...}` trong `film.json`. Mỗi hình có một mốc lên hình:
  - hình đầu mỗi khối: lúc câu bắt đầu;
  - `@"cụm từ"`: 0,15 s trước khi chữ đó được đọc;
  - `@+2.4`: 2,4 s sau khi câu đầu của khối bắt đầu;
  - hình không ghi mốc: chia đều quãng giữa hai mốc kề nhau.
  
  Mỗi hình kéo dài đến mốc kế tiếp. Engine không dời, không bỏ, không lấy clip từ pool. Cảnh dưới `edit.timed_min` (2 s), mốc sai thứ tự hoặc cụm từ không có trong bản ghi thì `edit` **dừng và in từng câu bị lỗi**, không ghi `edit.json`. Cảnh dài hơn `max_own` và clip dùng quá `clip_cap` hoặc lặp trong `clip_gap` chỉ in cảnh báo. Hai chữ quá sát nhau (ví dụ "double rainbow" và "a new star" cách 1,6 s) thì chọn một hình, hoặc neo hình trước vào chữ sớm hơn.
- `edit` luôn ghi `05_Renders/shots.csv`: mỗi cảnh một dòng gồm giờ lên hình, độ dài, mã hình, mốc, câu và mấy chữ đang được đọc lúc cắt. Duyệt thời điểm hình bằng file này, không cần mở Resolve.
- Chế độ cũ (không có `mode`): sau `build`, kiểm tra không còn cảnh nào lấy hình ngoài danh sách của câu (thường do một clip đã dùng đủ `clip_cap` hoặc dùng lại trong vòng 60 s).
- Trong một khối, mỗi hình chỉ dùng **một lần**: không cắt cận lặp lại cùng một tấm ảnh. Bài học từ khối Shalamov: một ảnh dùng nhiều lần trông rất nghèo hình.
- Trong cả phim, mỗi clip dùng tối đa 2 lần, mỗi ảnh tối đa 3 lần. Một clip không được quay lại trong vòng 60 giây.
- Khối dài hơn số hình được ghi sẽ lấy thêm từ `pools.py`. Ảnh đã gắn địa điểm thì chỉ được ở pool của chính nơi đó.

## 5. Đồ họa

```
python doc.py 12 overlays         # gắn đồ họa vào chữ -> overlays.json (báo lỗi nếu có chữ không tìm thấy hoặc đồ họa chồng nhau); -v in cả bảng
python doc.py 12 gfx stills       # chỉ đồ họa mới hoặc đã sửa -> PNG + bảng duyệt stills/_review_N.jpg (16 khung mỗi ảnh)
python doc.py 12 gfx stills --all # làm lại mọi khung
python doc.py 12 gfx              # render toàn bộ (ProRes 4444 có kênh alpha)
python doc.py 12 gfx G07 G15      # chỉ render lại vài cái
```

- **Mật độ theo `rules.gfx_per_min` của style** (`lint` báo nếu lệch). Với `netflix-cold`: **2,5–3 đồ họa mỗi phút**, tức 50–60 đồ họa cho phim 20 phút (người dùng chốt 18/11/2026; phim 13 đạt 2,8). Aral V2 dày hơn (khoảng 45 đồ họa trong 12 phút), đó là mức trần chứ không phải mục tiêu. Phim chỉ có lời dẫn trên footage thì quá trống.
- Có sẵn các loại: title, chapter, lower, stamp, stat, list, words, quote, define, timeline, map, bars, split_labels, end_text… (trong `Film.jsx` và `Overlays.jsx`). **Màu, font, chuyển động chữ, hạt phim lấy từ style** (`gfx` trong `styles/<tên>.json`, ghi đè được bằng `"gfx"` trong `film.json`); `gfx` tự ghi `src/style.json` trước khi render. Không sửa hằng số màu trong JSX nữa.
- **Đồ họa toàn màn hình (bản đồ…) phải luôn chuyển động**: camera đẩy chậm hoặc vật thể trượt vào. Đứng yên tối đa 6 s sau nhịp cuối, vì Oymyakon từng có 15 s bản đồ đứng im. Bên dưới chúng có một tấm nền màu, nên b-roll không chớp lộ ra giữa hai bản đồ.
- Giữa thẻ tựa và thẻ phần đầu tiên phải có ≥ 1,5 s màn đen.
- **Chỉ duyệt phần đã đổi:** `gfx stills` nhớ dấu của từng đồ họa (`stills/_hash.json`, gồm nội dung đồ họa và mã nguồn Remotion). Lần sau chỉ render và đưa vào `_review_N.jpg` những cái mới hoặc đã sửa; sửa `Film.jsx`/`Overlays.jsx` thì mọi khung được làm lại. Chỉ xem `_review_N.jpg`, không mở từng PNG. Thử trên phim 13: lần đầu 76 khung mất 3 phút; sửa một đồ họa thì 18 giây và một hàng ảnh để xem.

## 6. Dựng hình và bản nháp

```
python doc.py 12 edit             # hình lên trục thời gian -> edit.json
python doc.py 12 voicetrack       # chỉ có giọng, để làm bản nháp
python doc.py 12 render 60 120    # render thử một đoạn -> 05_Renders/tests/section_60_120.mp4
python doc.py 12 lint             # kiểm tra cả kế hoạch trong thư mục tạm, chỉ in lỗi; khoảng 3 s
python doc.py 12 build            # timeline + overlays + edit, chạy khi lint đã sạch
```

- **Lint trước, build sau.** `lint` chạy timeline, overlays, edit vào thư mục tạm (không đụng `05_Renders`), vẫn đi tiếp khi một bước hỏng nếu bước sau còn đầu vào, rồi kiểm tra mọi clip `px:`/`pb:` trong template đã tải và mọi file nhạc trong `audio_spec` có trong `07_Audio/music` hoặc kho nhạc. Mọi lỗi hiện trong một lần chạy, mỗi bước một dòng tóm tắt; thoát mã 1 khi còn lỗi. Thử trên phim 13 với 3 lỗi cài sẵn (cụm neo sai, clip chưa tải, file nhạc thiếu): bắt cả 3 trong một lần.

- Độ dài cảnh theo `edit.target/min/max` của style (`netflix-cold`: mục tiêu 3,6 s, trong khoảng 2,5–5 s). Điểm cắt được dời vào chỗ ngắt lời chỉ khi mọi cảnh vẫn nằm trong khoảng đó, nên cảnh không lúc quá nhanh lúc quá lâu.
- Ảnh tĩnh luôn có chuyển động máy: đẩy vào, kéo ra, lia, hoặc cận vào vùng nhiều chi tiết nhất.

## 7. Âm thanh

**Nguồn nhạc (từ 17/11/2026):** nhạc tự tạo bằng **Suno qua API AI33** thay cho vidIQ, kết hợp với **kho nhạc có sẵn** (244 bài Kevin MacLeod, chia 8 nhóm cảm xúc). vidIQ không dùng nữa.

| Dùng gì | Khi nào |
|---|---|
| Suno (AI33) | Bước ngoặt và cảm xúc riêng của phim: cold open, mỗi phần chính, cao trào, kết. Khoảng 4–6 cue mỗi phim |
| Kho nhạc có sẵn | Đoạn nối, nhạc nền dẫn chuyện, chỗ Suno không ra đúng ý, và khi Suno bị bộ lọc chặn |

```
python doc.py 12 music credits                                   # số dư AI33 (dùng chung với giọng đọc)
python doc.py 12 music lib somber cello --max 300                # tìm trong kho theo cảm xúc, nhạc cụ; --cat 1-8 lọc nhóm
python doc.py 12 music make a5_famine "Somber orchestral underscore about famine: solo cello, low strings, distant piano, 60 bpm, slowly building"
python doc.py 12 music get a5_famine <task_id>                   # lấy bài khi make hết 10 phút chờ
```

- `music make` tạo nhạc **không lời** (engine tự thêm câu "no vocals…" vào cuối prompt, tổng tối đa 500 ký tự). Mỗi lần ra **2 bản**: `07_Audio/music/suno_<cue>_1.mp3` và `_2.mp3`, dài khoảng 3 phút, kèm `suno_manifest.json` ghi prompt, task và credit. Giá khoảng 3.600 credit AI33 mỗi lần.
- Prompt viết bằng tiếng Anh, tả cảm xúc, nhạc cụ, tốc độ (bpm) và diễn tiến; không ghi tên nghệ sĩ hay tên phim. Nghe cả hai bản, chọn một, ghi bản đã chọn vào `HANDOVER.md`.
- Trong `audio_spec.MUSIC`, ghi tên file Suno (`suno_a5_famine_1.mp3`) hoặc tên file trong kho (`06_EmotionalPiano_64bpm_04m09s_Immersed.mp3`) như nhau. Bài Suno đo khoảng −14 đến −15 LUFS, bài kho −14 đến −18 LUFS (`music make` in ra số đo): đặt gain sao cho mọi cue ở khoảng −19 LUFS trước khi hạ dưới giọng.
- Suno báo lỗi do bộ lọc nội dung thì không gửi lại nguyên prompt; viết lại cho trung tính hơn hoặc lấy bài trong kho.
- `credits` tự tách nhạc AI ("Original score: AI-generated cues (Suno)") khỏi danh sách bài Kevin MacLeod.
- Bản quyền thương mại của nhạc Suno mua qua AI33 chưa được AI33 xác nhận bằng văn bản; hỏi họ trước khi bật kiếm tiền trên kênh.

```
python doc.py 12 audio            # chép file vào 07_Audio, ghi audio_plan.json, báo % lời dẫn có nhạc nền
python doc.py 12 audio preview    # bản trộn nghe thử (m4a)
python doc.py 12 audio final      # final_mix.wav ở −14 LUFS
```

- **Độ phủ và mức nhạc theo `rules.music_coverage` / `music_under_voice_db` của style**; `audio` và `lint` in độ phủ so với mục tiêu. Tính chất nhạc (nhạc cụ, bpm) cho prompt Suno lấy từ `notes.music` của style. Với `netflix-cold`: **nhạc gần như liên tục, khoảng 15 dB dưới giọng**, ≥ 85% thời lượng lời dẫn có nhạc. Bản Oymyakon đầu chỉ có 65% ở −21 dB và bị chê là "thiếu".
- Nhạc đổi theo bước ngoặt của câu chuyện. Im lặng chỉ dùng như một nhịp có chủ ý.
- Tiếng nền (động cơ, gió) phải nhỏ: động cơ diesel đặt khoảng −42 dB. Bản đầu của Oymyakon bị chê "động cơ quá to".
- Kho nhạc: `02. Giọng đọc & Âm thanh - Voice & Audio\03. Nhạc nền Phim tài liệu - BGM Tracks` (danh mục `DANH_MUC_KHO_NHAC_BGM.md`, bản sao trên `Y:\Data Footage\Discovery\Kien\BGM_NoCopyright` là nơi `audio` chép file). Tiếng động: 1001 Sound Effects trên `Y:` và Freesound CC0.

## 8. Dựng lên Adobe Premiere Pro (phim mới, mặc định từ 11/2026)

Phim tạo bằng `doc.py new` có `"editor": "premiere"` trong `film.json`, nên `review` chạy `premiere`. Phim cũ (đến phim 15) vẫn ở Resolve (mục 8R) và không xuất lại.

```
python doc.py 16 premiere                      # Claude: 05_Renders/premiere/timeline.xml + mọi thứ nó cần (vài phút)
python doc.py 16 qc "<file Premiere xuất ra>"  # Claude: QC trên bản cuối
```

**File `timeline.xml` (XML FCP7, Premiere đọc trực tiếp) tự đủ:**

| Track | Nội dung |
|---|---|
| V1 | Mỗi cảnh một clip hoặc ảnh gốc, tên `S131 px:6831205`. Clip stock đúng điểm vào, phóng phủ khung; clip chậm dùng Time Remap; ảnh tĩnh có Ken Burns bằng keyframe Scale/Center |
| V2 | **Để trống** cho adjustment layer gắn LUT grade |
| V3 | Vignette (kèm viền letterbox nếu style có `letterbox`) · V4 đồ họa Remotion (nền trong suốt) · V5 lớp phủ HUD nếu phim có |
| A1 | Từng câu thoại · A2 trở đi: nhạc rồi tiếng động, đã bake độ to, fade, ducking; tổng −14 LUFS |
| Marker | Mỗi khối lời dẫn một marker, kèm nguyên văn câu thoại |

**Người dùng làm:**
1. **File › Import…**, chọn `05_Renders/premiere/timeline.xml`. Mở sequence trong bin mới (double-click).
2. **Gắn màu, một lần:** **File › New › Adjustment Layer**, kéo lên **V2** phủ cả phim, rồi **Lumetri Color › Creative › Look** chọn `docpipe_<TÊN_PHIM>_grade`. LUT đã chép sẵn vào `%APPDATA%\Adobe\Common\LUTs\Creative`. Nếu không thấy, chọn Browse tới `05_Renders/premiere/grade.cube`.
3. Xem, chỉnh, rồi xuất. Nếu engine báo true peak vượt −1 dBTP: trong Export bật **Effects › Loudness Normalization** (−14 LUFS, true peak −1).
4. Gửi Claude đường dẫn file đã xuất để chạy `qc` và `credits`.

**Ghi chú**
- Vòng góp ý trên Premiere (đọc marker ra `REVIEW_NOTES.md`) chưa làm. Hiện tại người dùng tự sửa trên timeline.
- Đã kiểm chứng trên phim 12 (11/2026): ảnh, slow-motion, đồ họa, âm thanh đều đúng. Track âm thanh stereo phải có `currentExplodedTrackIndex`/`totalExplodedTrackCount`, thiếu là Premiere bỏ hết âm thanh.

## 8R. Dựng lên DaVinci Resolve (phim cũ), xem, góp ý, xuất bản cuối

**Phân vai:** người dùng viết và sửa `Narration.md`, mở timeline Claude dựng sẵn trong Resolve, góp ý, rồi tự xuất bản cuối theo cấu hình mình muốn. Claude lo mọi thứ còn lại: kế hoạch hình, b-roll và ảnh, giọng đọc, nhạc và tiếng động, đồ họa motion, và dựng file timeline.

```
python doc.py 12 review                        # Claude: 05_Renders/review/timeline.fcpxml + mọi thứ nó cần (vài phút)
python doc.py 12 notes góp_ý.edl               # Claude: marker góp ý -> 05_Renders/review/REVIEW_NOTES.md
python doc.py 12 qc "<file Resolve xuất ra>"   # Claude: QC trên bản cuối
```

**File `timeline.fcpxml` tự đủ.** Chỉ cần mở bằng tay là có:

| Track | Nội dung |
|---|---|
| V1 | Mỗi cảnh một clip hoặc ảnh gốc, tên `S131 px:6831205`; ảnh tĩnh có chuyển động máy bằng keyframe |
| V2 | Lớp vignette của phim |
| V3 | Đồ họa Remotion, nền trong suốt |
| V4 | Lớp phủ riêng của phim nếu có (bộ đếm nhiệt độ của Oymyakon) |
| Các track âm thanh | Từng câu thoại, từng đoạn nhạc, từng tiếng động, đã cắt sẵn độ to, fade, và nhạc tự hạ dưới giọng đọc. Tổng đã ở −14 LUFS |
| Marker xanh | Mỗi khối lời dẫn một marker, kèm nguyên văn câu thoại |

Khung hình khớp bản engine render tới dưới 1 pixel. Engine tự tránh những thứ làm Resolve báo "clips were not found" hoặc Media Offline: tên file có dấu hoặc quá dài (hardlink ASCII trong `review/links`), clip có timecode drop-frame (bản remux `*_notc.mp4`), ảnh tên toàn số (plate đặt tên `plate_<n>_solid.png`).

Resolve thường để **V1 trống** (khung của file), nên các lớp lùi lên một bậc: hình ở V2, vignette V3, đồ họa V4, lớp phủ V5. Gắn LUT cho track hình, và có thể xóa V1 trống.

**Người dùng làm:**
1. Trong Resolve, mở hoặc tạo project cho phim. Vào **File › Import › Timeline…** (Ctrl+Shift+I), chọn `05_Renders/review/timeline.fcpxml`.
2. Ở hộp thoại **Load XML**: tick **Automatically import source clips into media pool** và **Use sizing information**, rồi bấm OK. Đợi Resolve nạp media xong.
3. **Gắn màu:** ở trang **Color**, chọn mọi clip trên track hình (V1, hoặc V2 nếu V1 trống) (bấm vào dải clip, Ctrl+A), chuột phải › **LUTs** › **docpipe** › `<TÊN_PHIM>_grade`. Chỉ áp cho track hình, không áp cho đồ họa.
4. Xem phim. Chỗ cần sửa: bấm **M** để đặt marker, nhấp đúp vào marker và ghi góp ý vào ô Notes.
5. Xem xong: **File › Export › Timeline Markers to EDL…**, gửi file `.edl` cho Claude. Claude chạy `notes`, sửa kế hoạch, rồi xuất một `timeline.fcpxml` mới cho vòng xem tiếp theo.
6. Khi đã ưng: ở trang **Fairlight**, thêm **Limiter** vào Main bus, ceiling −1 dB. Hoặc ở trang **Deliver**, tick **Normalize Audio Levels**, chọn YouTube −14 LUFS, true peak −1.
7. Ở trang **Deliver**, chọn định dạng tùy ý (gợi ý: MP4, H.264 hoặc H.265, 1920×1080, 30 fps, AAC 320 kb/s). Add to Render Queue › Render All. Gửi Claude đường dẫn file để chạy `qc` và `credits`.

**Ghi chú**
- Sửa tay trên timeline vẫn được, nhưng mỗi vòng góp ý là một timeline mới, không mang theo phần sửa tay. Thay đổi lớn nên đi qua marker để Claude sửa kế hoạch; chỉ chỉnh tay ở vòng cuối.
- **Tự động hóa (tùy chọn):** khi bridge `resolve_bridge` đang chạy trong Resolve (Workspace › Scripts), Claude có thể tự làm bước 1–3 bằng `push` và đọc marker bằng `pull`. Bridge cho bản Free cài ở `C:\Users\Admin\davinci-resolve-mcp`. Bản Resolve 21 beta đôi khi hủy import chạy bằng script, nên mở tay là cách chính. Đừng cập nhật Resolve lên 21.1 trở đi nếu muốn giữ bridge.
- Engine vẫn render được như cũ (`render`, `patch`), dùng khi cần bản đối chiếu hoặc không có Resolve.

## 8b. Render bằng engine (dự phòng)

```
python doc.py 12 render           # cả phim (khoảng 30 phút cho 20 phút phim)
python doc.py 12 patch 713 742    # chỉ render lại vài đoạn rồi chèn vào phim (khoảng 10 phút)
python doc.py 12 credits          # CREDITS.md cho phần mô tả video
python doc.py 12 qc               # QC_REPORT.md
```

- `patch` giữ bản cũ ở `<tên>_prepatch.mp4`. Xem lại bản mới rồi tự xóa bản cũ. Không cắt ghép bằng stream copy, vì cách đó làm lệch số khung hình.

## 9. Duyệt bằng mắt

QC tự động chỉ bắt được lỗi cơ học. Hãy xem phim theo `QC_CHECKLIST.md`, ghi lỗi kèm mốc thời gian, rồi ghi thành marker góp ý trong Resolve.

---

### Sơ đồ nhanh

```
Narration.md ─voice─> 01_Voice ─timeline─> timeline.json ─┬─overlays─> overlays.json ─gfx─> render/ov/*.mov ─┐
script_template.md (VISUAL mã hình) ──────────────────────┴─edit──> edit.json ───────────────────────────────┼─render─> phim.mp4 ─qc─> QC_REPORT.md
media_spec.py ─search/pick/fetch/commons─> 02_B-Roll, 03_Images                                              │
audio_spec.py ─audio final─> final_mix.wav ──────────────────────────────────────────────────────────────────┘
```

### Ghi chú kỹ thuật

- Key API (AI33, Pexels, Pixabay, Freesound) được đọc lúc chạy từ biến môi trường, nếu không có thì từ `%USERPROFILE%\.docpipe\keys.env` (mỗi key một dòng `TÊN=giá trị`; xem `SETUP_CLAUDE.md` mục 4). Key không bao giờ được in ra hay lưu lại.
- `DOC_OUT=<thư mục>` chuyển mọi file ra (timeline, overlays, edit, render) sang thư mục khác để chạy thử mà không đụng vào dự án thật.
- `film.json` → `"hud": "module:Class"` vẽ một lớp phủ riêng của phim lên mọi khung hình, ví dụ bộ đếm nhiệt độ của Oymyakon (`counter:Counter`).
- Engine đã được chạy lại trên Oymyakon: timeline, overlays, counter và edit giống hệt bản cũ, các đoạn render khớp phim hoàn chỉnh.
