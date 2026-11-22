"""Provedor local: Ollama (os dados não saem da máquina)."""

from __future__ import annotations

from typing import Any

from challenge.ai.base import HttpLLMClient, LLMError

DEFAULT_MODEL = "llama3.1:8b"
DEFAULT_URL = "http://localhost:11434"


class OllamaClient(HttpLLMClient):
    """Cliente da API ``/api/chat`` do Ollama com saída em JSON e temperatura 0."""

    name = "ollama"

    def _complete_text(self, system: str, user: str) -> str:
        payload: dict[str, Any] = {
            "model": self.model,
            "stream": False,
            "format": "json",
            "options": {"temperature": 0},
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        body = self._post(f"{self._base_url}/api/chat", payload)
        try:
            return str(body["message"]["content"])
        except (KeyError, TypeError) as exc:
            raise LLMError(f"Formato Ollama inesperado: {list(body)}") from exc
