#!/usr/bin/env python3
"""
Database recreation utility

This script recreates the database with the proper schema.
Run this script when you have schema issues.
"""

import os
import sys
import shutil
from app import create_app
from app.extensions import db

print("Beginning database recreation process...")

# Khởi tạo ứng dụng Flask
app = create_app()

# Xác định đường dẫn đến file database
with app.app_context():
    db_uri = app.config['SQLALCHEMY_DATABASE_URI']
    if db_uri.startswith('sqlite:///'):
        # Trích xuất đường dẫn từ sqlite:///path/to/file.db
        db_path = db_uri.replace('sqlite:///', '')
        if os.path.exists(db_path):
            print(f"Removing existing database file: {db_path}")
            os.remove(db_path)
            print("Database file removed successfully.")
        else:
            print(f"No existing database file found at {db_path}.")
    else:
        print("Non-SQLite database detected. Please drop and recreate manually.")
        sys.exit(1)

# Thông báo user về các bước tiếp theo
print("\nDatabase has been removed.")
print("Now run the following commands to recreate it:")
print("1. flask db upgrade")
print("2. flask init-db")
print("\nOr simply run: python -m flask db upgrade && python -m flask init-db")
