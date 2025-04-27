# Ứng dụng học tiếng Anh

Ứng dụng web học tiếng Anh với nhiều tính năng tương tác.

## Tính năng

- Hệ thống lộ trình học tập theo cấp độ
- Bài học có nội dung trực quan
- Bài tập phát âm với đánh giá tự động
- Tính năng trò chuyện trực tuyến
- Công cụ dịch văn bản
- Quản lý người dùng và nội dung

## Cài đặt

### Yêu cầu

- Python 3.9+
- pip
- SQLite hoặc PostgreSQL
- Các thư viện âm thanh (cho chức năng phát âm)

### Thiết lập

1. Clone repository:
```bash
git clone <repository-url>
cd language-learning-app
```

2. Tạo môi trường ảo và kích hoạt:
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# hoặc
.venv\Scripts\activate  # Windows
```

3. Cài đặt thư viện:
```bash
pip install -r requirements.txt
```

4. Khởi tạo cơ sở dữ liệu:
```bash
flask init-db
flask seed-db  # Tạo dữ liệu mẫu
```

5. Chạy ứng dụng:
```bash
flask run
# hoặc
python wsgi.py
```

## Quản lý ứng dụng

### Tạo tài khoản admin

```bash
flask create-admin <username> <email> <password>
```

### Xem danh sách người dùng

```bash
flask list-users
```

## Cấu trúc dự án

```
language_learning_app/
├── app/                    # Mã nguồn chính
│   ├── models/             # Mô hình dữ liệu
│   ├── admin/              # Module quản trị
│   ├── auth/               # Module xác thực
│   ├── tutorials/          # Module học tập
│   ├── speech/             # Module phát âm
│   ├── chat/               # Module trò chuyện
│   ├── static/             # Tài nguyên tĩnh
│   └── templates/          # Giao diện người dùng
├── migrations/             # Tập tin di chuyển DB
├── .flaskenv               # Biến môi trường Flask
├── wsgi.py                 # Entry point
└── requirements.txt        # Thư viện phụ thuộc
```

## Phát triển

Dự án sử dụng mô hình Factory Pattern và Blueprint để tổ chức mã nguồn theo cách mô-đun hóa. Điều này cho phép mở rộng và bảo trì dễ dàng hơn.

## Tác giả

- [Tên tác giả]

## Giấy phép

[Loại giấy phép]



