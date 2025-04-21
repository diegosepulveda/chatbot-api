from __future__ import annotations
from typing import Dict, List, Optional
import uuid
import requests
import os

LLAMA_API_URL = os.getenv("LLM_API_URL") 

SYSTEM_PROMPT = (
    "You are a helpful real‑estate assistant. Only provide information about "
    "properties, prices, locations, features, and how users can schedule a visit. "
    "If the user's question is unrelated to real estate, politely refuse to answer."
)


class ChatSessionManager:
    """In‑memory chat history per session_id (swap for Redis later)."""

    def __init__(self) -> None:
        self.sessions: Dict[str, List[dict]] = {}

    def get_or_create(self, session_id: Optional[str]) -> str:
        if not session_id or session_id not in self.sessions:
            session_id = str(uuid.uuid4())
            self.sessions[session_id] = []
        return session_id

    def add(self, session_id: str, role: str, content: str) -> None:
        self.sessions[session_id].append({"role": role, "content": content})

    def as_prompt(self, session_id: str) -> List[dict]:
        return [{"role": "system", "content": SYSTEM_PROMPT}] + self.sessions[session_id]


class PromptSecurityBarrier:
    """Very simple keyword blacklist.  Replace with embeddings later."""

    _blacklist = {"hack", "jailbreak", "prompt injection", "ignore previous"}

    @classmethod
    def is_valid(cls, prompt: str) -> bool:
        lowered = prompt.lower()
        return not any(bad in lowered for bad in cls._blacklist)


class LLMClient:
    """Wrap the vLLM / OpenAI‑style endpoint."""

    def __init__(self, endpoint: str = LLAMA_API_URL, model: str = "meta-llama/Llama-3.2-3B-Instruct"):
        self.endpoint = endpoint
        self.model = model

    def query(self, messages: list[str | dict]) -> str:
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.2,
            "max_tokens": 512,
        }
        r = requests.post(self.endpoint, json=payload, timeout=60)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
