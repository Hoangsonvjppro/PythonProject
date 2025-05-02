from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from functools import wraps
from sqlalchemy import func

from app.admin import bp
from app.models.user import User
from app.models.learning import Level, Lesson, UserProgress, Vocabulary, Test
from app.models.chat import ChatRoom, Message, StatusPost
from app.extensions import db


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
    # Số người dùng hoạt động
    active_users = User.query.filter_by(active=True).count()
    # Tổng số bài học
    total_lessons = Lesson.query.count()
    # Tổng số từ vựng
    total_vocabulary = Vocabulary.query.count()
    # Tổng số bài kiểm tra
    total_tests = Test.query.count()
    
    # Thống kê về bài học
    lesson_stats = []
    lessons = Lesson.query.all()
    for lesson in lessons:
        completions = UserProgress.query.filter_by(lesson_id=lesson.id, completion_status=True).count()
        if total_users > 0:
            completion_rate = int((completions / total_users) * 100)
        else:
            completion_rate = 0
        lesson_stats.append({
            'lesson': lesson,
            'completions': completions,
            'completion_rate': completion_rate
        })

    return render_template('admin/stats.html',
                           total_users=total_users,
                           active_users=active_users,
                           total_lessons=total_lessons,
                           total_vocabulary=total_vocabulary,
                           total_tests=total_tests,
                           lesson_stats=lesson_stats)


@bp.route('/users/<int:user_id>')
@login_required
@admin_required
def user_detail(user_id):
    """Chi tiết người dùng"""
    user = User.query.get_or_404(user_id)
    
    # Xử lý hành động xóa người dùng
    if request.args.get('action') == 'delete':
        # Không cho phép xóa chính mình
        if user.id == current_user.id:
            flash('Bạn không thể xóa tài khoản của chính mình.', 'danger')
            return redirect(url_for('admin.dashboard'))
            
        username = user.username
        try:
            db.session.delete(user)
            db.session.commit()
            flash(f'Đã xóa người dùng {username} thành công.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Không thể xóa người dùng: {str(e)}', 'danger')
            
        return redirect(url_for('admin.dashboard'))
    
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


@bp.route('/users/<int:user_id>/toggle-status', methods=['POST'])
@login_required
@admin_required
def toggle_user_status(user_id):
    """Chuyển đổi trạng thái người dùng (kích hoạt/khóa)"""
    user = User.query.get_or_404(user_id)

    # Không cho phép khóa chính mình hoặc admin khác
    if user.id == current_user.id:
        flash('Bạn không thể thay đổi trạng thái của chính mình.', 'warning')
        return redirect(url_for('admin.users'))
    
    if user.role == 'admin' and current_user.id != user.id:
        flash('Bạn không thể thay đổi trạng thái của admin khác.', 'warning')
        return redirect(url_for('admin.users'))

    # Đảo ngược trạng thái hiện tại
    user.active = not user.active
    db.session.commit()

    status = "kích hoạt" if user.active else "khóa"
    flash(f'Đã {status} tài khoản của {user.username}.', 'success')
    return redirect(url_for('admin.users'))


@bp.route('/add-content/<string:content_type>', methods=['GET', 'POST'])
@login_required
@admin_required
def add_content(content_type):
    """Thêm nội dung mới (cấp độ/bài học)"""
    if content_type not in ['level', 'lesson']:
        flash('Loại nội dung không hợp lệ.', 'danger')
        return redirect(url_for('admin.content'))
        
    if request.method == 'POST':
        if content_type == 'level':
            # Xử lý thêm cấp độ mới
            level_name = request.form.get('level_name')
            description = request.form.get('description')
            icon = request.form.get('icon', 'graduation-cap')
            order = request.form.get('order', 0)
            
            level = Level(
                level_name=level_name,
                description=description,
                icon=icon,
                order=int(order),
                created_by=current_user.id
            )
            
            try:
                db.session.add(level)
                db.session.commit()
                flash(f'Đã thêm cấp độ {level_name} thành công!', 'success')
                return redirect(url_for('admin.content'))
            except Exception as e:
                db.session.rollback()
                flash(f'Không thể thêm cấp độ: {str(e)}', 'danger')
                
        elif content_type == 'lesson':
            # Xử lý thêm bài học mới
            title = request.form.get('title')
            description = request.form.get('description')
            level_id = request.form.get('level_id')
            order = request.form.get('order', 0)
            content = request.form.get('content')
            
            lesson = Lesson(
                title=title,
                description=description,
                level_id=int(level_id),
                order=int(order),
                content=content,
                created_by=current_user.id
            )
            
            try:
                db.session.add(lesson)
                db.session.commit()
                flash(f'Đã thêm bài học {title} thành công!', 'success')
                return redirect(url_for('admin.content'))
            except Exception as e:
                db.session.rollback()
                flash(f'Không thể thêm bài học: {str(e)}', 'danger')
    
    # GET request - hiển thị form
    levels = Level.query.all()
    return render_template('admin/add_content.html', 
                        content_type=content_type,
                        levels=levels)


@bp.route('/edit-content/<string:content_type>/<int:content_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_content(content_type, content_id):
    """Chỉnh sửa nội dung (cấp độ/bài học)"""
    if content_type not in ['level', 'lesson']:
        flash('Loại nội dung không hợp lệ.', 'danger')
        return redirect(url_for('admin.content'))
    
    # Lấy nội dung cần sửa
    if content_type == 'level':
        content = Level.query.get_or_404(content_id)
    else:
        content = Lesson.query.get_or_404(content_id)
    
    if request.method == 'POST':
        if content_type == 'level':
            # Cập nhật thông tin cấp độ
            content.level_name = request.form.get('level_name')
            content.description = request.form.get('description')
            content.icon = request.form.get('icon')
            content.order = int(request.form.get('order', 0))
        else:
            # Cập nhật thông tin bài học
            content.title = request.form.get('title')
            content.description = request.form.get('description')
            content.order = int(request.form.get('order', 0))
            content.content = request.form.get('content')
        
        try:
            db.session.commit()
            flash(f'Đã cập nhật thành công!', 'success')
            return redirect(url_for('admin.content'))
        except Exception as e:
            db.session.rollback()
            flash(f'Không thể cập nhật: {str(e)}', 'danger')
    
    # GET request - hiển thị form với dữ liệu hiện tại
    return render_template('admin/edit_content.html',
                        content_type=content_type,
                        content=content)


@bp.route('/delete-content/<string:content_type>/<int:content_id>', methods=['POST'])
@login_required
@admin_required
def delete_content(content_type, content_id):
    """Xóa nội dung (cấp độ/bài học)"""
    if content_type not in ['level', 'lesson']:
        flash('Loại nội dung không hợp lệ.', 'danger')
        return redirect(url_for('admin.content'))
    
    if content_type == 'level':
        content = Level.query.get_or_404(content_id)
        # Kiểm tra xem cấp độ có bài học nào không
        if content.lessons:
            flash('Không thể xóa cấp độ đang có bài học.', 'warning')
            return redirect(url_for('admin.content'))
            
        name = content.level_name
    else:
        content = Lesson.query.get_or_404(content_id)
        # Xóa tiến độ học tập liên quan
        UserProgress.query.filter_by(lesson_id=content_id).delete()
        name = content.title
    
    try:
        db.session.delete(content)
        db.session.commit()
        flash(f'Đã xóa "{name}" thành công!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Không thể xóa: {str(e)}', 'danger')
    
    return redirect(url_for('admin.content'))