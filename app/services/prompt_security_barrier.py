
import re
import html
class PromptSecurityBarrier:

    @staticmethod
    def sanitize(prompt: str) -> str:
        """
        Sanitize user input to reduce prompt injection risk.
        - Removes dangerous sequences like backticks, triple quotes, <script> tags.
        - Escapes potentially risky characters.
        """
        # Remove backticks and triple quotes
        prompt = re.sub(r"[`\"']{3,}", "", prompt)
        # Remove <script> tags or other HTML blocks
        prompt = re.sub(r"<\s*script.*?>.*?<\s*/\s*script\s*>", "", prompt, flags=re.IGNORECASE | re.DOTALL)
        prompt = re.sub(r"<[^>]*>", "", prompt)  # strip any other HTML tags

        # Remove 'role:', 'system:' fragments (case insensitive)
        prompt = re.sub(r"\b(role|system)\s*:\s*", "", prompt, flags=re.IGNORECASE)

        # Escape any remaining angle brackets
        prompt = html.escape(prompt)

        return prompt