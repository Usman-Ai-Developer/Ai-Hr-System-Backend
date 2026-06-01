# ai_services/llm.py
import json
import requests
from django.conf import settings

GROQ_API_KEY = settings.GROQ_API_KEY
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"


def call_groq(prompt: str, model: str = "llama-3.1-8b-instant", temperature: float = 0.3) -> str:
    """
    Call Groq API with a prompt and return the response text.
    """
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature
    }
    response = requests.post(GROQ_API_URL, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]


def extract_json_from_llm_response(response_text: str) -> dict:
    """
    Clean LLM response that may contain markdown code blocks and parse JSON.
    """
    text = response_text.strip()
    if text.startswith("```json"):
        text = text[7:-3]
    elif text.startswith("```"):
        text = text[3:-3]
    # Try to find JSON object with regex as fallback
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        import re
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            return json.loads(match.group())
        raise