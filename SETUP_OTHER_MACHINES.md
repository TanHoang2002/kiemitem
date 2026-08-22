# Setup trên máy khác — chạy từ source (không build DLL/EXE)

Yêu cầu: Windows 10/11, Diablo IV đã cài, quyền admin để cài DLL TTS.

## 1. Cài đặt công cụ (chỉ làm 1 lần mỗi máy)

### 1.1. Python 3.14

Tải từ https://www.python.org/downloads/release/python-3140/ — chọn **Windows installer (64-bit)**.

Khi cài, tick vào **"Add Python to PATH"**.

Verify trong PowerShell mới:

```powershell
python --version
# Phải thấy: Python 3.14.x
```

### 1.2. uv (package manager)

PowerShell chạy với admin:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Đóng PowerShell, mở lại. Verify:

```powershell
uv --version
```

## 2. Lấy source code

### 2.1. Từ git (nếu máy khác có internet + git)

```powershell
cd D:\
git clone <repo-url-của-bạn> BotFillItem
cd BotFillItem
```

### 2.2. Từ ZIP (không có git)

Copy cả thư mục `D:\Code\BotFillItem` từ máy dev sang máy đích. Có thể xóa trước các thư mục lớn không cần:

```powershell
# Trước khi copy (trên máy dev) — giảm dung lượng
Remove-Item -Recurse -Force .venv            # sẽ tạo lại ở máy đích
Remove-Item -Recurse -Force .git             # nếu không cần history
Remove-Item -Recurse -Force __pycache__      # có trong nhiều subdir
Remove-Item -Recurse -Force tests            # không cần khi chạy production
Remove-Item -Recurse -Force .pytest_cache
Remove-Item -Recurse -Force bridge\__pycache__, receiver\__pycache__
```

Giữ bắt buộc: `src/`, `assets/`, `tts/`, `bridge/`, `receiver/`, `pyproject.toml`, `uv.lock`, `install_dll.cmd`, `README.md`.

## 3. Cài dependencies (mỗi máy)

```powershell
cd D:\BotFillItem   # hoặc nơi bạn copy tới
uv sync
```

Lệnh này tạo `.venv\` và cài đầy đủ dependencies theo `uv.lock` — đảm bảo đúng phiên bản như máy dev.

Verify:

```powershell
uv run python -c "from src.app.shell import UnifiedMainWindow; print('OK')"
```

## 4. Cài DLL TTS (mỗi máy — cần admin)

**Đây là bắt buộc.** Tool đọc item từ game cần DLL TTS được ký và copy vào thư mục Diablo IV.

```powershell
# Chạy với admin
cd D:\BotFillItem
.\install_dll.cmd
```

Khi prompt:

- Nhập đường dẫn thư mục "Diablo IV" (vd `C:\Program Files (x86)\Diablo IV`). Để lấy: Battle.net → gear icon next to Play → Open in Explorer → copy path.
- Cho phép cài certificate khi được hỏi.

Xem chi tiết: [README.md mục TTS](README.md#tts).

## 5. Cấu hình game

Trong Diablo IV → Options:

| Section             | Setting                      | Giá trị           |
| ------------------- | ---------------------------- | ----------------- |
| Gameplay > Gameplay | Advanced Tooltip Information | **ON**            |
| Accessibility       | Use Screen Reader            | **ON**            |
| Accessibility       | 3rd Party Screen Reader      | **ON**            |
| Graphics            | Font Scale                   | Small hoặc Medium |
| Graphics            | HDR                          | **OFF**           |
| Language            | English                      | bắt buộc          |

## 6. Chạy d4lf

```powershell
cd D:\BotFillItem
uv run python -m src.main
```

Hoặc dùng launcher đã có (nếu có):

```powershell
.\d4lf-consoleonly.bat
```

## 7. Cấu hình GiaoIT V1 (đã bật mặc định)

Mở d4lf → UI tiếng Việt mặc định. Các thiết lập sau đã có sẵn:

- **Ngôn ngữ UI**: `viVN` mặc định (Settings → ⚙️ Hệ thống → Ngôn ngữ nếu muốn đổi về `enUS`, restart sau khi đổi)
- **Capture Mode (GiaoIT V1)**: luôn BẬT, không có toggle trong UI. Muốn tắt khẩn cấp → set env `GIAOIT_DISABLED=1` trước khi chạy d4lf
- **Hotkeys**: F2 = capture 1 món, F4 = đọc cả rương (có thể đổi trong Settings → ⌨️ Phím tắt)

Tạo file account list cho bridge:

```powershell
@("trial-account-01", "trial-account-02") | Set-Content "$env:USERPROFILE\.giaoit\accounts.txt"
```

## 8. Chạy bridge + receiver (nếu dùng GiaoIT V1)

**Terminal 1 — receiver:**

```powershell
cd D:\BotFillItem\receiver
uv run uvicorn main:app --port 8000
```

**Terminal 2 — bridge:**

```powershell
cd D:\BotFillItem
$env:GIAOIT_LANGUAGE = "viVN"   # tùy chọn, muốn UI tiếng Việt
uv run python -m bridge.main --ui
```

Verify:

- `http://127.0.0.1:8000/health` → `{"ok": true, ...}`
- Trong game, rê chuột lên item + bấm **F2** → bridge hiện confirm dialog → bấm Send → receiver nhận.

## 9. Kiểm tra vận hành sau khi chạy thử

Sau mỗi phiên thử, kiểm tra:

- `~/.giaoit/captures/pending/` — rỗng (tất cả đã gửi)
- `~/.giaoit/captures/sent/` — có các thư mục `<capture_id>/` với `payload.json` + ảnh PNG
- `~/.giaoit/received/` — receiver dump (verify phép thử 5)

## 10. Troubleshooting

### "TTS connection has not been made yet"

- DLL chưa cài → làm lại bước 4 với admin
- Diablo IV không chạy với admin → set `Diablo IV.exe` Properties → Compatibility → Run as administrator
- Xem chi tiết: [README.md mục Common problems](README.md#common-problems)

### Python import error sau khi copy thư mục

- Chưa chạy `uv sync` ở máy đích
- `.venv\` bị copy từ máy khác (sai path) → xóa rồi `uv sync` lại

### Bridge không thấy file capture

- Tool d4lf chưa bật `Capture Mode` trong Settings
- Receiver chưa chạy → bridge retry, file ở `pending/`

### UI không tiếng Việt sau khi chọn viVN

- Đổi language cần **restart d4lf** (warning sẽ hiện trong dashboard)
- Xem `~/.d4lf/params.ini` phải có `language = viVN` ở section `[general]`
