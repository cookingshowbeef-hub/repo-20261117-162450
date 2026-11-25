# Cài đặt cho Claude trên máy mới

> **Gửi Claude:** người dùng đưa link repo GitHub này để bạn tự cài và hiểu quy trình làm phim tài liệu. Làm lần lượt từng bước bên dưới. Bước nào cần người dùng (key API, đăng nhập, cài app có giao diện, chọn thư mục) thì hỏi họ.
>
> Xong thì chạy `python setup_check.py` và bước 9, rồi báo lại kết quả. Không in giá trị key ra màn hình, không commit key hay `settings.env`.

**Thư mục engine (gọi là ENGINE):** thư mục clone từ repo này, chứa `doc.py` và file này.

## Cần cài gì

| Thứ cần có | Bắt buộc? | Dùng cho |
|---|---|---|
| Repo này (bước 1) | Có | Engine, mẫu dự án, đồ họa Remotion, skill, memory |
| Python 3.11 + `requirements.txt` | Có | Toàn bộ engine; faster-whisper lấy mốc thời gian từng chữ |
| ffmpeg + ffprobe trên PATH | Có | Âm thanh, video, kiểm tra media |
| Node.js 20+ và `npm install` (Remotion) | Có | Render đồ họa motion |
| `~/.docpipe/keys.env`: key AI33, Pexels, Pixabay, Freesound | Có | Giọng đọc, nhạc Suno, b-roll, tiếng động |
| `~/.docpipe/settings.env`: thư mục dự án và kho nhạc | Có | Nơi để phim, nơi lấy nhạc và tiếng động |
| Adobe Premiere Pro (bản trả phí) | Có | Phim mới: người dùng mở timeline dựng sẵn, chỉnh, xuất bản cuối |
| DaVinci Resolve 21.0.x (bản Free được) | Chỉ phim cũ | Phim đến số 15 dựng trên Resolve |
| Skill `doc-pipeline` + memory (bước 6) | Có | Để Claude hiểu quy trình, các luật và lựa chọn của người dùng |
| Kho nhạc BGM (244 bài Kevin MacLeod) và kho tiếng động | Nên có | Nhạc nối, tiếng động; không có thì dùng Suno + Freesound |
| GPU NVIDIA | Không | Mốc thời gian giọng nhanh hơn; không có thì chạy CPU |
| `davinci-resolve-mcp` (GitHub) | Không | `push`/`pull` tự động vào Resolve |

Repo **không** chứa key, phim, b-roll, giọng đọc hay kho nhạc (quá nặng và có bản quyền riêng). Những thứ đó người dùng chép từ máy cũ nếu cần.

## 1. Clone repo

Hỏi người dùng muốn đặt ở đâu. Cách quen thuộc là giữ đúng cây thư mục cũ (khi đó không phải khai báo thư mục dự án):

```
git clone <link repo> "D:\4. bot\documentary\06. Kịch bản & Công cụ Code - Scripts & Engine\03. Doc Pipeline - Quy trình Phim tài liệu"
```

Đặt chỗ khác cũng được; bước 5 khai báo thư mục dự án và kho nhạc.

## 2. Python, ffmpeg

```
winget install Python.Python.3.11
winget install Gyan.FFmpeg
cd "<ENGINE>"
python -m pip install -r requirements.txt
```

`Gyan.FFmpeg` là bản full build. Hai gói `nvidia-*` trong `requirements.txt` chỉ cần khi có GPU NVIDIA. Không có GPU thì bỏ qua lỗi của chúng.

## 3. Node.js và Remotion

```
winget install OpenJS.NodeJS.LTS
cd "<ENGINE>\templates\remotion"
npm install
```

- `python doc.py new ...` nối `node_modules` này vào mỗi dự án mới bằng junction.
- Nếu `node_modules` nằm chỗ khác: đặt `DOC_NODE_MODULES`. Nếu `node.exe` không có trên PATH: đặt `REMOTION_NODE` trong `settings.env`.

## 4. Key API

Mọi key nằm trong **một file**: `%USERPROFILE%\.docpipe\keys.env`, ngoài thư mục repo. Hỏi người dùng từng key rồi tạo file này. Không in key ra, không chép vào file nào khác, không commit.

```
# API keys for the documentary pipeline. One NAME=value per line.
AI33_API_KEY=<key>          # giọng đọc, nhạc Suno, tiếng động AI (ai33.pro)
PEXELS_API_KEY=<key>        # b-roll
PIXABAY_API_KEY=<key>       # b-roll
FREESOUND_API_KEY=<key>     # tiếng động CC0
```

- Engine (`docpipe/ctx.py: key()`) đọc theo thứ tự: biến môi trường cùng tên trước, rồi `keys.env`. Muốn để file ở nơi khác thì đặt biến `DOCPIPE_KEYS=<đường dẫn>`.
- Nên giới hạn quyền đọc file cho riêng tài khoản người dùng (hỏi người dùng trước khi chạy): `icacls "%USERPROFILE%\.docpipe\keys.env" /inheritance:r /grant:r "%USERNAME%:F"`.

## 5. Đường dẫn của máy: `settings.env`

Tạo `%USERPROFILE%\.docpipe\settings.env`. Hỏi người dùng từng đường dẫn; dòng nào không có thì bỏ.

```
# Paths for the documentary pipeline on this machine. One NAME=value per line.
DOCPIPE_PROJECTS=D:\4. bot\documentary\04. Dự án đang Edit - Active Projects     # nơi để các phim (doc.py new tạo phim ở đây)
DOCPIPE_BGM=D:\4. bot\documentary\02. Giọng đọc & Âm thanh - Voice & Audio\03. Nhạc nền Phim tài liệu - BGM Tracks   # có bgm_vault_catalog.json (music lib)
DOCPIPE_LIBRARY=Y:\Data Footage\Discovery\Kien                                   # có BGM_NoCopyright và SFX_Vault (audio chép nhạc/tiếng động từ đây)
RESOLVE_MCP_DIR=C:\Users\<tên>\davinci-resolve-mcp                               # tùy chọn (bước 7)
```

- Thiếu `DOCPIPE_PROJECTS`: engine dùng `..\..\04. Dự án đang Edit - Active Projects` nếu có (cây thư mục cũ), không thì `<ENGINE>\projects` (đã nằm trong `.gitignore`).
- Biến môi trường cùng tên thắng `settings.env`. Muốn để file ở chỗ khác thì đặt `DOCPIPE_SETTINGS`.

## 6. Skill và memory cho Claude

```
xcopy /E /I "<ENGINE>\claude\skills\doc-pipeline" "%USERPROFILE%\.claude\skills\doc-pipeline"
```

- Skill tự kích hoạt khi người dùng nói về làm phim, `doc.py`, timeline Premiere/Resolve hay góp ý EDL. Bản gốc là bản trong repo; sửa xong thì chép lại.
- `claude/memory/` là các lựa chọn người dùng đã chốt (1080p, mật độ đồ họa, nhạc Suno, chọn hình bằng Sonnet, không dùng OpenAI tạo ảnh, mỗi chặng một session…). Chép các file `.md` trong đó vào thư mục memory của dự án Claude Code trên máy mới: `%USERPROFILE%\.claude\projects\<slug>\memory\`, với `<slug>` là thư mục làm việc của người dùng viết lại kiểu Claude Code (ví dụ `D:\4. bot\documentary` → `D--4--bot-documentary`). Nếu thư mục memory đã có `MEMORY.md` thì gộp các dòng, không ghi đè.
- Nên mở session với thư mục làm việc là thư mục cha của dự án (ví dụ `documentary`).

## 7. Adobe Premiere Pro (phim mới) và DaVinci Resolve (phim cũ)

**Premiere:** không cần cấu hình. `doc.py <prj> premiere` (hoặc `review` với phim có `"editor": "premiere"`) ghi `05_Renders/premiere/timeline.xml` và tự chép LUT vào `%APPDATA%\Adobe\Common\LUTs\Creative`. Người dùng import bằng File › Import. Cách làm chi tiết ở `docs/QUY_TRINH.md` mục 8.

**Resolve (chỉ khi mở lại phim cũ):**


1. Người dùng cài **DaVinci Resolve 21.0.x** (bản Free đủ dùng).
   **Không cập nhật lên 21.1 trở đi**: bản Free sẽ mất Python scripting và bridge.
2. Không cần cấu hình gì thêm cho cách mở tay. Lệnh `review` tự chép LUT màu vào `C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\LUT\docpipe\`.
3. **Tùy chọn: tự động đẩy timeline vào Resolve (`push`/`pull`).**

   ```
   git clone https://github.com/samuelgursky/davinci-resolve-mcp "%USERPROFILE%\davinci-resolve-mcp"
   cd "%USERPROFILE%\davinci-resolve-mcp"
   python scripts/install_resolve_bridge.py
   ```

   - Sau đó khởi động lại Resolve, mở project, rồi bấm **Workspace › Scripts › resolve_bridge**. Mỗi lần mở Resolve phải chạy lại bridge.
   - Clone vào chỗ khác thì đặt `RESOLVE_MCP_DIR` trong `settings.env`.
   - Bridge đang treo thường là do một hộp thoại trong Resolve đang mở.

## 8. Connector

- **vidIQ (tùy chọn):** người dùng bật connector vidIQ trong claude.ai (Settings › Connectors). Chỉ dùng để tìm thêm b-roll; nhạc tạo bằng `doc.py <prj> music make` (Suno qua AI33).

## 9. Kiểm tra

```
cd "<ENGINE>"
python setup_check.py
```

Mục bắt buộc phải là OK. Mục ghi "optional" thiếu cũng được.

Kiểm tra gọi API thật (không tốn credit đáng kể): `python doc.py <một dự án> music credits` phải in số dư AI33.

Nếu đã chép phim mẫu Oymyakon (dự án `11`), chạy thử khô. Lệnh này ghi ra thư mục tạm, không đụng dự án:

```
set DOC_OUT=%TEMP%\doc_smoke
python doc.py 11 build
```

Phải ra khoảng 295 cảnh và 65 đồ họa trong vài giây.

## 10. Sau khi cài: đọc quy trình

1. `docs/QUY_TRINH.md`: từng bước, từ tạo dự án tới Premiere. Đọc hết trước phim đầu tiên.
2. `docs/PICKER_SONNET.md`: chọn b-roll và ảnh bằng agent Sonnet.
3. `docs/QC_CHECKLIST.md`: duyệt bằng mắt.
4. `doc.py` (chạy không kèm tham số): danh sách lệnh.

**Tóm tắt vòng làm việc** (mỗi chặng một session, bàn giao qua `05_Renders/HANDOVER.md`)
1. Người dùng viết `Narration.md`. Claude: `voice` → `timeline`.
2. Claude: `search` → bảng ảnh nhỏ → agent Sonnet chọn hình → `fetch`, `commons`.
3. Claude: kịch bản hình → `overlays`/`gfx stills` → `music` → `lint` → `build` → `audio final` → `premiere`.
4. Người dùng import `05_Renders/premiere/timeline.xml` vào Premiere, gắn LUT bằng adjustment layer ở V2, chỉnh trên timeline.
5. Người dùng tự xuất bản cuối trong Premiere. Claude chạy `qc` + `credits` trên file đó.
