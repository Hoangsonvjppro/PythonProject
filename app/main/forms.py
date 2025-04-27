from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, EmailField
from wtforms.validators import DataRequired, Email

class ContactForm(FlaskForm):
    name = StringField('Họ và tên', validators=[DataRequired()])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    subject = StringField('Chủ đề', validators=[DataRequired()])
    message = TextAreaField('Nội dung tin nhắn', validators=[DataRequired()])
    submit = SubmitField('Gửi tin nhắn') 