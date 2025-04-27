from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from functools import wraps
from sqlalchemy import func

from app.admin import bp
from app.models.models import User, Level, Lesson, UserProgress, Vocabulary, Test, db, ChatRoom, Message, StatusPost

def admin_required(f):
    """Decorator để giới hạn quyền truy cập chỉ cho admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != "admin":
            flash("Bạn không có quyền truy cập trang này!", "danger")
            return redirect(url_for('main.home'))
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/')
@login_required
@admin_required
def dashboard():
    users = User.query.all()
    return render_template('admin/admin.html', users=users)

@bp.route('/users')
@login_required
@admin_required
def users():
    users = User.query.all()
    return render_template('admin/users.html', users=users)

@bp.route('/content')
@login_required
@admin_required
def content():
    levels = Level.query.all()
    lessons = Lesson.query.all()
    vocabulary = Vocabulary.query.all()
    tests = Test.query.all()
    return render_template('admin/content.html', levels=levels, lessons=lessons, vocabulary=vocabulary, tests=tests)

@bp.route('/stats')
@login_required
@admin_required
def stats():
    # Tổng số người dùng
    total_users = User.query.count()
    # Tổng số bài học
    total_lessons = Lesson.query.count()
    # Tổng số từ vựng
    total_vocabulary = Vocabulary.query.count()
    # Tổng số bài kiểm tra
    total_tests = Test.query.count()
    
    return render_template('admin/stats.html', 
                           total_users=total_users,
                           total_lessons=total_lessons,
                           total_vocabulary=total_vocabulary,
                           total_tests=total_tests)

# Quản lý người dùng
@bp.route('/users/<int:user_id>')
@login_required
@admin_required
def user_detail(user_id):
    """Chi tiết người dùng"""
    user = User.query.get_or_404(user_id)
    user_progress = UserProgress.query.filter_by(user_id=user_id).all()
    return render_template('admin/user_detail.html', title=f'Chi tiết: {user.username}',
                          user=user, user_progress=user_progress)

@bp.route('/users/<int:user_id>/toggle-role', methods=['POST'])
@login_required
@admin_required
def toggle_user_role(user_id):
    """Chuyển đổi quyền người dùng giữa admin và người dùng thường"""
    user = User.query.get_or_404(user_id)
    
    # Không cho phép hạ cấp chính mình
    if user.id == current_user.id:
        flash('Bạn không thể thay đổi quyền của chính mình.', 'warning')
        return redirect(url_for('admin.users'))
    
    user.role = 'user' if user.role == 'admin' else 'admin'
    db.session.commit()
    
    flash(f'Đã thay đổi quyền của {user.username} thành {user.role}.', 'success')
    return redirect(url_for('admin.users'))