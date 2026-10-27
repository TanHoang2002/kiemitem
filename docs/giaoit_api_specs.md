# GiaoIT V1 API Specifications

Tài liệu đặc tả các API của hệ thống GiaoIT V1 (BotFillItem). Bao gồm API điều khiển cục bộ (Local API) và API máy chủ nhận dữ liệu (Receiver API).

---

## 1. API Điều khiển Cục bộ (Local API)
API chạy trực tiếp trên máy của người chơi game dùng để gửi lệnh điều khiển hoạt động của Bot từ xa.

* **Base URL:** `http://127.0.0.1:18080`
* **Giao thức:** Hỗ trợ `GET` hoặc `POST`.

### 1.1. Quét Rương đồ (Trigger Stash Scan - F4)
Kích hoạt bot tự động quét toàn bộ rương và các tab rương đã cấu hình.
* **Path:** `/trigger/f4`
* **Tham số truy vấn (Query parameters):**
  * `account_id` *(Tùy chọn)*: Tên hoặc ID tài khoản game để gắn nhãn dữ liệu.
* **cURL Example:**
  ```bash
  curl "http://127.0.0.1:18080/trigger/f4?account_id=acc_kled"
  ```
* **Response (JSON):**
  ```json
  {
    "ok": true,
    "triggered": "F4",
    "account_id": "acc_kled"
  }
  ```

### 1.2. Thống kê Tiền tệ/Khóa (Trigger Currency Scan - F6)
Kích hoạt bot quét nhanh số lượng khóa, nguyên liệu trong tab rương hiện tại.
* **Path:** `/trigger/f6`
* **Tham số truy vấn (Query parameters):**
  * `account_id` *(Tùy chọn)*: Tên hoặc ID tài khoản game.
* **cURL Example:**
  ```bash
  curl "http://127.0.0.1:18080/trigger/f6?account_id=acc_kled"
  ```
* **Response (JSON):**
  ```json
  {
    "ok": true,
    "triggered": "F6",
    "account_id": "acc_kled"
  }
  ```

### 1.3. Quét Túi đồ Cá nhân (Trigger Inventory Scan - F11)
Kích hoạt bot chạy bộ lọc quét đồ trên túi đồ của nhân vật.
* **Path:** `/trigger/f11`
* **cURL Example:**
  ```bash
  curl "http://127.0.0.1:18080/trigger/f11"
  ```
* **Response (JSON):**
  ```json
  {
    "ok": true,
    "triggered": "F11"
  }
  ```

### 1.4. Kích Hoạt Tìm Chỉ Số (Trigger Affix Search - F5)
* **Path:** `/trigger/f5`
* **cURL Example:**
  ```bash
  curl "http://127.0.0.1:18080/trigger/f5"
  ```
* **Response (JSON):**
  ```json
  {
    "ok": true,
    "triggered": "F5"
  }
  ```

---

## 2. API Máy chủ Nhận Dữ liệu (Receiver API)
API chạy trên máy chủ để cầu nối (Bridge) đẩy dữ liệu lên và để người dùng lấy dữ liệu kho hàng ra sử dụng.

* **Base URL mặc định:** `http://192.168.2.115` (Có thể tùy chỉnh theo IP máy chủ thực tế).
* **Giao thức:** REST API.

### 2.1. Đẩy Dữ liệu Quét Lên Máy Chủ (`POST /items`)
Endpoint này nhận dữ liệu từ Bridge đẩy lên.
* **Method:** `POST`
* **Content-Type:** `multipart/form-data`
* **Tham số gửi lên (Form Data):**
  * `payload` *(Chuỗi JSON)*: Chứa cấu trúc món đồ, loại đồ, các chỉ số affixes, rolls...
  * `account_id` *(Chuỗi)*: ID tài khoản game thực hiện quét.
  * `images` *(Tập tin)*: Danh sách các ảnh cắt tooltip `.png` của trang bị (nếu có).
* **cURL Example:**
  ```bash
  curl -X POST "http://192.168.2.115/items" \
    -F "account_id=acc_kled" \
    -F "payload={\"schema\":\"giaoit.capture.v1\",\"capture_id\":\"uuid-12345\",\"kind\":\"stash\",\"items\":[]}" \
    -F "images=@latest_stash_000.png"
  ```
* **Response (JSON):**
  ```json
  {
    "ok": true,
    "id": "uuid-12345",
    "capture_id": "uuid-12345",
    "deduped": false,
    "deduped_by_capture_id": false,
    "deduped_by_hash": false,
    "items_count": 0
  }
  ```

### 2.2. Lấy Thống Kê Kho Hiện Tại (`GET /warehouse`)
Lấy số lượng nguyên liệu/khóa mới nhất của từng tài khoản.
* **Method:** `GET`
* **cURL Example:**
  ```bash
  curl "http://192.168.2.115/warehouse"
  ```
* **Response (JSON):**
  ```json
  {
    "acc_kled": {
      "last_updated": "2026-08-27 03:41:04 UTC",
      "currencies": {
        "Greater Lair Key": 20182,
        "Lair Key": 237429,
        "Superior Lair Key": 0,
        "Corrupted Roots": 0,
        "Crux of the False Prophet": 0
      }
    }
  }
  ```

### 2.3. Xem Lịch Sử Thay Đổi Kho (`GET /warehouse/history`)
* **Method:** `GET`
* **cURL Example:**
  ```bash
  curl "http://192.168.2.115/warehouse/history"
  ```

### 2.4. Xem Chi Tiết 1 Lượt Quét (`GET /items/{capture_id}`)
* **Method:** `GET`
* **cURL Example:**
  ```bash
  curl "http://192.168.2.115/items/uuid-12345"
  ```

---

## 3. Các Lệnh Khởi Động Hệ Thống

* **Chạy Tool Bot D4LF:**
  ```bash
  uv run python -m src.main
  ```
* **Chạy Máy chủ Nhận (Receiver):**
  ```bash
  uv run uvicorn receiver.main:app --host 0.0.0.0 --port 8000
  ```
* **Chạy Cầu Nối (Bridge - Headless):**
  ```bash
  set GIAOIT_RECEIVER_URL=http://<IP_SERVER>:8000
  uv run python -m bridge.main --headless
  ```
