# Ứng Dụng Học Tiếng Anh

Ứng dụng web học tiếng Anh đa chức năng với khả năng luyện phát âm, chat, dịch và các bài học theo cấp độ.

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
└── recreate_db.py            # Script tạo lại database
```

## Yêu cầu

- Python 3.8+
- Pip
- Các thư viện được liệt kê trong requirements.txt

## Cài đặt

1. Tạo môi trường ảo:

```bash
python -m venv venv
```

2. Kích hoạt môi trường ảo:

- Windows:
```bash
venv\Scripts\activate
```

- Linux/MacOS:
```bash
source venv/bin/activate
```

3. Cài đặt các dependency:

```bash
pip install -r requirements.txt
```

4. Thiết lập biến môi trường Flask:

```bash
# Nội dung file .flaskenv
FLASK_APP=wsgi.py
FLASK_ENV=development
FLASK_DEBUG=1
```

## Khởi tạo Database

1. Tạo database và thực hiện migrations:

```bash
flask db upgrade
```

2. Khởi tạo dữ liệu mẫu:

```bash
flask init-db
```

## Chạy ứng dụng

1. Chạy ứng dụng trong môi trường phát triển:

```bash
flask run
```

2. Nếu muốn sử dụng Socket.IO (cho tính năng chat và phát âm theo thời gian thực):

```bash
python wsgi.py
```

Ứng dụng sẽ chạy tại `http://127.0.0.1:5000/`

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

4. **Dịch thuật**
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

## Tác giả

- [Tên tác giả]

## Giấy phép

[Loại giấy phép]



