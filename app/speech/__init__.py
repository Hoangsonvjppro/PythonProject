from flask import Blueprint

bp = Blueprint('speech', __name__)

from app.speech import routes 