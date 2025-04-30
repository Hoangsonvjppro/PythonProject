from datetime import datetime
import sqlite3
import json
import numpy as np
from sentence_transformers import SentenceTransformer
import os
import shutil

print(f"[{datetime.now()}] Starting chatbot training script...")

# Ensure the instance directory exists
os.makedirs("instance", exist_ok=True)

# Check if chatbot_data.json exists in the duong folder
duong_json_path = os.path.join("duong", "chatbot_data.json")
instance_json_path = os.path.join("instance", "chatbot_data.json")

# Check if duong/chatbot_data.json exists
if os.path.exists(duong_json_path):
    print(f"[{datetime.now()}] Found chatbot_data.json in duong folder. Copying to instance folder...")
    shutil.copy(duong_json_path, instance_json_path)
else:
    print(f"[{datetime.now()}] Warning: {duong_json_path} not found.")
    # Create a basic json file with some sample data if it doesn't exist
    if not os.path.exists(instance_json_path):
        print(f"[{datetime.now()}] Creating a basic chatbot_data.json file...")
        basic_data = [
            {"question": "Hello", "answer": "Xin chào! Tôi có thể giúp gì cho bạn?"},
            {"question": "What is your name?", "answer": "Tôi là trợ lý AI của bạn."},
            {"question": "How are you?", "answer": "Tôi là một bot, nhưng tôi đang hoạt động rất tốt!"},
            {"question": "Goodbye", "answer": "Tạm biệt! Chúc bạn một ngày tốt lành!"}
        ]
        with open(instance_json_path, "w", encoding="utf-8") as f:
            json.dump(basic_data, f, ensure_ascii=False, indent=2)

# Check if duong/chatbot_data.db exists and copy it if it does
duong_db_path = os.path.join("duong", "chatbot_data.db")
instance_db_path = os.path.join("instance", "chatbot_data.db")

if os.path.exists(duong_db_path):
    print(f"[{datetime.now()}] Found chatbot_data.db in duong folder. Copying to instance folder...")
    shutil.copy(duong_db_path, instance_db_path)
    print(f"[{datetime.now()}] Database copied successfully. Skipping retraining...")
    exit(0)

# Continue with training if we didn't find an existing database
print(f"[{datetime.now()}] Loading SentenceTransformer model...")
try:
    model = SentenceTransformer('paraphrase-MiniLM-L6-v2')
    print(f"[{datetime.now()}] Model loaded successfully.")
except Exception as e:
    print(f"[{datetime.now()}] Error loading model: {str(e)}")
    exit(1)

# Check if JSON file exists
if not os.path.exists(instance_json_path):
    print(f"Error: File {instance_json_path} does not exist.")
    exit(1)

try:
    with open(instance_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    print(f"[{datetime.now()}] Loaded {len(data)} training examples.")
except Exception as e:
    print(f"Error reading {instance_json_path}: {str(e)}")
    exit(1)

questions = [item["question"] for item in data]
answers = [item["answer"] for item in data]

print(f"[{datetime.now()}] Encoding questions with SentenceTransformer...")
question_embeddings = model.encode(questions, convert_to_tensor=True).numpy()

print(f"[{datetime.now()}] Creating database...")
conn = sqlite3.connect(instance_db_path)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS chatbot_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    embedding BLOB NOT NULL
)
""")

print(f"[{datetime.now()}] Inserting data into database...")
for question, answer, embedding in zip(questions, answers, question_embeddings):
    cursor.execute("""
    INSERT INTO chatbot_data (question, answer, embedding)
    VALUES (?, ?, ?)
    """, (question, answer, embedding.tobytes()))

conn.commit()
conn.close()

print(f"[{datetime.now()}] Dữ liệu đã được lưu vào SQLite!")
print(f"[{datetime.now()}] Training completed successfully.") 