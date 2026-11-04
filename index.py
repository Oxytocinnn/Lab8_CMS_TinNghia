import sys
import os

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

from app import app, db
from models import Role, User

# Khởi tạo bảng và seed dữ liệu nếu CSDL chưa có dữ liệu
with app.app_context():
    try:
        db.create_all()
        Role.insert_roles()
        # Nếu chưa có người dùng nào, tự động seed tài khoản và bài viết mẫu
        if User.query.count() == 0:
            from seed import run as seed_run
            seed_run()
    except Exception as e:
        print(f"[Init DB] Info: {e}")

# Biến WSGI app bắt buộc để Vercel chạy
app = app
