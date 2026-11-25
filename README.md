# Doc Pipeline — quy trình phim tài liệu lời dẫn AI

> **Claude: nếu người dùng gửi link repo này để cài trên máy mới**, clone repo rồi làm theo [SETUP_CLAUDE.md](SETUP_CLAUDE.md) từ bước 1 đến bước 9. Hỏi người dùng các key API và đường dẫn thư mục; không in key ra, không commit key hay `settings.env`.

Engine dùng chung, rút từ các phim **Aral V2**, **Pagpag** và **Oymyakon**, rồi bổ sung qua các phim sau: lời dẫn AI (ElevenLabs qua AI33), b-roll từ stock miễn phí và Wikimedia Commons, đồ họa Remotion, nhạc Suno qua AI33 cùng kho nhạc có sẵn, timeline dựng sẵn cho Adobe Premiere Pro (phim mới) hoặc DaVinci Resolve (phim cũ) để người dùng xem, chỉnh và xuất. Xuất 1080p.

- **Bắt đầu một phim:** `python doc.py new "14. Tên phim (20 Phút) - slug" "FILM TITLE" [style]`
- **Phong cách edit (style):** `python doc.py styles` liệt kê các preset (`netflix-cold`, `warm-vintage`, `clean-explainer`, `noir-crime`), `python doc.py <prj> style set <tên>` đổi phong cách. Chi tiết và cách tạo style mới: [docs/STYLES.md](docs/STYLES.md)
- **Hướng dẫn từng bước:** [docs/QUY_TRINH.md](docs/QUY_TRINH.md)
- **Chọn b-roll và ảnh bằng agent Sonnet:** [docs/PICKER_SONNET.md](docs/PICKER_SONNET.md)
- **Duyệt phim:** [docs/QC_CHECKLIST.md](docs/QC_CHECKLIST.md)
- **Cài trên máy mới:** [SETUP_CLAUDE.md](SETUP_CLAUDE.md), kiểm tra bằng `python setup_check.py`

| Thư mục | Nội dung |
|---|---|
| `doc.py` | Lệnh chạy mọi bước (`python doc.py` không kèm gì để xem danh sách) |
| `styles/` | Preset phong cách edit: grade, letterbox, nhịp cắt, màu/font/chuyển động đồ họa, luật mật độ và nhạc, ghi chú từng chặng |
| `docpipe/` | Code engine: style, voice, music, media (b-roll, Commons, Freesound), timeline, overlays, edit, lint, audio, premiere, resolve, qc |
| `templates/code/` | File mẫu cho `04_Scripts_Code` của phim mới |
| `templates/remotion/` | Thư viện đồ họa (Film.jsx, Overlays.jsx đọc màu/font từ `src/style.json`), render_ov.mjs, font |
| `tools/` | Bảng ảnh nhỏ cho việc chọn hình, mẫu sinh kịch bản hình |
| `data/naturalearth/` | Dữ liệu bản đồ Natural Earth (public domain) |
| `claude/skills/doc-pipeline/` | Skill cho Claude Code |
| `claude/memory/` | Các lựa chọn người dùng đã chốt, chép vào memory của Claude trên máy mới |

**Không có trong repo** (để trên máy, ngoài repo): `~/.docpipe/keys.env` (API key), `~/.docpipe/settings.env` (đường dẫn của máy), các phim, b-roll, giọng đọc, kho nhạc và tiếng động.
