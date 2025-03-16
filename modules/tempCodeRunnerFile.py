import openai
import os

openai.api_key = os.getenv("OPENAI_API_KEY")  # Kiểm tra API Key

response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[{"role": "user", "content": "Hello!"}]
)

print(response)