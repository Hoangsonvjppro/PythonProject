from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import current_user, login_required
from models.models import Level, Lesson, UserProgress, db, SampleSentence, Test
from datetime import datetime

tutorials_bp = Blueprint('tutorials', __name__, template_folder='templates')

@tutorials_bp.route('/tutorials')
@login_required
def tutorials():
    levels = Level.query.all()
    level_data = {}
    for level in levels:
        lessons = Lesson.query.filter_by(level_id=level.level_id).all()
        total_lessons = len(lessons)
        completed_lessons = UserProgress.query.filter_by(
            user_id=current_user.id, completion_status=True
        ).join(Lesson).filter(Lesson.level_id == level.level_id).count()
        completion_percentage = (completed_lessons / total_lessons * 100) if total_lessons > 0 else 0
        level_data[level.level_name] = {
            "title": f"Cấp độ {level.level_name}",
            "description": f"Học các kỹ năng cơ bản cho cấp độ {level.level_name}.",
            "icon": "book",
            "difficulty": level.level_name,
            "lessons": total_lessons,
            "completion": round(completion_percentage, 2)
        }
    return render_template('tutorials.html', levels=level_data, current_user=current_user)

@tutorials_bp.route('/tutorials/start/<level_name>')
@login_required
def start_lesson(level_name):
    level = Level.query.filter_by(level_name=level_name).first()
    if not level:
        flash("Cấp độ không tồn tại!", "danger")
        return redirect(url_for('tutorials.tutorials'))
    lessons = Lesson.query.filter_by(level_id=level.level_id).order_by(Lesson.lesson_id).all()
    for lesson in lessons:
        progress = UserProgress.query.filter_by(user_id=current_user.id, lesson_id=lesson.lesson_id).first()
        if not progress or not progress.completion_status:
            return redirect(url_for('tutorials.lesson_detail', lesson_id=lesson.lesson_id))
    flash(f"Bạn đã hoàn thành tất cả bài học trong cấp độ {level_name}!", "success")
    return redirect(url_for('tutorials.tutorials'))

@tutorials_bp.route('/tutorials/lesson/<int:lesson_id>')
@login_required
def lesson_detail(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)
    progress = UserProgress.query.filter_by(user_id=current_user.id, lesson_id=lesson_id).first()
    if not progress:
        progress = UserProgress(user_id=current_user.id, lesson_id=lesson_id, completion_status=False)
        db.session.add(progress)
        db.session.commit()
    level = Level.query.get(lesson.level_id)
    speech_test = Test.query.filter_by(level_id=level.level_id, test_type='speech').first()
    pronunciation_sentences = SampleSentence.query.filter_by(test_id=speech_test.test_id).all() if speech_test else []
    return render_template('lesson.html', lesson=lesson, progress=progress, pronunciation_sentences=pronunciation_sentences)

@tutorials_bp.route('/tutorials/complete/<int:lesson_id>', methods=['POST'])
@login_required
def complete_lesson(lesson_id):
    progress = UserProgress.query.filter_by(user_id=current_user.id, lesson_id=lesson_id).first_or_404()
    lesson = Lesson.query.get(lesson_id)
    level = Level.query.get(lesson.level_id)
    speech_test = Test.query.filter_by(level_id=level.level_id, test_type='speech').first()

    # Kiểm tra điều kiện hoàn thành
    if speech_test:
        sentences = SampleSentence.query.filter_by(test_id=speech_test.test_id).all()
        accuracies = request.json.get('accuracies', [])
        if len(accuracies) != len(sentences) or not all(acc >= 70 for acc in accuracies):
            flash("Bạn cần hoàn thành tất cả bài tập phát âm với độ chính xác >= 70%!", "danger")
            return jsonify({"success": False, "message": "Bạn cần hoàn thành tất cả bài tập phát âm với độ chính xác >= 70%!"}), 400

    # Nếu đạt yêu cầu, cập nhật trạng thái hoàn thành
    progress.completion_status = True
    progress.completed_at = datetime.utcnow()
    db.session.commit()
    flash("Bạn đã hoàn thành bài học!", "success")

    # Chuyển đến bài học tiếp theo hoặc cấp độ tiếp theo
    next_lesson = Lesson.query.filter(
        Lesson.level_id == lesson.level_id,
        Lesson.lesson_id > lesson_id
    ).order_by(Lesson.lesson_id).first()
    if next_lesson:
        return jsonify({"success": True, "redirect": url_for('tutorials.lesson_detail', lesson_id=next_lesson.lesson_id)})
    else:
        current_level = Level.query.get(lesson.level_id)
        next_level = Level.query.filter(Level.level_id > current_level.level_id).order_by(Level.level_id).first()
        if next_level:
            flash(f"Chúc mừng! Bạn đã hoàn thành cấp độ {current_level.level_name}. Tiếp tục với {next_level.level_name}.", "success")
            return jsonify({"success": True, "redirect": url_for('tutorials.start_lesson', level_name=next_level.level_name)})
        else:
            flash("Chúc mừng! Bạn đã hoàn thành tất cả các cấp độ!", "success")
            return jsonify({"success": True, "redirect": url_for('tutorials.tutorials')})