"""utils/ollama_client.py — Groq API wrapper (free alternative to local Ollama)."""
import httpx
import json

# Groq API key (free tier at https://console.groq.com)
GROQ_API_KEY = "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"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

class OllamaError(Exception):
    pass

async def generate(prompt: str, system: str = "", temperature: float = 0.8) -> str:
    """Generate text via Groq API (stateless)."""
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
    payload = {
        "model": "mixtral-8x7b-32768",
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt}
        ],
        "temperature": temperature,
        "max_tokens": 2000
    }
    
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.post(GROQ_URL, json=payload, headers=headers)
            if resp.status_code != 200:
                raise OllamaError(f"Groq API error {resp.status_code}: {resp.text}")
            data = resp.json()
            return data["choices"][0]["message"]["content"]
        except httpx.RequestError as e:
            raise OllamaError(f"Failed to reach Groq: {e}")

async def chat(messages: list[dict], temperature: float = 0.7) -> str:
    """Chat via Groq API (stateful)."""
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": messages,
        "temperature": temperature,
        "max_tokens": 2000
    }
    
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.post(GROQ_URL, json=payload, headers=headers)
            if resp.status_code != 200:
                raise OllamaError(f"Groq API error {resp.status_code}: {resp.text}")
            data = resp.json()
            return data["choices"][0]["message"]["content"]
        except httpx.RequestError as e:
            raise OllamaError(f"Failed to reach Groq: {e}")
