import click
from flask.cli import with_appcontext
from flask import current_app
from app.models.user import User
from app.models.learning import Level, Lesson, UserProgress, Vocabulary, Test, SampleSentence, SpeechTest
from app.extensions import db
import os
import sys
import json
import sqlite3
import numpy as np
from datetime import datetime

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    print("Error: Required modules not available. Make sure you have installed all requirements.")


@click.command('create-admin')
@click.argument('username')
@click.argument('email')
@click.argument('password')
@with_appcontext
def create_admin_command(username, email, password):
    """Create a new admin user.

    Example:
        flask create-admin admin admin@example.com password123
    """
    try:
        if User.query.filter_by(username=username).first():
            click.echo(f"Error: Username {username} already exists.")
            return
        if User.query.filter_by(email=email).first():
            click.echo(f"Error: Email {email} already exists.")
            return

        user = User.create_admin(username, email, password)
        db.session.add(user)
        db.session.commit()
        click.echo(f"Admin user {username} created successfully.")
    except Exception as e:
        db.session.rollback()
        click.echo(f"Error creating admin user: {str(e)}")


@click.command('list-users')
@with_appcontext
def list_users_command():
    """List all users in the system."""
    try:
        users = User.query.all()
        if not users:
            click.echo("No users found.")
            return

        click.echo("\nUser List:")
        click.echo("=" * 80)
        click.echo(f"{'ID':<5} {'Username':<20} {'Email':<30} {'Role':<10} {'Created'}")
        click.echo("-" * 80)

        for user in users:
            created = "N/A"  # User model hiện không có trường created_at
            click.echo(f"{user.id:<5} {user.username:<20} {user.email:<30} {user.role:<10} {created}")

    except Exception as e:
        click.echo(f"Error listing users: {str(e)}")


@click.command('init-db')
@with_appcontext
def init_db_command():
    """Initialize the database with required tables."""
    try:
        db.create_all()
        click.echo("Database tables created successfully.")
    except Exception as e:
        click.echo(f"Error creating database tables: {str(e)}")


@click.command('init-chatbot')
@click.option('--force', is_flag=True, help='Ghi đè dữ liệu chatbot hiện có')
@with_appcontext
def init_chatbot(force):
    """Khởi tạo cơ sở dữ liệu cho chatbot"""
    try:
        click.echo(f"[{datetime.now()}] Starting chatbot initialization...")
        
        # Ensure instance directory exists
        os.makedirs("instance", exist_ok=True)
        
        # Set file paths
        json_path = os.path.join("instance", "chatbot_data.json")
        db_path = os.path.join("instance", "chatbot_data.db")
        
        # Check if database already exists
        if os.path.exists(db_path) and not force:
            click.echo(f"[{datetime.now()}] Chatbot database already exists. Use --force to overwrite.")
            return
            
        # Check if we have the JSON data
        if not os.path.exists(json_path):
            click.echo(f"[{datetime.now()}] Creating a basic chatbot_data.json file...")
            basic_data = [
                {"question": "Hello", "answer": "Xin chào! Tôi có thể giúp gì cho bạn?"},
                {"question": "What is your name?", "answer": "Tôi là trợ lý AI của bạn."},
                {"question": "How are you?", "answer": "Tôi là một bot, nhưng tôi đang hoạt động rất tốt!"},
                {"question": "Goodbye", "answer": "Tạm biệt! Chúc bạn một ngày tốt lành!"}
            ]
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(basic_data, f, ensure_ascii=False, indent=2)
                
        # Load the model
        click.echo(f"[{datetime.now()}] Loading SentenceTransformer model...")
        try:
            model = SentenceTransformer('paraphrase-MiniLM-L6-v2')
            click.echo(f"[{datetime.now()}] Model loaded successfully.")
        except Exception as e:
            click.echo(f"[{datetime.now()}] Error loading model: {str(e)}")
            return
            
        # Load the training data
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            click.echo(f"[{datetime.now()}] Loaded {len(data)} training examples.")
        except Exception as e:
            click.echo(f"Error reading {json_path}: {str(e)}")
            return
            
        questions = [item["question"] for item in data]
        answers = [item["answer"] for item in data]
        
        # Encode the questions
        click.echo(f"[{datetime.now()}] Encoding questions with SentenceTransformer...")
        question_embeddings = model.encode(questions, convert_to_tensor=True).numpy()
        
        # Create or overwrite the database
        click.echo(f"[{datetime.now()}] Creating database...")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("DROP TABLE IF EXISTS chatbot_data")
        cursor.execute("""
        CREATE TABLE chatbot_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            embedding BLOB NOT NULL
        )
        """)
        
        # Insert the data
        click.echo(f"[{datetime.now()}] Inserting data into database...")
        for question, answer, embedding in zip(questions, answers, question_embeddings):
            cursor.execute("""
            INSERT INTO chatbot_data (question, answer, embedding)
            VALUES (?, ?, ?)
            """, (question, answer, embedding.tobytes()))
            
        conn.commit()
        conn.close()
        
        click.echo(f"[{datetime.now()}] Chatbot database initialized successfully!")
    except Exception as e:
        click.echo(f"Error initializing chatbot: {str(e)}")


def register_commands(app):
    """Register CLI commands with the Flask application."""
    app.cli.add_command(create_admin_command)
    app.cli.add_command(list_users_command)
    app.cli.add_command(init_db_command)
    app.cli.add_command(init_chatbot)