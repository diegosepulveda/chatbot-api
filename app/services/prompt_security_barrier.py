# core/prompt_guard.py
class PromptSecurityBarrier:
    _blacklist = {"hack", "jailbreak", "prompt injection", "ignore previous"}

    @classmethod
    def is_valid(cls, prompt: str) -> bool:
        lowered = prompt.lower()
        return not any(bad in lowered for bad in cls._blacklist)
