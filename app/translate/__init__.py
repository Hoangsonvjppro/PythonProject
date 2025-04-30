from flask import Blueprint
from flask_cors import CORS

bp = Blueprint('translate', __name__)
CORS(bp, resources={r"/*": {"origins": "*"}})

from app.translate import routes 