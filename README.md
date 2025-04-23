# SpeakEasy - Ứng dụng Học Ngôn ngữ

Một ứng dụng học ngôn ngữ toàn diện dựa trên Flask, hỗ trợ nhận diện giọng nói, dịch văn bản/tập tin, giao tiếp thời gian thực và các bài học có cấu trúc. Được xây dựng với Python 3.13, Flask, SQLite và SocketIO.

---

## Mục lục

1. [Tính năng](#tính-năng)
2. [Công nghệ sử dụng](#công-nghệ-sử-dụng)
3. [Yêu cầu hệ thống](#yêu-cầu-hệ-thống)
4. [Cài đặt](#cài-đặt)
5. [Cấu hình](#cấu-hình)
6. [Chạy ứng dụng](#chạy-ứng-dụng)
7. [Cấu trúc dự án](#cấu-trúc-dự-án)
8. [Các mô hình dữ liệu (Models)](#các-mô-hình-dữ-liệu-models)
9. [Blueprints & Endpoints](#blueprints--endpoints)
10. [Quản lý cơ sở dữ liệu](#quản-lý-cơ-sở-dữ-liệu)
11. [Khắc phục sự cố](#khắc-phục-sự-cố)
12. [Kế hoạch phát triển](#kế-hoạch-phát-triển)

---

## Tính năng

- **Quản lý người dùng**: Đăng ký, đăng nhập/đăng xuất và tùy chỉnh hồ sơ cá nhân
- **Phân quyền**: Phân biệt vai trò admin và user
- **Nhận diện giọng nói**: Đánh giá phát âm và cung cấp phản hồi chi tiết
- **Dịch thuật**: Dịch văn bản và tập tin với bộ nhớ đệm thông minh
- **Cộng đồng chat**: Hỗ trợ phòng chat công khai/riêng tư và diễn đàn thảo luận
- **Học có cấu trúc**: Hệ thống cấp độ, bài học và từ vựng theo tiêu chuẩn CEFR
- **Đánh giá trình độ**: Xác định trình độ CEFR (A1-C1) dựa trên bài kiểm tra phát âm

---

## Công nghệ sử dụng

- **Backend**: Python 3.13, Flask, SQLAlchemy, Flask-Migrate
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5
- **Cơ sở dữ liệu**: SQLite
- **Thời gian thực**: Flask-SocketIO, Eventlet
- **Xác thực**: Flask-Login
- **API tích hợp**:
  - Google Speech Recognition API (nhận diện giọng nói)
  - Google Translate API (thông qua deep-translator)
- **Thư viện hỗ trợ**:
  - SpeechRecognition (xử lý âm thanh)
  - PyDub (phân tích âm thanh)
  - CacheLib (bộ nhớ đệm)

---

## Yêu cầu hệ thống

- Python 3.13+
- Môi trường hỗ trợ ghi âm (microphone)
- Kết nối Internet (để sử dụng các API nhận dạng giọng nói và dịch thuật)
- Git (để clone repository)

---

## Cài đặt

1. **Clone repository**
   ```bash
   git clone <repository_url>
   cd SpeakEasy
   ```

2. **Tạo và kích hoạt môi trường ảo**
   ```bash
   python3.13 -m venv .venv
   source .venv/bin/activate    # Linux/macOS
   .\.venv\Scripts\activate     # Windows
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
   
   Hoặc sử dụng phương pháp tạo trực tiếp:
   ```bash
   python -c "from app import app; from models.models import db; app.app_context().push(); db.create_all()"
   ```

---

## Cấu hình

Các thiết lập có thể tùy chỉnh trong `app.py`:

```python
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///learning_app.db'
app.config['SECRET_KEY'] = 'your_secret_key'  # Thay đổi trong môi trường production
app.config['UPLOAD_FOLDER'] = 'static/uploads'
```

Đảm bảo các thư mục uploads tồn tại và có quyền ghi.

---

## Chạy ứng dụng

Chạy với SocketIO và Eventlet (khuyến nghị):

```bash
python app.py
```

Ứng dụng sẽ chạy tại `http://localhost:5001`.

---

## Cấu trúc dự án

```
Learning-App/
├─ app.py # Entry point và cấu hình ứng dụng
├─ requirements.txt # Danh sách phụ thuộc Python
├─ learning_app.db # Cơ sở dữ liệu SQLite
├─ modules/ # Các blueprint chức năng
│ ├─ speech.py # Nhận diện giọng nói và đánh giá phát âm
│ ├─ translate.py # Dịch văn bản và tập tin
│ ├─ chat.py # Chat thời gian thực và diễn đàn
│ └─ tutorials.py # Quản lý bài học và tiến độ
├─ models/ # Định nghĩa SQLAlchemy models
│ └─ models.py # Tất cả mô hình dữ liệu
├─ templates/ # Giao diện người dùng
│ ├─ base.html # Template cơ sở
│ ├─ home.html # Trang chủ
│ ├─ settings.html # Cài đặt người dùng
│ ├─ speech_to_text.html # Đánh giá phát âm
│ ├─ translate_text.html # Dịch thuật
│ ├─ chatting.html # Chat và diễn đàn
│ ├─ tutorials.html # Danh sách bài học
│ └─ ... # Các template khác
└─ static/ # Tài nguyên tĩnh (CSS, JS, hình ảnh)
├─ styles.css # Stylesheet chính
├─ uploads/ # Tập tin người dùng upload
└─ img/ # Hình ảnh và biểu tượng
```

---

## Các mô hình dữ liệu (Models)

### Người dùng và Tiến độ
- **User**: Thông tin người dùng, xác thực và phân quyền
- **UserProgress**: Theo dõi tiến độ học tập của người dùng

### Hệ thống học tập
- **Level**: Cấp độ theo tiêu chuẩn CEFR (A1, A2, B1, B2, C1)
- **Lesson**: Bài học với nội dung, mô tả theo cấp độ
- **Vocabulary**: Từ vựng, định nghĩa, ví dụ và cấp độ
- **Test**: Bài kiểm tra phát âm và viết
- **SampleSentence**: Câu mẫu và file audio chuẩn
- **SpeechTest**: Kết quả đánh giá phát âm

### Cộng đồng và Chat
- **ChatRoom**: Phòng chat công khai và riêng tư
- **Message**: Tin nhắn trong phòng chat
- **RoomParticipant**: Thành viên của phòng chat
- **StatusPost**: Bài đăng trên diễn đàn
- **PostComment**: Bình luận cho bài đăng

---

## Blueprints & Endpoints

### Trang chính (`app.py`)
- `GET /` — Trang chủ
- `GET /settings` — Cài đặt tài khoản
- `POST /register` — Đăng ký tài khoản mới
- `POST /login` — Đăng nhập
- `GET /logout` — Đăng xuất
- `POST /update-profile` — Cập nhật thông tin cá nhân
- `GET /admin` — Bảng điều khiển admin (yêu cầu quyền admin)

### Nhận diện giọng nói (`modules/speech.py`)
- `GET /speech_to_text` — Hiển thị trang đánh giá phát âm
- `POST /speech_to_text` — Xử lý âm thanh và đánh giá phát âm

### Dịch thuật (`modules/translate.py`)
- `GET /translate` — Hiển thị trang dịch văn bản
- `POST /translate` — Dịch văn bản (API JSON)
- `POST /translate/file` — Dịch nội dung tập tin

### Chat và Diễn đàn (`modules/chat.py`)
- `GET /chat` — Hiển thị trang chat và diễn đàn
- `POST /chat/create-room` — Tạo phòng chat mới
- `GET /chat/room/<room_id>` — Xem phòng chat cụ thể
- `GET /chat/join-room/<room_id>` — Tham gia phòng chat
- `POST /chat/new-post` — Tạo bài đăng mới (giới hạn 1/ngày)
- `POST /chat/post/<post_id>/comment` — Bình luận bài đăng (giới hạn 10/ngày)

### Bài học (`modules/tutorials.py`)
- `GET /tutorials/tutorials` — Danh sách cấp độ và bài học
- `GET /tutorials/level/<level_name>` — Xem bài học theo cấp độ
- `GET /tutorials/lesson/<lesson_id>` — Nội dung bài học cụ thể
- `POST /tutorials/complete/<lesson_id>` — Đánh dấu hoàn thành bài học
- `GET /tutorials/vocabulary/<level_name>` — Xem từ vựng theo cấp độ

---

## Quản lý cơ sở dữ liệu

### Khởi tạo với Flask-Migrate
```bash
# Lần đầu tiên
flask db init
flask db migrate -m "Initial migration"
flask db upgrade

# Cập nhật schema
flask db migrate -m "Thêm tính năng XYZ"
flask db upgrade
```

### Khởi tạo trực tiếp
Ứng dụng tự động tạo bảng và dữ liệu mẫu khi chạy:
```python
with app.app_context():
    db.create_all()
    init_sample_data()  # Tạo dữ liệu mẫu
```

---

## Khắc phục sự cố

### Vấn đề với nhận diện giọng nói
- Đảm bảo microphone được cấu hình đúng
- Kiểm tra kết nối mạng (cần để truy cập Google Speech API)
- Thông báo lỗi ALSA trên Linux là bình thường và không ảnh hưởng đến hoạt động

### Lỗi database
Nếu gặp lỗi "no such table", thử:
```bash
flask db stamp head  # Đánh dấu migration hiện tại
flask db migrate     # Tạo migration mới
flask db upgrade     # Áp dụng migration
```

Hoặc xóa và tạo lại:
```bash
rm -f learning_app.db
python app.py  # Tự động tạo lại DB và dữ liệu mẫu
```

---

## Kế hoạch phát triển

### Tính năng sắp tới
- Hỗ trợ nhiều ngôn ngữ (hiện tại tập trung vào tiếng Anh)
- API nhận dạng giọng nói nâng cao với đánh giá chi tiết hơn
- Ứng dụng di động (React Native)
- Tích hợp AI để cá nhân hóa lộ trình học tập

### Cải tiến kỹ thuật
- Tối ưu hóa hiệu suất database với Redis cache
- Tách frontend thành SPA độc lập với backend REST API
- Triển khai CI/CD với GitHub Actions
- Containerization với Docker

---

© 2025 SpeakEasy. Mọi quyền được bảo lưu.



