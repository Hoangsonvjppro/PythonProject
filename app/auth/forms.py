from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
from app.models.user import User

class LoginForm(FlaskForm):
    """Form đăng nhập"""
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Mật khẩu', validators=[DataRequired()])
    remember_me = BooleanField('Ghi nhớ đăng nhập')
    submit = SubmitField('Đăng nhập')

class RegisterForm(FlaskForm):
    """Form đăng ký"""
    username = StringField('Tên người dùng', validators=[
        DataRequired(), 
        Length(min=3, max=50, message='Tên người dùng phải từ 3-50 ký tự')
    ])
    email = StringField('Email', validators=[
        DataRequired(), 
        Email(message='Email không hợp lệ')
    ])
    password = PasswordField('Mật khẩu', validators=[
        DataRequired(),
        Length(min=6, message='Mật khẩu phải ít nhất 6 ký tự')
    ])
    password2 = PasswordField('Xác nhận mật khẩu', validators=[
        DataRequired(),
        EqualTo('password', message='Mật khẩu xác nhận không khớp')
    ])
    submit = SubmitField('Đăng ký')
    
    def validate_username(self, username):
        """Kiểm tra tên người dùng đã tồn tại chưa"""
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Tên người dùng này đã được sử dụng. Vui lòng chọn tên khác.')
    
    def validate_email(self, email):
        """Kiểm tra email đã tồn tại chưa"""
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email này đã được đăng ký. Vui lòng sử dụng email khác.')

class ProfileForm(FlaskForm):
    """Form cập nhật thông tin cá nhân"""
    username = StringField('Tên người dùng mới', validators=[
        Length(min=3, max=50, message='Tên người dùng phải từ 3-50 ký tự')
    ])
    submit = SubmitField('Cập nhật')
    
    def __init__(self, original_username, *args, **kwargs):
        super(ProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username
    
    def validate_username(self, username):
        """Kiểm tra tên người dùng mới có bị trùng không"""
        if username.data != self.original_username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('Tên người dùng này đã được sử dụng. Vui lòng chọn tên khác.')

class ChangePasswordForm(FlaskForm):
    """Form đổi mật khẩu"""
    old_password = PasswordField('Mật khẩu hiện tại', validators=[DataRequired()])
    new_password = PasswordField('Mật khẩu mới', validators=[
        DataRequired(),
        Length(min=6, message='Mật khẩu phải ít nhất 6 ký tự')
    ])
    new_password2 = PasswordField('Xác nhận mật khẩu mới', validators=[
        DataRequired(),
        EqualTo('new_password', message='Mật khẩu xác nhận không khớp')
    ])
    submit = SubmitField('Đổi mật khẩu') 