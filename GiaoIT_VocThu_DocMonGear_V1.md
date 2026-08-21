# GIAO ĐỘI IT — VỌC THỬ PHẦN ĐỌC MÓN GEAR

**Bản V1 · ngày 11 tháng 8 năm 2026 · người giữ: Trung · lưu hành nội bộ**

---

## 0 · Đọc trước — đây là bản vứt đi, không phải bản dựng thật

Tài liệu 2 mẻ 1 chưa ra. Chính nó mới chốt bộ trường của một món, tên bảng, và mã sự kiện. Đợt này chỉ để trả lời câu **có chạy được không**, không phải để dựng cái dùng lâu dài.

Ba chỗ được dựng thật, vì tài liệu 2 sẽ không đổi chúng:

1. Bản sao kho mã nguồn của tool, ghim một bản, có người trong đội nhận nuôi.
2. Đoạn chèn ghi món ra tệp trong tool.
3. Bốn tệp danh mục tải về và giữ lại.

Bốn chỗ chỉ được dựng tạm, và phải vứt khi tài liệu 2 ra:

1. Bảng chứa món trong cơ sở dữ liệu. Đừng đặt tên bảng, đừng tạo DocType thật. Đổ tạm vào tệp hoặc một bảng nháp.
2. Cửa nhận. Dựng một cửa tạm cho chạy được, đừng gắn vào QT-06.
3. Màn hình xác nhận và màn hình tìm.
4. Mọi luật nghiệp vụ. Trạng thái món, giữ hàng, thanh lý, kiểm kho — không đụng tới.

**Không đổ dữ liệu của đợt vọc vào cơ sở dữ liệu đang chạy thật.** Dựng một bản riêng.

---

## 1 · Sáu thứ lấy từ tool, và mỗi thứ về đâu

Kho mã nguồn: github.com/d4lfteam/d4lf. Giấy phép MIT, dùng được trong sản phẩm thương mại, chỉ phải giữ lại dòng ghi công của tác giả.

**Việc đầu tiên: sao trọn kho về giữ riêng và ghim đúng một bản.** Không gọi thẳng vào bản mới nhất của họ. Lý do: dự án chỉ có một người duy trì chính, và lý do tồn tại chính của nó là lọc đồ rơi, việc mà nhà phát hành đã làm luôn trong game từ mùa 13. Người dùng sẽ rời đi. Từ lúc ghim bản, nó là mã nguồn của công ty phải nuôi, không phải thư viện đi mượn.

### 1.1 · Phần đọc một món

Diablo 4 có chức năng đọc màn hình cho người khiếm thị và cho nạp một thư viện đọc của bên thứ ba. Tool thay thư viện đó bằng thư viện của nó, nên chữ do chính game đưa ra, không phải máy nhìn ảnh mà đoán.

Đây là nguồn nhập chính. Không có sai số phiên chữ.

### 1.2 · Phần đọc trọn rương

Một lượt đọc ra cả danh sách món trong rương. Về sau đây là nguồn cho việc kiểm kho. Đợt này chỉ cần chứng minh đọc ra được.

### 1.3 · Bốn tệp danh mục

Nằm ở `assets/lang/enUS/` trong kho. Đếm ngày 11 tháng 8 năm 2026:

| Tệp | Số dòng | Chở gì |
|---|---|---|
| affixes.json | 877 | Tên chỉ số |
| item_types.json | 33 | Loại món, tức ô trang bị |
| uniques.json | 298 | Tên món Unique, kèm số dòng chỉ số cố hữu |
| aspects.json | 584 | Tên aspect |

Mỗi dòng là một cặp gồm tên máy dùng và tên hiển thị. Đây là bộ mồi cho danh mục tên chỉ số. Tải về giữ lại, đừng gọi qua mạng mỗi lần chạy.

Kho có nhiều ngôn ngữ. Chỉ dùng `enUS`, vì game của mình để tiếng Anh.

### 1.4 · Bộ hình mẫu nhận dạng trên tooltip

Nằm ở `assets/templates/item_descr/`, 68 tấm. Ba nhóm dùng được:

- Hình dấu đầu dòng của một chỉ số thường và của một Greater Affix, gồm cả biến thể khi món đã masterwork.
- Hình góc trên bên trái của tooltip, phân theo hạng món: magic, rare, legendary, unique, mythic.
- Hình cạnh dưới của tooltip.

Bộ này dùng cho **đường đọc ảnh**, tức đường không cần cài gì vào game. Đợt vọc này chưa cần, nhưng tải về giữ luôn.

### 1.5 · Cấu trúc dữ liệu một món

`src/item/models.py` và `src/item/data/affix.py`. Đây là hình của bộ trường, chép được nguyên.

### 1.6 · Mô hình khai điều kiện lọc

`src/item/filter/`. Cách họ khai một điều kiện kiểu *chỉ số này bắt buộc phải là Greater Affix, chỉ số kia thì thường cũng được, giá trị tối thiểu bao nhiêu, phần trăm so với khoảng tối đa bao nhiêu*.

Không chép mã của họ — bộ lọc của họ chạy trên máy người chơi soi mấy chục món trước mắt, còn màn hình tìm của mình chạy trên máy chủ soi cả nghìn món. Chỉ chép cách khai điều kiện.

---

## 2 · Năm thứ tắt hoặc bỏ qua

1. **Phần tự điều khiển chuột để dọn đồ trong rương — tắt hẳn.** Tool có sẵn lựa chọn chỉ nhìn không chạm, bật cái đó. Đây là phần nặng rủi ro nhất và nó không phục vụ việc gì của mình.
2. Lớp phủ bảng paragon.
3. Lớp phủ đếm giờ world boss, legion, helltide, và đếm vàng với kinh nghiệm mỗi giờ.
4. Vẽ khung lên màn hình khi món khớp bộ lọc.
5. Nhập bộ lọc từ các trang dựng build, và phần sigil với tribute.

---

## 3 · Cách xử lý code

### 3.1 · Hình chung: tách hai đoạn, không cho tool gọi thẳng vào máy chủ

```
[game] → [tool, đã sửa] → ghi tệp vào thư mục
                                 ↓
                          [cầu nối, chương trình riêng]
                                 ↓
                          [cửa nhận trên máy chủ]
```

Bốn lý do tách:

- Tool đổi theo mùa. Cắm một khối lớn vào giữa mã của người khác thì lần nào hoà bản mới cũng đau.
- Máy chơi game hay mất mạng và hay đóng đột ngột. Ghi ra tệp thì món nằm đó chờ; gọi thẳng mà lỗi mạng là mất luôn cái vừa đọc mà người không biết.
- Khoá mở cửa vào phần mềm công ty không nên nằm trong mã nguồn của người khác.
- Về sau đổi sang đường đọc ảnh thì cầu nối giữ nguyên không sửa một chữ, chỉ đổi cái sinh ra tệp.

### 3.2 · Chỗ chèn thứ nhất — ghi món ra tệp

**Tệp:** `src/loot/filter.py`, hàm `check_items`.

Đây là vòng đọc món. Sau khi tool đọc xong một món, chỗ đó đã có sẵn đối tượng món.

**Việc phải làm:** ghi đối tượng món ra một tệp JSON trong thư mục quy ước, kèm tấm ảnh vùng tooltip.

**Chỗ này nhẹ hơn tưởng.** Trong `src/item/models.py` đã có sẵn một lớp tên `ItemJSONEncoder`, chuyển một món ra JSON với đúng các trường cần. Nó đã được xuất ra ở `src/item/__init__.py` nhưng **chưa chỗ nào trong tool gọi tới**. Nên đoạn chèn chỉ là gọi `json.dump` với bộ mã hoá đó, cộng phần chụp ảnh và phần ghi mấy trường của mình. Khoảng năm tới mười dòng.

### 3.3 · Chỗ chèn thứ hai — thêm một phím tắt

**Tệp:** `src/app/handler.py`, chỗ tool đang đăng ký các phím tắt.

Thêm hai phím mới, tách khỏi phím chạy bộ lọc sẵn có:

- Một phím: gửi món đang rê chuột vào kho.
- Một phím: đọc trọn rương.

Không đụng gì khác trong tool.

### 3.4 · Ảnh

Tool có sẵn phần chụp màn hình và bộ hình mẫu để tìm khung tooltip, nên gọi ra là được. Lưu cùng thư mục với tệp món, cùng tên khác đuôi.

**Ảnh là bắt buộc, không phải tuỳ chọn.** Thư viện đọc chỉ đưa chữ, mà mọi món gear phải có ảnh khoá lại làm bản ghi chống tráo.

---

## 4 · Cấu trúc tệp ghi ra

Lấy đúng theo cấu trúc của tool, cộng bốn trường của mình.

**Phần đầu món** — từ `Item` trong `src/item/models.py`:

| Trường | Kiểu | Ghi chú |
|---|---|---|
| `item_type` | chữ | Loại món, tức ô trang bị |
| `rarity` | chữ | Hạng món |
| `name` | chữ | Tên món riêng, chỉ có với Unique và Mythic |
| `power` | số nguyên | Chỉ số sức mạnh của món |
| `is_ancestral` | đúng/sai | |
| `codex_upgrade` | đúng/sai | |
| `set_name` | chữ | |
| `affixes` | danh sách | Các dòng chỉ số |
| `inherent` | danh sách | Các dòng chỉ số cố hữu của nền món |
| `aspect` | một khối | Sức mạnh riêng |

**Mỗi dòng chỉ số** — từ `Affix` trong `src/item/data/affix.py`:

| Trường | Kiểu | Ghi chú |
|---|---|---|
| `name` | chữ | Tên máy dùng, khớp với affixes.json |
| `text` | chữ | Chữ nguyên văn như game viết |
| `value` | số | Giá trị |
| `min_value` | số | Đáy của khoảng |
| `max_value` | số | Trần của khoảng |
| `type` | chữ | Một trong năm: `normal`, `inherent`, `greater`, `rerolled`, `tempered` |

**Cột `type` là cột quan trọng nhất trong cả tệp.** Giá trị `greater` là dấu Greater Affix, tức trị số đắt nhất khi định giá. Còn `rerolled` và `tempered` là dấu món **đã bị sửa nên đã khoá vào tài khoản và không bán được nữa** — món dính hai giá trị này không được vào kho hàng hoá.

**Khối aspect** — cùng hình với một dòng chỉ số: `name`, `text`, `value`, `min_value`, `max_value`.

**Bốn trường của mình, tool không có, phải tự thêm:**

| Trường | Ghi chú |
|---|---|
| `capture_id` | Mã riêng của lần chụp, sinh ngẫu nhiên. Để đẩy hai lần không đẻ hai món |
| `captured_at` | Lúc chụp |
| `machine_id` | Máy nào chụp |
| `image_file` | Tên tệp ảnh đi kèm |

---

## 5 · Cầu nối — sáu việc

Chương trình nhỏ riêng, chạy nền trên cùng máy. Đợt vọc dựng bản tối giản cũng được, nhưng phải đủ sáu việc để biết hình nó có chạy không.

1. **Canh thư mục**, thấy tệp mới thì đọc lên.
2. **Bày màn hình xác nhận**: ảnh một bên, các ô máy đọc một bên, người sửa được.
3. **Gắn tài khoản game.** Bản thật sẽ hỏi phần mềm xem người này đang mở quãng dùng tài khoản nào. Đợt vọc thì cho chọn tay cũng được, nhưng phải biết bản thật không làm vậy — chọn tay là chỗ sẽ sai và sai lặng lẽ.
4. **Gửi kèm `capture_id`** để đẩy hai lần không đẻ hai món.
5. **Đẩy vào cửa nhận.** Thành công thì chuyển tệp sang thư mục *đã gửi*. Thất bại thì giữ nguyên tệp và thử lại, có hàng đợi trên đĩa.
6. **Giữ nhật ký riêng**, để lần ra được một món đã đọc mà chưa đẩy hay chưa từng đọc.

**Tệp đọc trọn rương đi cùng đường này**, chỉ khác loại tệp: cầu nối thấy loại đó thì không bày màn hình xác nhận mà đẩy thẳng.

---

## 6 · Năm phép thử phải chạy trong đợt vọc

Đây là cái đợt này phải trả lời. Mỗi phép ghi lại kết quả bằng số.

**Phép 1 — đọc được một món.** Cài, bật hai lựa chọn đọc màn hình trong phần trợ năng của game, bật hiện chỉ số đầy đủ trong tooltip, để game tiếng Anh. Rê chuột lên một món, bấm phím, ra một tệp JSON đúng cấu trúc ở mục 4.

**Phép 2 — cờ Greater Affix đọc đúng.** Lấy hai chục món trong đó có món mang Greater Affix. Đếm bao nhiêu món đọc đúng cột `type`. **Đây là con số quan trọng nhất của cả đợt**, vì nó là trị số đắt nhất khi định giá.

**Phép 3 — đọc trọn rương.** Một rương đầy, một lượt, ra một tệp chứa cả danh sách. Đếm số món trong tệp so với số món đếm bằng mắt.

**Phép 4 — bốn tệp danh mục nạp được.** Đổ 877 dòng tên chỉ số vào một bảng nháp. Rồi lấy các món đã đọc ở phép 1 và 2, xem trường `name` của từng dòng chỉ số có khớp vào danh mục không. Đếm tỉ lệ khớp. Không khớp thì phải biết vì sao.

**Phép 5 — đẩy hai lần không đẻ hai món.** Đẩy cùng một tệp vào cửa nhận hai lần, số món sinh ra phải bằng một.

**Một phép nữa làm sau, khi có sẵn dữ liệu:** đường đọc ảnh chạy trên chính mấy tấm ảnh của phép 1 và 2, so kết quả với chữ tool đọc ra. Đây là cách đo độ chính xác của đường ảnh mà không tốn buổi riêng nào, vì mỗi món đã có sẵn cả hai.

---

## 7 · Điều kiện an toàn khi chạy thử

Đây là đợt **thử nghiệm an toàn**, chưa phải dùng thật. Trung chốt: an toàn thì mới dùng.

- **Chạy trên tài khoản không giữ hàng giá trị.** Đừng chạy trên tài khoản trader đang ôm hàng.
- **Tắt hẳn phần điều khiển chuột**, bật chế độ chỉ nhìn không chạm. Đây là điều kiện cứng, không phải khuyến nghị.
- **Chỉ bật trong lúc thử, tắt lúc chạy đơn và lúc cày.**
- **Ghi lại tổng số giờ đã chạy** để cuối đợt đối chiếu.

Cái phải biết trước khi bấm nút: điều khoản của Blizzard cấm phần mềm trái phép nào tự động hoá, sửa đổi, hay can thiệp vào game, và họ đã dùng đúng câu đó khi cấm một công cụ chỉ hiển thị thông tin. Việc chép một tệp thư viện vào thư mục cài game nằm trong chữ *sửa đổi*. Không tìm thấy báo cáo bị khoá nào vì riêng tool này, nhưng không có báo cáo không có nghĩa là an toàn.

**Điều kiện vận hành của tool:** Windows; game để ngôn ngữ tiếng Anh; bật hiện chỉ số đầy đủ trong tooltip; bật hai lựa chọn đọc màn hình trong phần trợ năng; tắt dải sáng rộng; cỡ chữ và độ phân giải theo đúng bộ tool đòi.

---

## 8 · Ba câu phải báo lại

1. Năm phép thử ở mục 6 ra con số bao nhiêu, đặc biệt phép 2.
2. Tổng số giờ đã chạy và tài khoản có sao không.
3. Chỗ nào trong tool khó sửa hơn tưởng, để lượt cắt tài liệu 2 biết mà tính lại.
