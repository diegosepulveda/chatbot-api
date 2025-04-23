# core/llm_client.py
import os
import requests

# Try to import the new OpenAI SDK client
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


class LLMClient:
    """
    Uses OpenAI if OPENAI_API_KEY is set (with OPENAI_BASE_URL);
    otherwise falls back to the local LLaMA API.
    """

    def __init__(
        self,
        local_endpoint: str | None = None,
        local_model: str | None = None,
        openai_model: str | None = None,
    ) -> None:
        # read env
        openai_key = os.getenv("OPENAI_API_KEY", "").strip()
        openai_base = os.getenv("OPENAI_BASE_URL", "https://api.llmapi.com/")
        self.openai_model = openai_model or os.getenv("OPENAI_MODEL", "llama3.2-3b")

        # configure local llama
        self.local_endpoint = local_endpoint or os.getenv("LLM_API_URL")
        self.local_model    = local_model    or os.getenv("LLM_MODEL", "meta-llama/Llama-3.2-3B-Instruct")

        # decide which to use
        if openai_key:
            if OpenAI is None:
                raise ImportError(
                    "OPENAI_API_KEY is set but the OpenAI SDK is not installed. "
                    "Please `pip install openai`."
                )
            self.use_openai = True
            # **pass the same base_url** you used in your standalone snippet
            self.openai_client = OpenAI(
                api_key=openai_key,
                base_url=openai_base
            )
        else:
            self.use_openai = False

    def query(self, messages: list[dict]) -> str:
        """
        messages: List of {"role": "...", "content": "..."} dicts
        """
        if self.use_openai:
            # exactly like your working snippet
            chat_completion = self.openai_client.chat.completions.create(
                model=self.openai_model,
                messages=messages,
                stream=False
            )
            # SDK returns .choices[0].message.content
            return chat_completion.choices[0].message.content

        # fallback to local llama
        payload = {
            "model": self.local_model,
            "messages": messages,
            "temperature": 0.1,
            "max_tokens": 512,
        }
        resp = requests.post(self.local_endpoint, json=payload, timeout=60)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
