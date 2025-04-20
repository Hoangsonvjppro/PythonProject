from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import current_user, login_required
from models.models import Level, Lesson, UserProgress, db, SampleSentence, Test
from datetime import datetime

tutorials_bp = Blueprint('tutorials', __name__, template_folder='templates')


@tutorials_bp.route('/tutorials')
@login_required
def tutorials():
    levels = Level.query.order_by(Level.level_id).all()
    level_data = {}
    for level in levels:
        lessons = Lesson.query.filter_by(level_id=level.level_id).order_by(Lesson.lesson_id).all()
        total_lessons = len(lessons)
        completed_lessons = UserProgress.query.filter_by(
            user_id=current_user.id,
            completion_status=True
        ).join(Lesson).filter(Lesson.level_id == level.level_id).count()

        completion_percentage = (completed_lessons / total_lessons * 100) if total_lessons > 0 else 0
        level_data[level.level_id] = {
            "level_name": level.level_name,
            "title": f"Cấp độ {level.level_name}",
            "description": f"Học các kỹ năng cơ bản cho cấp độ {level.level_name}.",
            "icon": "book",
            "total_lessons": total_lessons,
            "completed_lessons": completed_lessons,
            "completion": round(completion_percentage, 2),
            "is_locked": level.level_id > 1 and completion_percentage < 80  # Khóa nếu chưa hoàn thành 80% cấp độ trước
        }
    return render_template('tutorials.html', levels=level_data, current_user=current_user)


@tutorials_bp.route('/tutorials/<int:level_id>')
@login_required
def level_detail(level_id):
    level = Level.query.get_or_404(level_id)
    lessons = Lesson.query.filter_by(level_id=level_id).order_by(Lesson.lesson_id).all()

    # Kiểm tra nếu cấp độ bị khóa
    if level_id > 1:
        prev_level = Level.query.get(level_id - 1)
        prev_completion = UserProgress.query.filter_by(
            user_id=current_user.id,
            completion_status=True
        ).join(Lesson).filter(Lesson.level_id == prev_level.level_id).count()
        prev_total = Lesson.query.filter_by(level_id=prev_level.level_id).count()
        if prev_total > 0 and (prev_completion / prev_total * 100) < 80:
            flash(f"Bạn cần hoàn thành ít nhất 80% cấp độ {prev_level.level_name} để mở khóa cấp độ này!", "warning")
            return redirect(url_for('tutorials.tutorials'))

    lesson_progress = []
    for lesson in lessons:
        progress = UserProgress.query.filter_by(
            user_id=current_user.id,
            lesson_id=lesson.lesson_id
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
        'level_detail.html',
        level=level,
        lesson_progress=lesson_progress,
        progress_percent=progress_percent,
        current_user=current_user
    )


@tutorials_bp.route('/tutorials/<int:level_id>/lesson/<int:lesson_id>')
@login_required
def lesson_detail(level_id, lesson_id):
    lesson = Lesson.query.filter_by(lesson_id=lesson_id, level_id=level_id).first_or_404()
    level = Level.query.get(level_id)

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

    # Lấy bài tập phát âm nếu có
    speech_test = Test.query.filter_by(level_id=level_id, test_type='speech').first()
    pronunciation_sentences = SampleSentence.query.filter_by(test_id=speech_test.test_id).all() if speech_test else []

    return render_template(
        'lesson_detail.html',
        level=level,
        lesson=lesson,
        progress=progress,
        pronunciation_sentences=pronunciation_sentences
    )


@tutorials_bp.route('/tutorials/<int:level_id>/complete/<int:lesson_id>', methods=['POST'])
@login_required
def complete_lesson(level_id, lesson_id):
    progress = UserProgress.query.filter_by(
        user_id=current_user.id,
        lesson_id=lesson_id
    ).first_or_404()

    data = request.get_json()
    vocab_results = data.get('vocab_results', [])
    sentence_results = data.get('sentence_results', [])

    # Kiểm tra điều kiện hoàn thành
    if not all(vocab_results) or not all(sentence_results):
        return jsonify({
            "success": False,
            "message": "Bạn cần hoàn thành tất cả bài tập phát âm!"
        }), 400

    # Cập nhật tiến độ
    progress.completion_status = True
    progress.completed_at = datetime.utcnow()
    db.session.commit()

    return jsonify({
        "success": True,
        "redirect": url_for('tutorials.level_detail', level_id=level_id)
    })
    # Kiểm tra nếu đã hoàn thành tất cả bài học trong cấp độ
    total_lessons = Lesson.query.filter_by(level_id=level_id).count()
    completed_lessons = UserProgress.query.filter_by(
        user_id=current_user.id,
        completion_status=True
    ).join(Lesson).filter(Lesson.level_id == level_id).count()

    level_completed = completed_lessons >= total_lessons

    return jsonify({
        "success": True,
        "level_completed": level_completed,
        "next_lesson_url": url_for('tutorials.lesson_detail', level_id=level_id,
                                   lesson_id=lesson_id + 1) if not level_completed else None,
        "level_url": url_for('tutorials.level_detail', level_id=level_id),
        "progress_percent": round((completed_lessons / total_lessons * 100), 2) if total_lessons > 0 else 0
    })