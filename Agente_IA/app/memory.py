from __future__ import annotations

from collections import defaultdict, deque
from threading import Lock
from typing import Any


class ConversationMemory:
    """Memoria corta en RAM, aislada por session_id."""

    def __init__(self, max_messages: int = 12) -> None:
        self._max_messages = max_messages
        self._sessions: dict[str, deque[Any]] = defaultdict(
            lambda: deque(maxlen=self._max_messages)
        )
        self._lock = Lock()

    def get(self, session_id: str) -> list[Any]:
        with self._lock:
            return list(self._sessions[session_id])

    def add_many(self, session_id: str, messages: list[Any]) -> None:
        with self._lock:
            self._sessions[session_id].extend(messages)

    def clear(self, session_id: str) -> None:
        with self._lock:
            self._sessions.pop(session_id, None)
