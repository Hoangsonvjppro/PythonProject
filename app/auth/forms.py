from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
from app.models.user import User

class LoginForm(FlaskForm):
    """Form đăng nhập"""
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Mật khẩu', validators=[DataRequired()])
    remember_me = BooleanField('Nhớ đăng nhập')
    submit = SubmitField('Đăng nhập')

class RegisterForm(FlaskForm):
    """Form đăng ký"""
    username = StringField('Tên người dùng', validators=[
        DataRequired(),
        Length(min=3, max=50)
    ])
    email = StringField('Email', validators=[
        DataRequired(),
        Email(),
        Length(max=100)
    ])
    password = PasswordField('Mật khẩu', validators=[
        DataRequired(),
        Length(min=6, max=50)
    ])
    password2 = PasswordField('Xác nhận mật khẩu', validators=[
        DataRequired(),
        EqualTo('password', message='Mật khẩu không khớp')
    ])
    submit = SubmitField('Đăng ký')
    
    def validate_username(self, username):
        """Kiểm tra tên người dùng đã tồn tại hay chưa"""
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Tên người dùng đã tồn tại. Vui lòng chọn tên khác.')
    
    def validate_email(self, email):
        """Kiểm tra email đã tồn tại hay chưa"""
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Email đã được sử dụng. Vui lòng chọn email khác.')

class ChangePasswordForm(FlaskForm):
    """Form đổi mật khẩu"""
    old_password = PasswordField('Mật khẩu hiện tại', validators=[DataRequired()])
    new_password = PasswordField('Mật khẩu mới', validators=[
        DataRequired(),
        Length(min=6, max=50)
    ])
    new_password2 = PasswordField('Xác nhận mật khẩu mới', validators=[
        DataRequired(),
        EqualTo('new_password', message='Mật khẩu không khớp')
    ])
    submit = SubmitField('Cập nhật mật khẩu') 