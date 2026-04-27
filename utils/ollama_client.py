"""utils/ollama_client.py — Async wrapper for Ollama API."""
import aiohttp
import json
from config import OLLAMA_BASE_URL, MODEL_NAME

class OllamaError(Exception):
    pass

async def generate(prompt: str, system: str = "", temperature: float = 0.8) -> str:
    """Stateless generation for the Scenario Generator."""
    url = f"{OLLAMA_BASE_URL}/api/generate"
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "system": system,
        "temperature": temperature,
        "stream": False
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, json=payload) as response:
                if response.status != 200:
                    text = await response.text()
                    raise OllamaError(f"Ollama returned {response.status}: {text}")
                
                data = await response.json()
                return data.get("response", "")
        except aiohttp.ClientError as e:
             raise OllamaError(f"Failed to connect to Ollama at {OLLAMA_BASE_URL}. Is it running? Error: {e}")

async def chat(messages: list[dict], temperature: float = 0.7) -> str:
    """Stateful chat for Cast Agents."""
    url = f"{OLLAMA_BASE_URL}/api/chat"
    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "temperature": temperature,
        "stream": False
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, json=payload) as response:
                if response.status != 200:
                    text = await response.text()
                    raise OllamaError(f"Ollama returned {response.status}: {text}")
                
                data = await response.json()
                return data.get("message", {}).get("content", "")
        except aiohttp.ClientError as e:
            raise OllamaError(f"Failed to connect to Ollama: {e}")
