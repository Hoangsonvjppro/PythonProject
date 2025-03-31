from flask import Blueprint, render_template
from flask_login import current_user

tutorials_bp = Blueprint('tutorials', __name__, template_folder='templates')

# Lộ trình học tiếng Anh theo cấp độ
learning_path = {
    "A1": "Ngữ pháp cơ bản, từ vựng đơn giản, giao tiếp hàng ngày.",
    "A2": "Mở rộng từ vựng, mẫu câu thông dụng, giao tiếp du lịch.",
    "B1": "Nâng cao khả năng giao tiếp, viết email, đọc hiểu văn bản đơn giản.",
    "B2": "Sử dụng ngôn ngữ linh hoạt, tranh luận, viết luận cơ bản.",
    "C1": "Thành thạo tiếng Anh, đọc hiểu chuyên sâu, viết luận nâng cao."
}

@tutorials_bp.route('/tutorials')
def tutorials():
    return render_template('tutorials.html', levels=learning_path, current_user=current_user)
