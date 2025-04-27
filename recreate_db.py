#!/usr/bin/env python3
"""
Database recreation utility

This script recreates the database with the proper schema.
Run this script when you have schema issues.
"""

import os
import sys

# Check if the database file exists and remove it
db_file = 'learning_app.db'
if os.path.exists(db_file):
    print(f"Removing existing database file: {db_file}")
    os.remove(db_file)
    print("Database file removed successfully.")
else:
    print("No existing database file found.")

# Execute app.py with recreate-db flag
print("Recreating database with new schema...")
os.system("python app.py recreate-db")
print("Database recreation completed.")
