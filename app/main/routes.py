from flask import render_template, redirect, url_for, flash, request
from flask_login import current_user, login_required
from app.main import bp

@bp.route('/')
def index():
    """Trang chủ"""
    return render_template('main/home.html', title='Trang chủ')

@bp.route('/settings')
@login_required
def settings():
    """Trang cài đặt tài khoản"""
    return render_template('main/settings.html', title='Cài đặt') 