from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, BooleanField, IntegerField, SubmitField
from wtforms.validators import DataRequired, Length, ValidationError, Optional
from flask_wtf.file import FileField, FileAllowed

class LevelForm(FlaskForm):
    """Form để thêm/sửa cấp độ"""
    level_name = StringField('Tên cấp độ', validators=[DataRequired(), Length(max=50)])
    description = TextAreaField('Mô tả', validators=[DataRequired()])
    icon = StringField('Icon', default='graduation-cap')
    order = IntegerField('Thứ tự hiển thị', default=0)
    active = BooleanField('Kích hoạt', default=True)
    submit = SubmitField('Lưu')

class LessonForm(FlaskForm):
    """Form để thêm/sửa bài học"""
    title = StringField('Tiêu đề', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('Mô tả ngắn', validators=[DataRequired()])
    content = TextAreaField('Nội dung bài học', validators=[DataRequired()])
    level_id = SelectField('Cấp độ', coerce=int, validators=[DataRequired()])
    order = IntegerField('Thứ tự hiển thị', default=0)
    active = BooleanField('Kích hoạt', default=True)
    submit = SubmitField('Lưu')

class PronunciationExerciseForm(FlaskForm):
    """Form để thêm/sửa bài tập phát âm"""
    text = TextAreaField('Nội dung câu', validators=[DataRequired()])
    audio_file = FileField('File âm thanh (nếu có)', validators=[
        Optional(),
        FileAllowed(['mp3', 'wav'], 'Chỉ hỗ trợ file MP3 hoặc WAV.')
    ])
    is_required = BooleanField('Bắt buộc hoàn thành', default=True)
    submit = SubmitField('Lưu') 