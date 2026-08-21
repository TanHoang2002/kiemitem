"""Vietnamese string catalog. Keys mirror :mod:`src.i18n.en` exactly."""

STRINGS_VI: dict[str, str] = {
    # ── Settings window ────────────────────────────────────────────────────
    "Settings": "Cài đặt",
    "Save": "Lưu",
    "Cancel": "Hủy",
    "OK": "Đồng ý",
    "Yes": "Có",
    "No": "Không",
    "Restart now": "Khởi động lại ngay",
    "Later": "Để sau",
    "Reset Settings": "Đặt lại cài đặt",
    "Would you like to reset only the '{tab_name}' settings or all settings to defaults?": (
        "Bạn muốn đặt lại chỉ cài đặt '{tab_name}' hay toàn bộ về mặc định?"
    ),
    "Reset {tab_name}": "Đặt lại {tab_name}",
    "Reset All Tabs": "Đặt lại tất cả tab",
    "This will reset ALL custom values in your params.ini. Are you sure?": (
        "Việc này sẽ đặt lại TOÀN BỘ giá trị trong params.ini. Bạn chắc chắn chứ?"
    ),
    "Reset to defaults": "Đặt lại về mặc định",
    "Restart required": "Cần khởi động lại",
    "Vision mode changes require restarting d4lf. Restart now?": (
        "Thay đổi chế độ Vision cần khởi động lại d4lf. Khởi động lại ngay?"
    ),
    "Restart failed": "Khởi động lại thất bại",
    "d4lf could not be restarted automatically. Please restart it manually.": (
        "d4lf không thể tự khởi động lại. Vui lòng khởi động lại thủ công."
    ),
    "Error validating value": "Lỗi khi kiểm tra giá trị",
    "Your value has been reset to its previous version.": (
        "Giá trị của bạn đã được đặt lại về phiên bản trước đó."
    ),
    "Set Hotkey": "Đặt phím tắt",
    "Press the key or combination of keys you\nwant to use as a hotkey, then click save.": (
        "Nhấn phím hoặc tổ hợp phím bạn\nmuốn dùng làm phím tắt, sau đó bấm Lưu."
    ),
    "Search settings...": "Tìm cài đặt...",
    "Key Bindings": "Phím tắt",
    "Technical Settings": "Cài đặt kỹ thuật",
    # ── Settings category labels ───────────────────────────────────────────
    "📦 Loot Behavior": "📦 Hành vi nhặt đồ",
    "📄 Profiles": "📄 Hồ sơ",
    "🤖 Automation": "🤖 Tự động",
    "🎒 Stash & Transfer": "🎒 Rương & Chuyển đồ",
    "🎨 UI & Theme": "🎨 Giao diện & Chủ đề",
    "⚙️ System & Paths": "⚙️ Hệ thống & Đường dẫn",
    "⌨️ Hotkeys": "⌨️ Phím tắt",
    "🛠️ Advanced": "🛠️ Nâng cao",
    # ── MoveItemsType labels ───────────────────────────────────────────────
    "Favorites": "Yêu thích",
    "Junk": "Rác",
    "Unmarked": "Chưa đánh dấu",
    # ── Dashboard ──────────────────────────────────────────────────────────
    "Dashboard": "Bảng điều khiển",
    "Full Logs": "Nhật ký đầy đủ",
    "ACTIVE PROFILES": "HỒ SƠ ĐANG BẬT",
    "Toggle profiles to enable them. Drag <b>⠿</b> to set priority; the top profile determines affix highlighting.": (
        "Bật/tắt các hồ sơ để kích hoạt. Kéo <b>⠿</b> để đặt ưu tiên; hồ sơ trên cùng quyết định hiển thị affix."
    ),
    "Filter profiles...": "Lọc hồ sơ...",
    "Enable All": "Bật tất cả",
    "Disable All": "Tắt tất cả",
    "KEYBOARD SHORTCUTS": "PHÍM TẮT",
    "Show Activity Log": "Hiện nhật ký hoạt động",
    "Import Profile": "Nhập hồ sơ",
    "Minimize to Tray": "Thu nhỏ vào khay",
    "Vision Mode: STOPPED": "Vision Mode: ĐÃ DỪNG",
    "Vision Mode: RUNNING": "Vision Mode: ĐANG CHẠY",
    "Vision Mode: Disabled (GUI-only)": "Vision Mode: Tắt (chỉ GUI)",
    "TTS: Disconnected": "TTS: Ngắt kết nối",
    "TTS: Connected": "TTS: Đã kết nối",
    "TTS: Disabled (GUI-only)": "TTS: Tắt (chỉ GUI)",
    "TTS connection has not been made yet. Have you followed all of the instructions in %s? If so, it's possible your Windows user does not have the correct permissions to allow Diablo 4 to connect to a third party screen reader.": (
        "Chưa kết nối được TTS. Bạn đã làm theo tất cả hướng dẫn trong %s chưa? "
        "Nếu rồi, có thể tài khoản Windows của bạn không đủ quyền để Diablo 4 "
        "kết nối với trình đọc màn hình của bên thứ ba."
    ),
    # ── Profile card ───────────────────────────────────────────────────────
    "Edit": "Sửa",
    "Edit Profile": "Sửa hồ sơ",
    "Delete": "Xóa",
    "Delete Profile": "Xóa hồ sơ",
    "Are you sure you want to permanently delete the profile '{name}'?": (
        "Bạn có chắc muốn xóa vĩnh viễn hồ sơ '{name}' không?"
    ),
    "No Profiles found. Please import a profile below.": (
        "Không tìm thấy hồ sơ. Vui lòng nhập hồ sơ bên dưới."
    ),
    "Last Modified:": "Sửa lần cuối:",
    "Items:": "Món đồ:",
    "Affix Filters:": "Bộ lọc affix:",
    "Aspect Upgrades:": "Nâng cấp Aspect:",
    "Global Uniques:": "Unique toàn cục:",
    "Sigils: Included": "Sigil: Đã bao gồm",
    "Tributes: Included": "Tribute: Đã bao gồm",
    "Paragon Overlay: Data Found": "Overlay Paragon: Có dữ liệu",
    "(Could not parse profile details)": "(Không thể phân tích chi tiết hồ sơ)",
    # ── Tray ───────────────────────────────────────────────────────────────
    "Restore": "Hiển thị lại",
    "Exit": "Thoát",
    "D4 Loot Filter": "Bộ lọc đồ D4",
    "D4LF settings reload failed": "Tải lại cài đặt D4LF thất bại",
    "D4LF profile loading": "Đang tải hồ sơ D4LF",
    # ── Profile editor ─────────────────────────────────────────────────────
    "Profile Editor": "Trình sửa hồ sơ",
    "Profile": "Hồ sơ",
    "Undo Changes": "Hoàn tác thay đổi",
    "Instructions": "Hướng dẫn",
    "Select a profile from the dropdown. Click 'Save' to save your changes. Click 'Undo Changes' to revert your changes.": (
        "Chọn hồ sơ từ menu thả xuống. Bấm 'Lưu' để lưu thay đổi. Bấm 'Hoàn tác thay đổi' để quay lại."
    ),
    "Unsaved Changes": "Thay đổi chưa lưu",
    "You have unsaved changes. Do you want to save them before closing?": (
        "Bạn có thay đổi chưa lưu. Có muốn lưu trước khi đóng không?"
    ),
    "Alert": "Cảnh báo",
    "--------- Active Profiles ---------": "--------- Hồ sơ đang bật ---------",
    "--------- Inactive Profiles ---------": "--------- Hồ sơ đang tắt ---------",
    "No profiles found": "Không tìm thấy hồ sơ",
    "Profile Validation Failed": "Kiểm tra hồ sơ thất bại",
    "Validation Error": "Lỗi kiểm tra",
    "Info": "Thông tin",
    "Profile saved successfully": "Đã lưu hồ sơ thành công",
    "Profile saved successfully to {name}": "Đã lưu hồ sơ thành công vào {name}",
    "Warning": "Cảnh báo",
    "The profile model might not be valid. Do you still want to save your changes ?": (
        "Hồ sơ có thể không hợp lệ. Bạn vẫn muốn lưu thay đổi chứ?"
    ),
    "Profile not saved.": "Chưa lưu hồ sơ.",
    "Error": "Lỗi",
    "Remove Selected": "Xóa các mục đã chọn",
    "Select at least one rule to remove.": "Chọn ít nhất một quy tắc để xóa.",
    "Add": "Thêm",
    "Remove": "Xóa",
    "Delete Items": "Xóa các mục",
    "Items": "Món đồ",
    "Select items to delete:": "Chọn mục cần xóa:",
    "Set Min Power": "Đặt Power tối thiểu",
    "Min Power:": "Power tối thiểu:",
    "Set Min Greater Affix": "Đặt GA tối thiểu",
    "Min Greater Affix:": "GA tối thiểu:",
    "Set Min Percent Of Affix": "Đặt % affix tối thiểu",
    "Min Percent Of Affix:": "% affix tối thiểu:",
    # ── Profile editor per-section tabs ────────────────────────────────────
    "Affixes": "Affix",
    "Value": "Giá trị",
    "Min %": "% tối thiểu",
    "Unique Aspects": "Aspect Unique",
    "Create Item": "Tạo món",
    "Remove Item": "Xóa món",
    "Set All Min GAs (Excludes Auto Synced Items)": (
        "Đặt GA tối thiểu cho tất cả (trừ món tự đồng bộ)"
    ),
    "Convert All To Min %": "Chuyển tất cả sang % tối thiểu",
    "Set all minPower": "Đặt Power tối thiểu cho tất cả",
    "Item name already exist please rename {item_name} in the profile file.": (
        "Tên món đã tồn tại, vui lòng đổi tên {item_name} trong file hồ sơ."
    ),
    "Aspect Upgrades": "Nâng cấp Aspect",
    "Add any legendary aspects you'd like to have favorited if an upgrade is found. See the readme on AspectUpgrades for more information.": (
        "Thêm các aspect legendary bạn muốn đánh dấu yêu thích khi tìm thấy bản nâng cấp. Xem readme về AspectUpgrades để biết thêm."
    ),
    "Add Aspect": "Thêm Aspect",
    "Sigils": "Sigil",
    "Add Sigil": "Thêm Sigil",
    "Remove Whitelist Sigil": "Xóa Sigil whitelist",
    "Remove Blacklist Sigil": "Xóa Sigil blacklist",
    "Priority:": "Ưu tiên:",
    "Rarities:": "Độ hiếm:",
    "Blacklist": "Danh sách đen",
    "Whitelist": "Danh sách trắng",
    "Sigil already exist in whitelist. You can modify the existing one.": (
        "Sigil đã có trong danh sách trắng. Bạn có thể sửa mục đã có."
    ),
    "Sigil already exist in blacklist. You can modify the existing one.": (
        "Sigil đã có trong danh sách đen. Bạn có thể sửa mục đã có."
    ),
    "Add tribute names and select rarities you want to keep. Leaving rarities empty keeps all rarities.": (
        "Thêm tên tribute và chọn độ hiếm cần giữ. Để trống độ hiếm để giữ tất cả."
    ),
    "Add Tribute": "Thêm Tribute",
    "Select at least one tribute rule to remove.": "Chọn ít nhất một quy tắc tribute để xóa.",
    "Global Unique Rule": "Quy tắc Unique toàn cục",
    "Profile Alias:": "Bí danh hồ sơ:",
    "Minimum Power:": "Power tối thiểu:",
    "Min Greater Affixes:": "GA tối thiểu:",
    "Min Percent of Aspect:": "% Aspect tối thiểu:",
    "Create Rule": "Tạo quy tắc",
    "Remove Rule": "Xóa quy tắc",
    "Unique Rule {index}": "Quy tắc Unique {index}",
    "Create {kind}": "Tạo {kind}",
    "Remove {kind}": "Xóa {kind}",
    "{kind} name already exists, please rename {item_name} in the profile file.": (
        "Tên {kind} đã tồn tại, vui lòng đổi tên {item_name} trong file hồ sơ."
    ),
    "No sets selected": "Chưa chọn set nào",
    "Auto Sync": "Tự đồng bộ",
    "When checked: Min Greater Affixes automatically matches the number of affixes marked as 'want greater'\nWhen unchecked: You can manually set Min Greater Affixes to any value": (
        "Khi tích: GA tối thiểu tự khớp với số lượng affix được đánh dấu 'want greater'\n"
        "Khi không tích: Bạn có thể tự đặt GA tối thiểu theo ý muốn"
    ),
    "Default file name: {value}": "Tên file mặc định: {value}",
    "Custom file name:": "Tên file tùy chỉnh:",
    "Leave blank for default filename": "Để trống nếu dùng tên file mặc định",
    "Default filename includes...": "Tên file mặc định bao gồm...",
    "Found {count} variants in {source}.\nSelect which variants to keep:": (
        "Tìm thấy {count} biến thể trong {source}.\nChọn biến thể cần giữ:"
    ),
    "Variant {index}": "Biến thể {index}",
    "Import Aspect Upgrades": "Nhập nâng cấp Aspect",
    "If legendary aspects are in the build, do you want an aspect upgrades section generated for them?": (
        "Nếu build có aspect legendary, bạn có muốn tạo mục nâng cấp aspect cho chúng không?"
    ),
    "Import Charms": "Nhập Charm",
    "If a build has charms, should they be included in the imported profile?": (
        "Nếu build có charm, có nên đưa vào hồ sơ đã nhập không?"
    ),
    "Import Seals": "Nhập Seal",
    "If a build has seals, should they be included in the imported profile?": (
        "Nếu build có seal, có nên đưa vào hồ sơ đã nhập không?"
    ),
    "Add to profiles": "Thêm vào hồ sơ",
    "Do you want to add this build to your active profiles upon generating?": (
        "Bạn có muốn thêm build này vào hồ sơ đang bật khi tạo không?"
    ),
    "Include GAs": "Bao gồm GA",
    "Include the greater affix tags from the build, making it look for GAs?": (
        "Bao gồm tag greater affix từ build, để tìm các GA?"
    ),
    "Require all GAs": "Yêu cầu tất cả GA",
    "Are the GAs required to match the item?": "Các GA có bắt buộc phải khớp với món đồ không?",
    "Import Paragon": "Nhập Paragon",
    "Import paragon boards for the paragon overlay?": "Nhập bảng Paragon cho overlay Paragon?",
    "Multi Build Import": "Nhập nhiều Build",
    "Import multiple builds from the link?": "Nhập nhiều build từ link?",
    "You can link either the build guide or a direct link to the specific planner.\n\nhttps://maxroll.gg/d4/build-guides/tornado-druid-guide\nor\nhttps://maxroll.gg/d4/planner/cm6pf0xa#5\nor\nhttps://d4builds.gg/builds/ef414fbd-81cd-49d1-9c8d-4938b278e2ee\nor\nhttps://mobalytics.gg/diablo-4/builds/barbarian/bash\nor\nhttps://infinitybuilds.gg/en/builds/barbarian-fL8P6vVSqI\n\nIt will create a file based on the label of the build in the planner in: {user_dir}\\profiles\n\n": (
        "Bạn có thể dùng link hướng dẫn build hoặc link trực tiếp đến planner cụ thể.\n\n"
        "https://maxroll.gg/d4/build-guides/tornado-druid-guide\n"
        "hoặc\n"
        "https://maxroll.gg/d4/planner/cm6pf0xa#5\n"
        "hoặc\n"
        "https://d4builds.gg/builds/ef414fbd-81cd-49d1-9c8d-4938b278e2ee\n"
        "hoặc\n"
        "https://mobalytics.gg/diablo-4/builds/barbarian/bash\n"
        "hoặc\n"
        "https://infinitybuilds.gg/en/builds/barbarian-fL8P6vVSqI\n\n"
        "Nó sẽ tạo file dựa trên nhãn của build trong planner tại: {user_dir}\\profiles\n\n"
    ),
    "Source": "Nguồn",
    "Season": "Mùa",
    "Class": "Class",
    "Build title": "Tên build",
    "Select at least one filename part or enter a custom file name.": (
        "Chọn ít nhất một phần tên file hoặc nhập tên file tùy chỉnh."
    ),
    "none": "không có",
    # ── Importer wizard ────────────────────────────────────────────────────
    "Profile Importer - d2core / Maxroll / D4Builds / Mobalytics / InfinityBuilds": (
        "Trình nhập hồ sơ - d2core / Maxroll / D4Builds / Mobalytics / InfinityBuilds"
    ),
    "Log:": "Nhật ký:",
    "Instructions:": "Hướng dẫn:",
    "URL:": "URL:",
    "Generate": "Tạo",
    "Generating...": "Đang tạo...",
    "Saving...": "Đang lưu...",
    "Enter a URL to generate a profile.": "Nhập URL để tạo hồ sơ.",
    "Select variants to import": "Chọn biến thể cần nhập",
    # ── Overlay (info panel) ───────────────────────────────────────────────
    "World Boss:": "World Boss:",
    "Legion:": "Legion:",
    "Helltide:": "Helltide:",
    "GPH:": "Vàng/giờ:",
    "Pending": "Đang chờ",
    "|Gained:": "|Đạt:",
    "Gained:": "Đạt:",
    "EPH:": "KN/giờ:",
    "|Exp:": "|KN:",
    "Exp:": "KN:",
    "T2L:": "Còn:",
    "|Next Scan:": "|Quét tiếp:",
    "Next Scan:": "Quét tiếp:",
    "Ready": "Sẵn sàng",
    "SETTINGS": "CÀI ĐẶT",
    "Track Gold": "Theo dõi vàng",
    "Show Gold Per Hour": "Hiện vàng mỗi giờ",
    "Show Gold Gained": "Hiện vàng đạt được",
    "Gold Config": "Cấu hình Vàng",
    "Track Exp": "Theo dõi kinh nghiệm",
    "Show EXP Per Hour": "Hiện KN mỗi giờ",
    "Show EXP Gained": "Hiện KN đạt được",
    "Show Time to Level": "Hiện thời gian lên level",
    "Show Next Scan": "Hiện lần quét tiếp",
    "Auto-Capture Exp When Inventory Opened": "Tự chụp KN khi mở túi đồ",
    "EXP Capture Time": "Thời gian chụp KN",
    "Configure EXP Bar Position": "Cấu hình vị trí thanh KN",
    "Reset EXP Bar Position": "Đặt lại vị trí thanh KN",
    "Exp Config": "Cấu hình KN",
    "Reset Gold": "Đặt lại vàng",
    "Reset Exp": "Đặt lại KN",
    "Reset Stats": "Đặt lại thống kê",
    "Orientation:": "Hướng:",
    "Increase Size (+)": "Tăng cỡ (+)",
    "Decrease Size (-)": "Giảm cỡ (-)",
    "Font": "Phông chữ",
    "Never": "Không bao giờ",
    "0m": "0p",
    "3m": "3p",
    "5m": "5p",
    "10m": "10p",
    "30m": "30p",
    "60m": "60p",
    "Refresh Timers Now": "Làm mới bộ đếm ngay",
    "Lock Position": "Khóa vị trí",
    "Close Overlay": "Đóng overlay",
    "DRAG ACROSS YOUR EXPERIENCE BAR\n(Escape to cancel)": (
        "KÉO QUA THANH KINH NGHIỆM\n(Escape để hủy)"
    ),
    # ── LOGGER.info user-facing messages ───────────────────────────────────
    "Reloaded hotkeys from updated settings": "Đã tải lại phím tắt từ cài đặt mới",
    "Reloaded language assets for %s": "Đã tải lại tài nguyên ngôn ngữ cho %s",
    "Please restart d4lf manually to apply %s.": "Vui lòng khởi động lại d4lf thủ công để áp dụng %s.",
    "Closing Paragon overlay": "Đang đóng overlay Paragon",
    "Opening Paragon overlay (source: %s)": "Đang mở overlay Paragon (nguồn: %s)",
    "Closing Info Panel overlay": "Đang đóng overlay Info Panel",
    "Opening Info Panel overlay": "Đang mở overlay Info Panel",
    "Stopping filter or move process": "Đang dừng tiến trình lọc/chuyển đồ",
    "Running loot filter": "Đang chạy bộ lọc đồ",
    "Loot filter done": "Bộ lọc đồ hoàn tất",
    "Mark as favorite": "Đánh dấu yêu thích",
    # ── Bridge confirm UI ──────────────────────────────────────────────────
    "(no preview)": "(không xem trước)",
    "(no image)": "(không ảnh)",
    "Parsed item (editable before send):": "Món đã parse (có thể sửa trước khi gửi):",
    "Account:": "Tài khoản:",
    "Send": "Gửi",
    "Dismiss": "Bỏ qua",
    "No account": "Chưa chọn tài khoản",
    "Pick or type an account first.": "Chọn hoặc nhập tài khoản trước.",
    "GiaoIT Bridge": "Cầu nối GiaoIT",
}
