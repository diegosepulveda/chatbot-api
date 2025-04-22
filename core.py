# core.py – redis‑based chat & parameter tracking
from __future__ import annotations
from typing import Dict, List, Optional, TypedDict
import uuid, json, os, re
import requests, redis
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# ENV
# ---------------------------------------------------------------------------
LLAMA_API_URL = os.getenv("LLM_API_URL")
REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")

# ---------------------------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------------------------
REQUIRED_FIELDS = {"budget", "size", "type", "city"}  # expand anytime
SYSTEM_PROMPT = (
    "You are a helpful real‑estate assistant.\n"
    "First greet the user, then tell them you need the following information: \n"
    "1. Budget (number + currency)\n"
    "2. Total Size requirement (number + m²)\n"
    "3. Real‑estate type (e.g. office, apartment)\n"
    "4. City.\n\n"
    "You MUST collect all four before offering properties.\n"
    "When you have ALL four, respond with *only* a JSON object in the exact form: \n"
    "<params>{\"budget\": ..., \"size\": ..., \"type\": ..., \"city\": ...}</params> \n"
    "— no extra words. After that, provide a short human summary and an https link like \n"
    "https://example.com/search?budget=...&size=...&type=...&city=...\n"
    "If the user later changes any field, output a new <params> block with updated JSON.\n"
    "If the question is unrelated to real‑estate, politely refuse without further explanation."
)

PARAM_TAG_RE = re.compile(r"<params>(.*?)</params>")

# ---------------------------------------------------------------------------
# Redis connection
# ---------------------------------------------------------------------------
redis_client = redis.StrictRedis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    password=REDIS_PASSWORD,
    decode_responses=True,
)

# ---------------------------------------------------------------------------
# TypedDict for strong typing
# ---------------------------------------------------------------------------
class SearchParams(TypedDict, total=False):
    budget: str
    size: str
    type: str
    city: str

# ---------------------------------------------------------------------------
# ChatSessionManager now also tracks params + generated links
# ---------------------------------------------------------------------------
class ChatSessionManager:
    """Store messages + param snapshots in Redis."""

    def __init__(self):
        self.r = redis_client

    # ------------------- session helpers -------------------
    def _msg_key(self, sid: str) -> str:  # list of messages
        return f"{sid}:msgs"

    def _param_key(self, sid: str) -> str:  # list of param json strings
        return f"{sid}:params"

    # ------------------- session lifecycle ----------------
    def get_or_create(self, session_id: Optional[str]) -> str:
        if session_id and self.r.exists(self._msg_key(session_id)):
            return session_id
        new_id = str(uuid.uuid4())
        # initialise empty redis lists
        self.r.rpush(self._msg_key(new_id), *[])  # create key
        return new_id

    # ------------------- message ops ----------------------
    def add(self, sid: str, role: str, content: str) -> None:
        self.r.rpush(self._msg_key(sid), json.dumps({"role": role, "content": content}))
        self._maybe_store_params(sid, content)

    def _load(self, sid: str) -> List[dict]:
        raw = self.r.lrange(self._msg_key(sid), 0, -1)
        return [json.loads(item) for item in raw]

    def as_prompt(self, sid: str) -> List[dict]:
        return [{"role": "system", "content": SYSTEM_PROMPT}] + self._load(sid)

    # ------------------- params tracking ------------------
    def _maybe_store_params(self, sid: str, message: str) -> None:
        match = PARAM_TAG_RE.search(message)
        if not match:
            return
        try:
            params: SearchParams = json.loads(match.group(1))
        except json.JSONDecodeError:
            return
        # ensure keys cover required fields
        if REQUIRED_FIELDS.issubset(params.keys()):
            self.r.rpush(self._param_key(sid), json.dumps(params, ensure_ascii=False))

    def latest_params(self, sid: str) -> Optional[SearchParams]:
        if not self.r.exists(self._param_key(sid)):
            return None
        return json.loads(self.r.lindex(self._param_key(sid), -1))

    # expose for history endpoint (returns list of dicts, not system prompt)
    def history(self, sid: str) -> List[dict]:
        return self._load(sid)


# ---------------------------------------------------------------------------
# PromptSecurityBarrier – unchanged except blacklist set
# ---------------------------------------------------------------------------
class PromptSecurityBarrier:
    _blacklist = {"hack", "jailbreak", "prompt injection", "ignore previous"}

    @classmethod
    def is_valid(cls, prompt: str) -> bool:
        lowered = prompt.lower()
        return not any(bad in lowered for bad in cls._blacklist)


# ---------------------------------------------------------------------------
# LLM Client – thin wrapper
# ---------------------------------------------------------------------------
class LLMClient:
    def __init__(self, endpoint: str = LLAMA_API_URL, model: str = "meta-llama/Llama-3.2-3B-Instruct"):
        self.endpoint = endpoint
        self.model = model

    def query(self, messages: list[dict]) -> str:
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.2,
            "max_tokens": 512,
        }
        r = requests.post(self.endpoint, json=payload, timeout=60)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
