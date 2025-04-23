from __future__ import annotations
from typing import Dict, Any, Optional
from urllib.parse import urlencode
import json, re
from app.config import FRONTEND_URL

class QueryParameters:
    """Parse and hold user‑supplied parameters; build URL when complete."""

    required_fields = {"budget", "size", "type", "city"}

    def __init__(self, data: Optional[Dict[str, Any]] = None) -> None:
        data = data or {}
        self.budget: Optional[str] = data.get("budget")
        self.size: Optional[str] = data.get("size")
        self.type: Optional[str] = data.get("type")
        self.city: Optional[str] = data.get("city")
        # store any future/extra keys transparently
        self.extra: Dict[str, Any] = {k: v for k, v in data.items() if k not in self.required_fields}

    # ----------- helpers -----------
    @classmethod
    def from_llm_text(cls, text: str) -> "QueryParameters | None":
        """Extract first JSON object from an LLM reply. Returns None if not found/invalid."""
        import re, json  # local import to avoid global cost
        try:
            match = re.search(r"\{.*?\}", text, re.S)
            if not match:
                return None
            data = json.loads(match.group())
            return cls(data)
        except json.JSONDecodeError:
            return None

    def update(self, key: str, value: str) -> None:
        if key in self.required_fields:
            setattr(self, key, value)
        else:
            self.extra[key] = value

    def is_complete(self) -> bool:
        return all(getattr(self, f) for f in self.required_fields)

    def to_dict(self) -> Dict[str, Any]:
        base = {"budget": self.budget, "size": self.size, "type": self.type, "city": self.city}
        base.update(self.extra)
        return base

    def to_query_url(self) -> str:
        from urllib.parse import urlencode
        from os import getenv

        return f"{FRONTEND_URL}/search?" + urlencode(self.to_dict())