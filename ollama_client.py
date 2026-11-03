"""Optional local Ollama client used to improve grounded response wording."""

from __future__ import annotations

import json
import os
import re
from urllib.error import URLError
from urllib.request import Request, urlopen


class OllamaClient:
    """Small dependency-free client for Ollama's local generate endpoint."""

    def __init__(
        self,
        model: str | None = None,
        base_url: str | None = None,
        timeout: float = 60.0,
    ) -> None:
        self.model = model or os.getenv("OLLAMA_MODEL", "llama3.2:latest")
        self.base_url = (base_url or os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")).rstrip("/")
        self.timeout = timeout

    def generate(self, user_message: str, grounded_answer: str) -> str | None:
        if re.search(r"\d", grounded_answer) or "não entendi" in grounded_answer.lower():
            return None

        prompt = (
            "You are the customer service assistant for Empório da Música. "
            "Answer in Brazilian Portuguese. Rewrite the grounded answer below "
            "to be clear and friendly. Do not add facts, prices, addresses, "
            "policies, or availability that are not present in the grounded answer. "
            "If the grounded answer says the information is unavailable, keep that limitation.\n\n"
            f"Customer question:\n{user_message}\n\n"
            f"Grounded answer:\n{grounded_answer}"
        )
        payload = json.dumps(
            {"model": self.model, "prompt": prompt, "stream": False}
        ).encode("utf-8")
        request = Request(
            f"{self.base_url}/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                body = json.loads(response.read().decode("utf-8"))
        except (OSError, URLError, TimeoutError, json.JSONDecodeError):
            return None

        answer = body.get("response")
        if not isinstance(answer, str) or not answer.strip():
            return None
        answer = answer.strip()
        return answer
