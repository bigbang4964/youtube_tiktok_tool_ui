# youtube_tiktok_tool_ui
Tổng quan chức năng
  Nhập từ khóa → tìm video YouTube (độ dài 1–15 phút, lượt xem cao)
  Hiển thị danh sách kết quả trong Combobox để chọn video
  Xem preview video trước khi chỉnh sửa/đăng
  Chỉnh sửa caption thủ công
  Cài đặt nâng cao: font, kích thước, màu chữ, watermark (logo/text), nhạc nền (mp3), intro/outro (video)
  Tải video → chỉnh sửa (thêm watermark, overlay caption, ghép nhạc/intro/outro) → đăng lên TikTok (tự động hóa / bán tự động)
Kiến trúc & thư viện đề xuất
  GUI: tkinter + ttk (Combobox, file dialogs, simple preview controls)
  Tìm kiếm YouTube:
  Tùy chọn A (khuyến nghị): YouTube Data API v3 (google-api-python-client) — ổn định, chính thức — cần API key.
  Tùy chọn B: yt-dlp/ytsearch: để tìm và lấy metadata (không cần API key).
  Tải video: yt-dlp hoặc pytube (khuyến nghị yt-dlp vì ổn định).
  Xử lý video/audio: moviepy (dễ dùng để overlay text/logo, ghép audio, concat video).
  Phát preview:
  Mở URL bằng webbrowser.open() (nhanh, đơn giản) hoặc
  Tải video tạm thời rồi play bằng python-vlc hoặc subprocess gọi ffplay nếu bạn cần preview offline.
  Đăng lên TikTok:
  Không có API upload chính thức public cho mọi tài khoản — 2 cách thường dùng:
  Selenium + mô phỏng trình duyệt (mobile emulation) để upload qua web.tiktok.com — ổn định tuỳ thời điểm, cẩn trọng với bảo mật & 2FA.
  Thiết bị thực (adb): kết nối emulated Android và điều khiển app TikTok (phức tạp).
  Lưu ý: việc tự động hoá upload có thể vi phạm điều khoản dịch vụ—hãy kiểm tra và dùng tài khoản thử nghiệm.
Luồng xử lý (đề xuất)
  Người dùng nhập từ khóa → app gọi YouTube API / yt-dlp để tìm top N kết quả (lọc 1–15 phút, sort by viewCount).
  Kết quả hiển thị trong Combobox (title + duration + view).
  Chọn 1 video → show thumbnail + bấm Preview mở YouTube hoặc play offline.
  Người dùng chỉnh caption & cấu hình (font, size, color, watermark, music, intro/outro).
  Bấm Download & Edit → yt-dlp tải video về → moviepy thực hiện chỉnh sửa → lưu file đầu ra.
  Sau khi hoàn tất, người dùng bấm Upload to TikTok (mở modal cho credentials) → thực hiện upload bằng Selenium (hoặc export file để người dùng upload thủ công).
Cài đặt môi trường (pip)
  pip install yt-dlp moviepy google-api-python-client python-vlc selenium pillow
  # Nếu cần: pip install pytube
  Ghi chú: moviepy cần ffmpeg cài trên hệ thống (https://ffmpeg.org). yt-dlp cũng cần ffmpeg để merge audio/video.
Tải về và chạy:
  python youtube_to_ticktok.py
  
