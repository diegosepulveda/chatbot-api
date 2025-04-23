
import json
import os
import uuid
from typing import Optional, Dict, Any, List
import redis
from fastapi import Cookie, Response
from dotenv import load_dotenv
from system_prompt import SYSTEM_PROMPT
from app.services.query_parameters import QueryParameters

class ChatSessionManager:
    """
    Redis-backed chat history + query history per session_id.
    """
    def __init__(self, redis_instance: redis.StrictRedis) -> None:
        self.r = redis_instance

    def get_or_create(self, session_id: Optional[str]) -> str:
        if session_id and self.r.exists(session_id):
            return session_id
        new_id = str(uuid.uuid4())
        self.r.set(session_id := new_id, json.dumps([]))
        self.r.set(f"{session_id}:queries", json.dumps([]))
        return session_id

    def add_message(self, session_id: str, role: str, content: str) -> None:
        messages = self._load(messages_key := session_id)
        messages.append({"role": role, "content": content})
        self.r.set(messages_key, json.dumps(messages, ensure_ascii=False))

    def as_prompt(self, session_id: str) -> List[dict]:
        return [{"role": "system", "content": SYSTEM_PROMPT}] + self._load(session_id)

    def _load(self, key: str) -> List[dict]:
        raw = self.r.get(key)
        return json.loads(raw) if raw else []

    def record_query(self, session_id: str, params: QueryParameters) -> None:
        key = f"{session_id}:queries"
        queries = self._load(key)
        queries.append(params.to_dict())
        self.r.set(key, json.dumps(queries, ensure_ascii=False))

    def get_queries(self, session_id: str) -> List[Dict[str, Any]]:
        return json.loads(self.r.get(f"{session_id}:queries") or "[]")