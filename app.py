from flask import Flask, render_template, redirect, url_for, request, flash, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
from flask_cors import CORS
from flask_socketio import SocketIO, send
import os

# Khởi tạo Flask
app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, async_mode='eventlet')

# Cấu hình
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Khởi tạo extensions
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"


# Model User
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    avatar = db.Column(db.String(200), nullable=True, default="default.jpg")
    role = db.Column(db.String(50), nullable=False, default="user")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


# Decorator admin
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != "admin":
            abort(403)
        return f(*args, **kwargs)

    return decorated_function


# User loader
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# Routes
@app.route('/')
def home():
    return render_template('home.html')


@app.route('/settings')
@login_required
def settings():
    return render_template('settings.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        if User.query.filter_by(username=username).first():
            flash("Username exists!", "danger")
            return redirect(url_for('register'))

        user = User(username=username, email=email, role="user")
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash("Registered!", "success")
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('home'))

        flash("Invalid credentials!", "danger")
    return render_template('login.html')


@app.route('/update-profile', methods=['GET', 'POST'])
@login_required
def update_profile():
    if request.method == 'POST':
        current_user.username = request.form.get('username', current_user.username)

        if password := request.form.get('password'):
            current_user.set_password(password)

        if avatar := request.files.get('avatar'):
            filename = secure_filename(avatar.filename)
            avatar.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            current_user.avatar = filename

        db.session.commit()
        flash("Profile updated!", "success")
        return redirect(url_for('settings'))

    return render_template('settings.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))


# Error handler
@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    socketio.run(app, debug=True)