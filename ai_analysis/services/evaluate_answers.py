import requests
import os
import re


# Read key from Django settings (which reads from .env) — never hardcode credentials here.
from django.conf import settings as _django_settings
GROQ_API_KEY = _django_settings.GROQ_API_KEY

API_URL = "https://api.groq.com/openai/v1/chat/completions"

headers = {
    "Authorization": f"Bearer {GROQ_API_KEY}",
    "Content-Type": "application/json"
}


# ---------- Read and parse numbered list ----------
def parse_file(filename):
    with open(filename, "r", encoding="utf-8") as f:
        lines = f.readlines()

    items = []
    for line in lines:
        match = re.sub(r"^\d+\.\s*", "", line.strip())
        if match:
            items.append(match)

    return items


# ---------- AI evaluation ----------
def evaluate(question, answer):
    prompt = f"""
You are an expert HR interviewer.

Evaluate the candidate's answer based on clarity, relevance, and understanding.

Question: {question}
Answer: {answer}

Evaluation guidelines:
- Do NOT be overly strict in scoring.
- If the answer includes the key idea or concept, give a GOOD score even if it is brief.
- Do NOT heavily penalize for short length, minor grammar issues, or imperfect wording.
- Focus more on understanding than completeness.
- Be fair, balanced, and slightly generous.

Return ONLY in this format:

Score: X/10
Feedback: ...
Improvement: ...
"""

    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }

    response = requests.post(API_URL, headers=headers, json=payload)

    if response.status_code != 200:
        return f"Error: {response.text}"

    data = response.json()
    return data["choices"][0]["message"]["content"]


# ---------- MAIN ----------
if __name__ == "__main__":
    print("Reading files...")

    questions = parse_file("questions.txt")
    answers = parse_file("answers.txt")

    results = []

    count = min(len(questions), len(answers))

    print(f"Evaluating {count} Q&A pairs...\n")

    for i in range(count):
        print(f"Processing Q{i+1}...")

        result = evaluate(questions[i], answers[i])

        formatted = f"""
========================
Question {i+1}: {questions[i]}
Answer: {answers[i]}

Evaluation:
{result}
========================
"""

        results.append(formatted)

    # ---------- Save results ----------
    with open("results.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(results))

    print("\nDone! Results saved to results.txt")