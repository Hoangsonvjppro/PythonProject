from flask import Flask, render_template, redirect, url_for, request, flash, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
from speech import speech_bp
from translate import translate_bp
from flask_cors import CORS
import os


# init Flask
app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config['SECRET_KEY'] = 'your_secret_key'

app.register_blueprint(speech_bp)
app.register_blueprint(translate_bp)
@app.errorhandler(500)
def handle_internal_error(error):
    return jsonify({'success': False, 'error': 'Internal Server Error'}), 500

# init database
db = SQLAlchemy(app)

#Flask-Login configuration
login_manager = LoginManager(app)
login_manager.login_view = "login"


#model User
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    avatar = db.Column(db.String(200), nullable=True, default="default.jpg")  # Thêm ảnh đại diện
    role = db.Column(db.String(50), nullable=False, default="user")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.role == "admin":
            abort(403) #return 403 error Forbidden if !=admin
        return f(*args, **kwargs)
    return decorated_function

# Load user cho Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def home():
    return render_template('home.html', current_user=current_user)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']  # Thêm email
        password = request.form['password']
        role = request.form['role']

        if User.query.filter_by(username=username).first():
            flash("Username already exists!", "danger")
            return redirect(url_for('register'))

        if User.query.filter_by(email=email).first():  # Kiểm tra email trùng
            flash("Email already registered!", "danger")
            return redirect(url_for('register'))

        new_user = User(username=username, email=email, role=role)  # Lưu email
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        flash("Registration successful! You can now login.", "success")
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            flash("Login successful!", "success")
            return redirect(url_for('home'))
        else:
            flash("Invalid username or password!", "danger")
            return redirect(url_for('login'))

    return render_template('login.html')

UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/update-profile', methods=['GET', 'POST'])
@login_required
def update_profile():
    if request.method == 'POST':
        new_username = request.form['username']
        new_password = request.form['password']
        avatar = request.files['avatar']

        if new_username:
            current_user.username = new_username

        if new_password:
            current_user.set_password(new_password)

        if avatar:
            filename = secure_filename(avatar.filename)
            avatar.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            current_user.avatar = filename

        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('update_profile'))

    return render_template('update_profile.html')

@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    users = User.query.all()
    return render_template('admin.html', users=users)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.debug = True
    with app.app_context():
        db.create_all()
    app.run()
