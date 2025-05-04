from datetime import datetime
import sqlite3
import json
import numpy as np
from sentence_transformers import SentenceTransformer
import os

model = SentenceTransformer('paraphrase-MiniLM-L6-v2')

json_path = os.path.join("instance", "chatbot_data.json")
db_path = os.path.join("instance", "chatbot_data.db")

# Kiểm tra file JSON
if not os.path.exists(json_path):
    print(f"Error: File {json_path} does not exist.")
    exit(1)

try:
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
except Exception as e:
    print(f"Error reading {json_path}: {str(e)}")
    exit(1)

questions = [item["question"] for item in data]
answers = [item["answer"] for item in data]

question_embeddings = model.encode(questions, convert_to_tensor=True).numpy()

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS chatbot_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    embedding BLOB NOT NULL
)
""")

for question, answer, embedding in zip(questions, answers, question_embeddings):
    cursor.execute("""
    INSERT INTO chatbot_data (question, answer, embedding)
    VALUES (?, ?, ?)
    """, (question, answer, embedding.tobytes()))

conn.commit()
conn.close()

print(f"[{datetime.now()}] Dữ liệu đã được lưu vào SQLite!")