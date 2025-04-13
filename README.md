# Ứng dụng Học Ngôn ngữ

Một ứng dụng học ngôn ngữ dựa trên Flask, hỗ trợ nhận diện giọng nói, dịch văn bản/tập tin, chat thời gian thực và các bài học có cấu trúc. Xây dựng với Python 3.13, Flask, SQLite và SocketIO.

---

## Mục lục

1. [Tính năng](#tính-năng)
2. [Công nghệ sử dụng](#công-nghệ-sử-dụng)
3. [Yêu cầu trước khi cài đặt](#yêu-cầu-trước-khi-cài-đặt)
4. [Cài đặt](#cài-đặt)
5. [Cấu hình](#cấu-hình)
6. [Chạy ứng dụng](#chạy-ứng-dụng)
7. [Cấu trúc dự án](#cấu-trúc-dự-án)
8. [Các mô hình dữ liệu (Models)](#các-mô-hình-dữ-liệu-models)
9. [Blueprints & Endpoints](#blueprints--endpoints)
10. [Cơ sở dữ liệu & Migrations](#cơ-sở-dữ-liệu--migrations)
11. [Đóng góp](#đóng-góp)
12. [Các bước tiếp theo](#các-bước-tiếp-theo)

---

## Tính năng

- Đăng ký, đăng nhập/đăng xuất và quản lý hồ sơ người dùng
- Phân quyền (admin và user)
- Nhận diện giọng nói và đánh giá phát âm
- Dịch văn bản và tập tin qua Google Translate API
- Chat thời gian thực với SocketIO
- Bài học có cấu trúc: cấp độ, bài học, từ vựng, bài kiểm tra
- Khởi tạo dữ liệu mẫu tự động

---

## Công nghệ sử dụng

- **Ngôn ngữ:** Python 3.13
- **Web Framework:** Flask
- **Cơ sở dữ liệu:** SQLite (qua SQLAlchemy)
- **Thời gian thực:** Flask-SocketIO + eventlet
- **Xác thực:** Flask-Login
- **CORS:** Flask-CORS
- **Dịch thuật:** deep-translator (GoogleTranslator)
- **Nhận diện giọng nói:** SpeechRecognition + Google Speech API
- **Template:** Jinja2

---

## Yêu cầu trước khi cài đặt

- Python 3.13
- Git
- Công cụ tạo môi trường ảo (venv, virtualenv)

---

## Cài đặt

1. **Clone repository**
   ```bash
   git clone <repository_url>
   cd Learning-App
   ```

2. **Tạo và kích hoạt môi trường ảo**
   ```bash
   python3.13 -m venv .venv
   source .venv/bin/activate    # Linux/macOS
   .\.venv\\Scripts\\activate  # Windows
   ```

3. **Cài đặt các gói phụ thuộc**
   ```bash
   pip install -r requirements.txt
   ```

4. **Khởi tạo cơ sở dữ liệu**
   ```bash
   flask db init
   flask db migrate -m "Initial migration"
   flask db upgrade
   ```

---

## Cấu hình

1. **Biến môi trường**
   - Tạo file `.env` ở thư mục gốc:
     ```dotenv
     FLASK_APP=app.py
     FLASK_ENV=development
     SECRET_KEY=your_secret_key
     DATABASE_URL=sqlite:///instance/learning_app.db
     ```

2. **Thư mục lưu tập tin upload**
   - Mặc định: `static/uploads`
   - Đảm bảo thư mục tồn tại và có quyền ghi.

---

## Chạy ứng dụng

```bash
flask run --port=5001
```

Hoặc chạy trực tiếp với SocketIO:

```bash
python app.py
```

Truy cập ứng dụng tại `http://localhost:5001`.

---

## Cấu trúc dự án

```
Learning-App/
├─ .gitignore           # Loại trừ .venv/, instance/*.db, __pycache__/, .idea/
├─ .env                 # Biến môi trường
├─ app.py               # Entry point và app factory
├─ requirements.txt     # Danh sách phụ thuộc Python
├─ instance/
│  └─ learning_app.db   # Cơ sở dữ liệu SQLite
├─ modules/             # Các blueprint chức năng
│  ├─ speech.py
│  ├─ translate.py
│  ├─ chat.py
│  └─ tutorials.py
├─ models/              # Định nghĩa SQLAlchemy models
│  └─ models.py
├─ templates/           # Jinja2 templates
│  ├─ home.html
│  ├─ settings.html
│  ├─ speech_to_text.html
│  ├─ translate_text.html
│  ├─ chatting.html
│  ├─ tutorials.html
│  ├─ lesson.html
│  └─ admin.html
├─ static/              # Static assets (CSS, JS, images)
│  └─ uploads/          # Tập tin người dùng upload
└─ tests/               # (Tùy chọn) Unit tests
```

---

## Các mô hình dữ liệu (Models)

- **User**: Quản lý tài khoản, hồ sơ, phân quyền
- **Level**: Các cấp độ học (A1, A2, B1, B2, C1)
- **Lesson**: Tiêu đề, mô tả, nội dung theo cấp độ
- **UserProgress**: Theo dõi bài học đã hoàn thành
- **Vocabulary**: Từ vựng, định nghĩa, ví dụ, cấp độ
- **Test**: Bài kiểm tra phát âm hoặc viết theo cấp độ
- **SampleSentence**: Câu mẫu kèm audio đúng
- **SpeechTest**: Theo dõi kết quả đánh giá phát âm

---

## Blueprints & Endpoints

### Speech (`modules/speech.py`)
- `GET /speech_to_text` — Hiển thị trang nhận diện giọng nói
- `POST /speech_to_text` — Ghi âm và đánh giá phát âm

### Translate (`modules/translate.py`)
- `GET /translate` — Hiển thị trang dịch văn bản
- `POST /translate` — Dịch văn bản JSON
- `POST /translate/file` — Upload và dịch nội dung tập tin

### Chat (`modules/chat.py`)
- `GET /chat` — Hiển thị trang chat
- Sự kiện SocketIO: `connect`, `disconnect`, `send_message`, `join`, `leave`, `update_username`

### Tutorials (`modules/tutorials.py`)
- `GET /tutorials` — Liệt kê cấp độ và tiến độ học của người dùng
- `GET /tutorials/start/<level_name>` — Bắt đầu cấp độ
- `GET /tutorials/lesson/<lesson_id>` — Xem nội dung bài học
- `POST /tutorials/complete/<lesson_id>` — Đánh dấu hoàn thành bài học

---

## Cơ sở dữ liệu & Migrations

Sử dụng Flask-Migrate để quản lý schema:

```bash
flask db init
flask db migrate -m "Thêm tính năng mới"
flask db upgrade
```

---

## Đóng góp

1. Fork repository
2. Tạo nhánh tính năng: `git checkout -b feature/TenTinhNang`
3. Commit thay đổi: `git commit -m "Thêm tính năng ..."`
4. Push lên nhánh của bạn: `git push origin feature/TenTinhNang`
5. Tạo Pull Request

Vui lòng tuân thủ PEP8 và thêm unit tests cho tính năng mới.

---

## Các bước tiếp theo

- Tổ chức lại code thành package `src/`
- Viết unit tests đầy đủ trong `tests/`
- Thiết lập CI/CD (GitHub Actions)
- Cải thiện xử lý lỗi và logging
- Triển khai lên môi trường production (Heroku, AWS, v.v.)

---

&mdash; **Chúc bạn học vui vẻ!** 🎓


