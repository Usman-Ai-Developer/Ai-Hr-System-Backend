import requests
import os


# Read key from Django settings (which reads from .env) — never hardcode credentials here.
from django.conf import settings as _django_settings
GROQ_API_KEY = _django_settings.GROQ_API_KEY

API_URL = "https://api.groq.com/openai/v1/chat/completions"

headers = {
    "Authorization": f"Bearer {GROQ_API_KEY}",
    "Content-Type": "application/json"
}

def generate_questions(topic):
    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {
                "role": "user",
                "content": f"Generate 5 interview short and technical questions for {topic}. Return only numbered list."
            }
        ]
    }

    response = requests.post(API_URL, headers=headers, json=payload)

    print("STATUS:", response.status_code)
    print("RESPONSE:", response.text)

    data = response.json()
    return data["choices"][0]["message"]["content"]





if __name__ == "__main__":
    topic = input("Enter topic: ")

    print("\nGenerating questions...\n")

    result = generate_questions(topic)

    filename = f"{topic.replace(' ', '_')}_questions.txt"

    with open(filename, "w", encoding="utf-8") as f:
        f.write(result)

    print("\nSaved successfully!")
    print("File:", filename)

