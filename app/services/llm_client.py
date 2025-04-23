# core/llm_client.py
import requests
from os import getenv

LLAMA_API_URL = getenv("LLM_API_URL")

class LLMClient:
    def __init__(self, endpoint: str = LLAMA_API_URL, model: str = "meta-llama/Llama-3.2-3B-Instruct") -> None:
        self.endpoint = endpoint
        self.model = model

    def query(self, messages: list[str | dict]) -> str:
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.1,
            "max_tokens": 512,
        }
        r = requests.post(self.endpoint, json=payload, timeout=60)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
