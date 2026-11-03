"""Persistência de histórico de conversa.

Salva cada troca (usuário → agente) em um arquivo JSON simples,
permitindo que o agente retome o contexto em sessões futuras.
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any


class ConversationHistory:
    """Armazena o histórico de uma conversa em disco."""

    def __init__(self, path: str | None = None):
        if path is None:
            path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "conversation_history.json"
            )
        self.path = path
        self._ensure_file()

    def _ensure_file(self) -> None:
        if not os.path.exists(self.path):
            with open(self.path, "w", encoding="utf-8") as fh:
                json.dump([], fh, ensure_ascii=False, indent=2)

    def _read(self) -> list[dict[str, Any]]:
        try:
            with open(self.path, encoding="utf-8") as fh:
                return json.load(fh)
        except (json.JSONDecodeError, OSError):
            return []

    def _write(self, records: list[dict[str, Any]]) -> None:
        tmp = self.path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(records, fh, ensure_ascii=False, indent=2)
        os.replace(tmp, self.path)

    def add(self, user_message: str, agent_response: str) -> None:
        """Registra uma troca na conversa."""
        records = self._read()
        records.append(
            {
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                "user": user_message,
                "agent": agent_response,
            }
        )
        # Mantém apenas as últimas 100 trocas para não crescer indefinidamente
        records = records[-100:]
        self._write(records)

    def get_recent(self, limit: int = 5) -> list[dict[str, str]]:
        """Retorna as últimas trocas (para contexto do modelo)."""
        records = self._read()
        return records[-limit:]

    def clear(self) -> None:
        """Limpa o histórico."""
        self._write([])

    def count(self) -> int:
        """Retorna a quantidade de trocas armazenadas."""
        return len(self._read())
