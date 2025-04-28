from flask import render_template, Blueprint, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.main import bp
from app.extensions import db  # Sửa dòng này
from app.models.user import User  # Sửa dòng này
from werkzeug.utils import secure_filename
import os
from flask import current_app
from app.main.forms import ContactForm

@bp.route('/')
def home():
    return render_template('main/home.html', current_user=current_user)

@bp.route('/settings')
def settings():
    return render_template('main/settings.html', current_user=current_user)

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        role = request.form.get('role', 'user')

        if User.query.filter_by(username=username).first():
            flash("Tên người dùng đã tồn tại!", "danger")
            return redirect(url_for('main.settings'))
        if User.query.filter_by(email=email).first():
            flash("Email đã được đăng ký!", "danger")
            return redirect(url_for('main.settings'))

        new_user = User(username=username, email=email, role=role)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        flash("Đăng ký thành công! Bạn có thể đăng nhập.", "success")
        return redirect(url_for('main.settings'))
    return redirect(url_for('main.settings'))

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            flash("Đăng nhập thành công!", "success")
            return redirect(url_for('main.home'))
        else:
            flash("Tên người dùng hoặc mật khẩu không đúng!", "danger")
            return redirect(url_for('main.settings'))
    return redirect(url_for('main.settings'))

@bp.route('/update-profile', methods=['GET', 'POST'])
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
            avatar.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
            current_user.avatar = filename

        db.session.commit()
        flash('Cập nhật hồ sơ thành công!', 'success')
        return redirect(url_for('main.settings'))
    return redirect(url_for('main.settings'))

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Bạn đã đăng xuất.", "info")
    return redirect(url_for('main.home'))

@bp.route('/about')
def about():
    """Trang giới thiệu"""
    return render_template('main/about.html', title='Giới thiệu')
    
@bp.route('/contact', methods=['GET', 'POST'])
def contact():
    """Trang liên hệ"""
    form = ContactForm()
    if form.validate_on_submit():
        # Xử lý dữ liệu form - có thể gửi email hoặc lưu vào database
        flash('Tin nhắn của bạn đã được gửi thành công!', 'success')
        return redirect(url_for('main.contact'))
    return render_template('main/contact.html', title='Liên hệ', form=form) 