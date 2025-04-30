# Ứng Dụng Học Tiếng Anh

Ứng dụng web học tiếng Anh đa chức năng với khả năng luyện phát âm, chat, dịch, chatbot AI và các bài học theo cấp độ.

## Cấu trúc dự án

```
PythonProject/
├── app/                      # Thư mục chính của ứng dụng Flask
│   ├── __init__.py           # Khởi tạo ứng dụng Flask
│   ├── config.py             # Cấu hình ứng dụng
│   ├── commands.py           # CLI commands
│   ├── extensions.py         # Các tiện ích mở rộng (db, login, etc)
│   ├── models/               # Models database
│   ├── chat/                 # Module chat
│   ├── chatbot/              # Module chatbot AI
│   ├── speech/               # Module phát âm
│   ├── translate/            # Module dịch thuật
│   ├── tutorials/            # Module bài học
│   ├── templates/            # Templates HTML
│   └── static/               # Tài nguyên tĩnh (CSS, JS, images)
├── migrations/               # Migrations database
├── instance/                 # Thư mục instance (database)
├── requirements.txt          # Các dependency
├── .flaskenv                 # Biến môi trường Flask
├── app.py                    # Entry point đơn giản
├── wsgi.py                   # Entry point WSGI cho production
├── recreate_db.py            # Script tạo lại database
└── train_chatbot.py          # Script huấn luyện chatbot
```

## Yêu cầu

- Python 3.8+
- Pip
- Các thư viện được liệt kê trong requirements.txt

## Hướng dẫn cài đặt

### Yêu cầu
- Python 3.8 hoặc mới hơn
- pip (trình quản lý gói Python)

### Bước 1: Clone dự án
```bash
git clone [url-của-repository]
cd PythonProject
```

### Bước 2: Tạo môi trường ảo
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS/Linux
python3 -m venv .venv
source .venv/bin/activate
```

### Bước 3: Cài đặt các gói phụ thuộc
```bash
pip install -r requirements.txt
```

### Bước 4: Thiết lập cơ sở dữ liệu
```bash
flask db upgrade
# Hoặc sử dụng script để tạo lại cơ sở dữ liệu
python recreate_db.py
```

### Bước 5: Huấn luyện chatbot (nếu cần)
```bash
python train_chatbot.py
```

### Bước 6: Chạy ứng dụng
```bash
# Windows
flask run
# hoặc
python -m flask run

# macOS/Linux
flask run
# hoặc
python3 -m flask run
```

Ứng dụng sẽ khởi chạy tại địa chỉ http://127.0.0.1:5000/

## Tính năng chính

1. **Học theo cấp độ (A1, A2, B1, B2, C1)**
   - Bài học theo cấp độ
   - Từ vựng theo cấp độ

2. **Luyện phát âm**
   - Phân tích độ chính xác
   - Phản hồi về phát âm

3. **Chat cộng đồng**
   - Tạo phòng chat
   - Chia sẻ kinh nghiệm học tập

4. **Chatbot AI**
   - Trả lời câu hỏi liên quan đến học tiếng Anh
   - Huấn luyện chatbot bằng cách gửi tin nhắn theo cú pháp `Training: câu hỏi => câu trả lời`

5. **Dịch thuật**
   - Dịch văn bản
   - Dịch câu từ nhiều ngôn ngữ

## Các lệnh hữu ích

- Tạo tài khoản admin:
```bash
flask create-admin <username> <email> <password>
```

- Liệt kê tất cả người dùng:
```bash
flask list-users
```

- Tạo lại database nếu gặp vấn đề:
```bash
python recreate_db.py
```

## Lưu ý

1. Đảm bảo các thư mục `instance` và `static/uploads` có quyền ghi.
2. Tất cả tệp âm thanh mẫu nên được đặt trong thư mục `static/correct_audios/`.
3. Khi sử dụng Socket.IO, luôn chạy ứng dụng thông qua `python wsgi.py` để đảm bảo hoạt động đúng.
4. Lưu ý đặt SECRET_KEY mạnh hơn trong môi trường sản xuất.

## Troubleshooting

1. Nếu gặp lỗi khi tạo migration, hãy xóa thư mục migrations và thực hiện lại:
```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

2. Nếu database bị lỗi, hãy sử dụng script recreate_db.py:
```bash
python recreate_db.py
flask db upgrade
flask init-db
```

3. Nếu thiếu thư viện, hãy cài đặt thêm:
```bash
pip install eventlet gunicorn
```

4. Nếu chatbot không hoạt động, hãy đảm bảo đã chạy:
```bash
flask init-chatbot
```
hoặc
```bash
python train_chatbot.py
```

### Khắc phục sự cố SocketIO và SSL
Nếu gặp lỗi liên quan đến `ssl.wrap_socket` hoặc các lỗi SSL khác:
```bash
# Ứng dụng đã được cấu hình để sử dụng chế độ threading thay vì eventlet/gevent
# để tránh lỗi SSL trên các phiên bản Python mới
# Bạn không cần thực hiện thêm bất kỳ cấu hình nào để khắc phục lỗi này
```

Nếu cần cài đặt Python 3.9 hoặc 3.10 để tương thích tốt hơn với tất cả các gói phụ thuộc.

## Tác giả

- [Tên tác giả]

## Giấy phép

[Loại giấy phép]

## Tương thích đa nền tảng

Ứng dụng này đã được thiết kế để hoạt động trên nhiều nền tảng khác nhau (Windows, macOS và Linux). Tuy nhiên, có một số lưu ý khi chạy trên các nền tảng khác nhau:

### Windows
- Cài đặt PyAudio có thể yêu cầu Microsoft Visual C++ Build Tools. Nếu gặp lỗi khi cài đặt PyAudio, bạn có thể:
  - Cài đặt Microsoft Visual C++ Build Tools từ https://visualstudio.microsoft.com/visual-cpp-build-tools/
  - Hoặc sử dụng wheel có sẵn: `pip install https://github.com/jleb/pyaudio/releases/download/0.2.11/PyAudio-0.2.11-cp310-cp310-win_amd64.whl` (thay đổi phiên bản Python cho phù hợp)
  - Hoặc bỏ qua tính năng nhận diện giọng nói (ứng dụng vẫn hoạt động nhưng không có chức năng này)

### macOS
- Cài đặt PortAudio trước khi cài đặt PyAudio:
  ```bash
  brew install portaudio
  pip install pyaudio
  ```

### Linux
- Cài đặt các thư viện phát triển cần thiết:
  ```bash
  # Ubuntu/Debian
  sudo apt-get install python3-dev portaudio19-dev
  pip install pyaudio
  
  # Fedora
  sudo dnf install python3-devel portaudio-devel
  pip install pyaudio
  ```

### Khắc phục sự cố SocketIO
Nếu gặp lỗi "Invalid async_mode specified" khi chạy ứng dụng, hãy đảm bảo bạn đã cài đặt các gói hỗ trợ:
```bash
pip install eventlet gevent
```

Ứng dụng sẽ cố gắng sử dụng SocketIO nếu có thể, nhưng sẽ tự động chuyển sang chế độ Flask thông thường nếu có lỗi.

## Chạy ứng dụng không cần SocketIO

Nếu bạn gặp vấn đề với SocketIO, ứng dụng đã được cấu hình để tự động chuyển sang chế độ Flask thông thường:

```bash
# Cách 1: Sử dụng app.py (chỉ Flask, không có SocketIO)
python app.py

# Cách 2: Sử dụng wsgi.py (tự động phát hiện và xử lý SocketIO nếu có thể)
python wsgi.py
```

Ứng dụng sẽ tự động phát hiện xem SocketIO có sẵn sàng không và chọn phương thức phù hợp.

### Các tính năng bị giới hạn khi không có SocketIO
Khi chạy ứng dụng mà không có SocketIO, một số tính năng sẽ hoạt động theo chế độ giới hạn:

- **Chatbot**: Sẽ sử dụng giao tiếp HTTP thông thường thay vì giao tiếp thời gian thực
- **Chat cộng đồng**: Có thể không hoạt động hoặc hoạt động với tính năng hạn chế
- **Nhận diện giọng nói**: Vẫn hoạt động bình thường



