from app import create_app
from app.extensions import socketio, socketio_available

# Tạo ứng dụng
app = create_app()

if __name__ == '__main__':
    if socketio_available:
        try:
            print("Starting application with SocketIO...")
            socketio.run(app, debug=app.config['DEBUG'], host='0.0.0.0', port=5000)
        except Exception as e:
            print(f"Error starting SocketIO: {e}")
            print("Falling back to regular Flask server")
            app.run(debug=app.config['DEBUG'], host='0.0.0.0', port=5000)
    else:
        print("SocketIO is not available. Starting regular Flask server...")
        app.run(debug=app.config['DEBUG'], host='0.0.0.0', port=5000)
