import eventlet
eventlet.monkey_patch()
from app import create_app
from app.extensions import socketio, socketio_available

app = create_app()

if __name__ == '__main__':
    url = "http://127.0.0.1:5000"
    if socketio_available:
        try:
            print("🚀 Starting application with SocketIO (eventlet)...")
            print(f"✅ Ứng dụng đang chạy tại: {url}")
            socketio.run(app, debug=app.config['DEBUG'], host='0.0.0.0', port=5000)
        except Exception as e:
            print(f"❌ Lỗi SocketIO: {e}")
            print("👉 Chuyển sang server Flask thường")
            print(f"✅ Ứng dụng đang chạy tại: {url}")
            app.run(debug=app.config['DEBUG'], host='0.0.0.0', port=5000)
    else:
        print("⚠️  SocketIO không khả dụng. Khởi chạy Flask server thường...")
        print(f"✅ Ứng dụng đang chạy tại: {url}")
        app.run(debug=app.config['DEBUG'], host='0.0.0.0', port=5000)
