from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import current_user, login_required
from datetime import datetime

from app.tutorials import bp
from app.models.learning import Level, Lesson, UserProgress, PronunciationExercise, PronunciationAttempt
from app.extensions import db

@bp.route('/')
@login_required
def index():
    """Trang chính của học tập - danh sách các cấp độ"""
    levels = Level.query.filter_by(active=True).order_by(Level.order).all()
    
    level_data = {}
    for level in levels:
        lessons = Lesson.query.filter_by(level_id=level.id, active=True).order_by(Lesson.order).all()
        total_lessons = len(lessons)
        
        if total_lessons > 0:
            # Tính số bài học đã hoàn thành
            completed_lessons = UserProgress.query.filter_by(
                user_id=current_user.id,
                completion_status=True
            ).join(Lesson).filter(Lesson.level_id == level.id).count()
            
            completion_percentage = (completed_lessons / total_lessons * 100) if total_lessons > 0 else 0
            
            # Kiểm tra xem cấp độ có bị khóa không
            is_locked = False
            if level.order > 1:  # Không khóa cấp độ đầu tiên
                prev_levels = Level.query.filter(Level.order < level.order).order_by(Level.order.desc()).first()
                if prev_levels:
                    prev_lessons = Lesson.query.filter_by(level_id=prev_levels.id, active=True).all()
                    prev_completed = UserProgress.query.filter_by(
                        user_id=current_user.id,
                        completion_status=True
                    ).join(Lesson).filter(Lesson.level_id == prev_levels.id).count()
                    
                    if len(prev_lessons) > 0 and (prev_completed / len(prev_lessons) < 0.8):
                        is_locked = True
            
            level_data[level.id] = {
                "id": level.id,
                "name": level.name,
                "description": level.description,
                "icon": level.icon or "graduation-cap",
                "total_lessons": total_lessons,
                "completed_lessons": completed_lessons,
                "completion": round(completion_percentage, 2),
                "is_locked": is_locked
            }
    
    return render_template('tutorials/index.html', title='Lộ trình học tập', levels=level_data)

@bp.route('/<int:level_id>')
@login_required
def level_detail(level_id):
    """Chi tiết cấp độ"""
    level = Level.query.filter_by(id=level_id, active=True).first_or_404()
    lessons = Lesson.query.filter_by(level_id=level_id, active=True).order_by(Lesson.order).all()
    
    # Kiểm tra nếu cấp độ bị khóa
    if level.order > 1:
        prev_level = Level.query.filter(Level.order < level.order).order_by(Level.order.desc()).first()
        if prev_level:
            prev_lessons = Lesson.query.filter_by(level_id=prev_level.id, active=True).all()
            prev_completed = UserProgress.query.filter_by(
                user_id=current_user.id,
                completion_status=True
            ).join(Lesson).filter(Lesson.level_id == prev_level.id).count()
            
            if len(prev_lessons) > 0 and (prev_completed / len(prev_lessons) < 0.8):
                flash(f'Bạn cần hoàn thành ít nhất 80% cấp độ {prev_level.name} để mở khóa cấp độ này!', 'warning')
                return redirect(url_for('tutorials.index'))
    
    # Lấy thông tin tiến độ cho mỗi bài học
    lesson_progress = []
    for lesson in lessons:
        progress = UserProgress.query.filter_by(
            user_id=current_user.id,
            lesson_id=lesson.id
        ).first()
        
        lesson_progress.append({
            "lesson": lesson,
            "is_completed": progress.completion_status if progress else False,
            "completed_at": progress.completed_at if progress and progress.completion_status else None
        })
    
    # Tính toán tiến độ
    completed_count = sum(1 for lp in lesson_progress if lp['is_completed'])
    progress_percent = round((completed_count / len(lessons) * 100), 2) if lessons else 0
    
    return render_template(
        'tutorials/level_detail.html',
        title=f'Cấp độ {level.name}',
        level=level,
        lesson_progress=lesson_progress,
        completed_count=completed_count,
        progress_percent=progress_percent
    )

@bp.route('/<int:level_id>/lesson/<int:lesson_id>')
@login_required
def lesson_detail(level_id, lesson_id):
    """Chi tiết bài học"""
    level = Level.query.filter_by(id=level_id, active=True).first_or_404()
    lesson = Lesson.query.filter_by(id=lesson_id, level_id=level_id, active=True).first_or_404()
    
    # Kiểm tra tiến độ bài học
    progress = UserProgress.query.filter_by(
        user_id=current_user.id,
        lesson_id=lesson_id
    ).first()
    
    if not progress:
        progress = UserProgress(
            user_id=current_user.id,
            lesson_id=lesson_id,
            completion_status=False
        )
        db.session.add(progress)
        db.session.commit()
    
    # Lấy bài tập phát âm
    pronunciation_exercises = PronunciationExercise.query.filter_by(lesson_id=lesson_id).all()
    
    # Lấy kết quả phát âm trước đó
    exercise_results = {}
    for exercise in pronunciation_exercises:
        attempt = PronunciationAttempt.query.filter_by(
            user_id=current_user.id,
            exercise_id=exercise.id
        ).order_by(PronunciationAttempt.created_at.desc()).first()
        
        if attempt:
            exercise_results[exercise.id] = {
                'accuracy': attempt.accuracy,
                'feedback': attempt.feedback,
                'passed': attempt.accuracy >= 70
            }
    
    return render_template(
        'tutorials/lesson_detail.html',
        title=f'Bài: {lesson.title}',
        level=level,
        lesson=lesson,
        progress=progress,
        pronunciation_exercises=pronunciation_exercises,
        exercise_results=exercise_results
    )

@bp.route('/<int:level_id>/complete/<int:lesson_id>', methods=['POST'])
@login_required
def complete_lesson(level_id, lesson_id):
    """Đánh dấu bài học đã hoàn thành"""
    progress = UserProgress.query.filter_by(
        user_id=current_user.id,
        lesson_id=lesson_id
    ).first_or_404()
    
    data = request.get_json()
    
    # Kiểm tra xem bài học có bài tập phát âm bắt buộc không
    required_exercises = PronunciationExercise.query.filter_by(
        lesson_id=lesson_id,
        is_required=True
    ).all()
    
    if required_exercises:
        # Kiểm tra kết quả phát âm
        for exercise in required_exercises:
            attempt = PronunciationAttempt.query.filter_by(
                user_id=current_user.id,
                exercise_id=exercise.id
            ).order_by(PronunciationAttempt.created_at.desc()).first()
            
            if not attempt or attempt.accuracy < 70:
                return jsonify({
                    "success": False,
                    "message": "Bạn cần hoàn thành tất cả bài tập phát âm bắt buộc với độ chính xác ≥ 70%!"
                }), 400
    
    # Cập nhật tiến độ
    progress.completion_status = True
    progress.completed_at = datetime.utcnow()
    db.session.commit()
    
    # Kiểm tra nếu đã hoàn thành tất cả bài học trong cấp độ
    total_lessons = Lesson.query.filter_by(level_id=level_id, active=True).count()
    completed_lessons = UserProgress.query.filter_by(
        user_id=current_user.id,
        completion_status=True
    ).join(Lesson).filter(Lesson.level_id == level_id).count()
    
    level_completed = completed_lessons >= total_lessons
    
    # Tìm bài học tiếp theo nếu có
    next_lesson = None
    if not level_completed:
        next_lesson = Lesson.query.filter(
            Lesson.level_id == level_id,
            Lesson.active == True,
            Lesson.order > Lesson.query.get(lesson_id).order
        ).order_by(Lesson.order).first()
    
    return jsonify({
        "success": True,
        "level_completed": level_completed,
        "next_lesson_url": url_for('tutorials.lesson_detail', level_id=level_id, lesson_id=next_lesson.id) if next_lesson else None,
        "level_url": url_for('tutorials.level_detail', level_id=level_id),
        "progress_percent": round((completed_lessons / total_lessons * 100), 2) if total_lessons > 0 else 0
    }) 