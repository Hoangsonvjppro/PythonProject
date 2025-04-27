from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from functools import wraps
from sqlalchemy import func

from app.admin import bp
from app.models.user import User
from app.models.learning import Level, Lesson, UserProgress, Vocabulary, Test, PronunciationExercise
from app.models.chat import ChatRoom, Message, StatusPost
from app.admin.forms import LevelForm, LessonForm, PronunciationExerciseForm
from app.extensions import db

def admin_required(f):
    """Decorator để giới hạn quyền truy cập chỉ cho admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin():
            flash('Bạn không có quyền truy cập trang này.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/')
@login_required
@admin_required
def index():
    """Trang chủ admin"""
    stats = {
        'total_users': User.query.count(),
        'total_levels': Level.query.count(),
        'total_lessons': Lesson.query.count()
    }
    return render_template('admin/index.html', title='Quản trị', stats=stats)

# Quản lý người dùng
@bp.route('/users')
@login_required
@admin_required
def users():
    """Danh sách người dùng"""
    page = request.args.get('page', 1, type=int)
    users = User.query.paginate(page=page, per_page=10)
    return render_template('admin/users.html', title='Quản lý người dùng', users=users)

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

# Quản lý nội dung
@bp.route('/levels')
@login_required
@admin_required
def levels():
    """Danh sách cấp độ"""
    levels = Level.query.order_by(Level.order).all()
    return render_template('admin/levels.html', title='Quản lý cấp độ', levels=levels)

@bp.route('/levels/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_level():
    """Thêm cấp độ mới"""
    form = LevelForm()
    if form.validate_on_submit():
        level = Level(
            name=form.name.data,
            description=form.description.data,
            icon=form.icon.data,
            order=form.order.data,
            active=form.active.data,
            created_by=current_user.id
        )
        db.session.add(level)
        db.session.commit()
        
        flash('Đã thêm cấp độ mới thành công!', 'success')
        return redirect(url_for('admin.levels'))
    
    return render_template('admin/level_form.html', title='Thêm cấp độ mới', form=form)

@bp.route('/levels/<int:level_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_level(level_id):
    """Chỉnh sửa cấp độ"""
    level = Level.query.get_or_404(level_id)
    form = LevelForm(obj=level)
    
    if form.validate_on_submit():
        form.populate_obj(level)
        db.session.commit()
        
        flash('Đã cập nhật cấp độ thành công!', 'success')
        return redirect(url_for('admin.levels'))
    
    return render_template('admin/level_form.html', title=f'Chỉnh sửa: {level.name}', form=form)

@bp.route('/levels/<int:level_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_level(level_id):
    """Xóa cấp độ"""
    level = Level.query.get_or_404(level_id)
    
    # Kiểm tra nếu có bài học thuộc cấp độ này
    if level.lessons:
        flash('Không thể xóa cấp độ này vì nó chứa các bài học. Vui lòng xóa các bài học trước.', 'danger')
        return redirect(url_for('admin.levels'))
    
    name = level.name
    db.session.delete(level)
    db.session.commit()
    
    flash(f'Đã xóa cấp độ "{name}" thành công!', 'success')
    return redirect(url_for('admin.levels'))

# Quản lý bài học
@bp.route('/lessons')
@login_required
@admin_required
def lessons():
    """Danh sách bài học"""
    level_id = request.args.get('level_id', None, type=int)
    
    if level_id:
        level = Level.query.get_or_404(level_id)
        lessons = Lesson.query.filter_by(level_id=level_id).order_by(Lesson.order).all()
        return render_template('admin/lessons.html', title=f'Bài học: {level.name}',
                              lessons=lessons, level=level)
    
    # Hiển thị tất cả bài học nếu không có level_id
    lessons = Lesson.query.join(Level).order_by(Level.order, Lesson.order).all()
    return render_template('admin/lessons.html', title='Tất cả bài học', lessons=lessons)

@bp.route('/lessons/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_lesson():
    """Thêm bài học mới"""
    form = LessonForm()
    form.level_id.choices = [(level.id, level.name) for level in Level.query.order_by(Level.order).all()]
    
    if form.validate_on_submit():
        lesson = Lesson(
            title=form.title.data,
            description=form.description.data,
            content=form.content.data,
            level_id=form.level_id.data,
            order=form.order.data,
            active=form.active.data,
            created_by=current_user.id
        )
        db.session.add(lesson)
        db.session.commit()
        
        flash('Đã thêm bài học mới thành công!', 'success')
        return redirect(url_for('admin.lessons', level_id=lesson.level_id))
    
    # Lấy level_id từ query parameter nếu có
    level_id = request.args.get('level_id', None, type=int)
    if level_id:
        form.level_id.data = level_id
    
    return render_template('admin/lesson_form.html', title='Thêm bài học mới', form=form)

@bp.route('/lessons/<int:lesson_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_lesson(lesson_id):
    """Chỉnh sửa bài học"""
    lesson = Lesson.query.get_or_404(lesson_id)
    form = LessonForm(obj=lesson)
    form.level_id.choices = [(level.id, level.name) for level in Level.query.order_by(Level.order).all()]
    
    if form.validate_on_submit():
        form.populate_obj(lesson)
        db.session.commit()
        
        flash('Đã cập nhật bài học thành công!', 'success')
        return redirect(url_for('admin.lessons', level_id=lesson.level_id))
    
    return render_template('admin/lesson_form.html', title=f'Chỉnh sửa: {lesson.title}', form=form)

@bp.route('/lessons/<int:lesson_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_lesson(lesson_id):
    """Xóa bài học"""
    lesson = Lesson.query.get_or_404(lesson_id)
    level_id = lesson.level_id
    title = lesson.title
    
    db.session.delete(lesson)
    db.session.commit()
    
    flash(f'Đã xóa bài học "{title}" thành công!', 'success')
    return redirect(url_for('admin.lessons', level_id=level_id))

# Quản lý bài tập phát âm
@bp.route('/pronunciation/<int:lesson_id>')
@login_required
@admin_required
def pronunciation_exercises(lesson_id):
    """Danh sách bài tập phát âm cho bài học"""
    lesson = Lesson.query.get_or_404(lesson_id)
    exercises = PronunciationExercise.query.filter_by(lesson_id=lesson_id).all()
    
    return render_template('admin/pronunciation_exercises.html', 
                          title=f'Bài tập phát âm: {lesson.title}',
                          lesson=lesson, exercises=exercises)

@bp.route('/pronunciation/<int:lesson_id>/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_pronunciation_exercise(lesson_id):
    """Thêm bài tập phát âm mới"""
    lesson = Lesson.query.get_or_404(lesson_id)
    form = PronunciationExerciseForm()
    
    if form.validate_on_submit():
        exercise = PronunciationExercise(
            lesson_id=lesson_id,
            text=form.text.data,
            is_required=form.is_required.data,
            created_by=current_user.id
        )
        db.session.add(exercise)
        db.session.commit()
        
        flash('Đã thêm bài tập phát âm mới thành công!', 'success')
        return redirect(url_for('admin.pronunciation_exercises', lesson_id=lesson_id))
    
    return render_template('admin/pronunciation_form.html', 
                          title=f'Thêm bài tập phát âm: {lesson.title}',
                          form=form, lesson=lesson)

# Thống kê
@bp.route('/stats')
@login_required
@admin_required
def stats():
    """Thống kê và báo cáo"""
    user_count = User.query.count()
    lesson_count = Lesson.query.count()
    
    # Số người dùng đăng ký theo tháng
    user_monthly = db.session.query(
        func.strftime('%Y-%m', User.created_at).label('month'),
        func.count(User.id).label('count')
    ).group_by('month').order_by('month').all()
    
    # Bài học hoàn thành nhiều nhất
    top_lessons = db.session.query(
        Lesson.id, Lesson.title,
        func.count(UserProgress.id).label('completion_count')
    ).join(UserProgress, UserProgress.lesson_id == Lesson.id)\
     .filter(UserProgress.completion_status == True)\
     .group_by(Lesson.id)\
     .order_by(func.count(UserProgress.id).desc())\
     .limit(5).all()
    
    # Tỷ lệ hoàn thành theo cấp độ
    level_completion = db.session.query(
        Level.id, Level.name,
        func.count(Lesson.id).label('total_lessons'),
        func.count(UserProgress.id).label('completed_lessons')
    ).join(Lesson, Lesson.level_id == Level.id)\
     .outerjoin(UserProgress, (UserProgress.lesson_id == Lesson.id) & (UserProgress.completion_status == True))\
     .group_by(Level.id)\
     .order_by(Level.order).all()
    
    level_stats = []
    for level in level_completion:
        if level.total_lessons > 0:
            completion_rate = (level.completed_lessons / level.total_lessons) * 100
        else:
            completion_rate = 0
        level_stats.append({
            'name': level.name,
            'total': level.total_lessons,
            'completed': level.completed_lessons,
            'rate': round(completion_rate, 2)
        })
    
    return render_template('admin/stats.html', title='Thống kê',
                          user_count=user_count,
                          lesson_count=lesson_count,
                          user_monthly=user_monthly,
                          top_lessons=top_lessons,
                          level_stats=level_stats)