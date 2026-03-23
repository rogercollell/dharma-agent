"""Session-scoped conversation memory."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Turn:
    """A single turn in a conversation."""

    role: str
    content: str
    kind: str = "message"
    metadata: dict[str, Any] = field(default_factory=dict)


class ConversationStore(ABC):
    """Abstract session history store."""

    @abstractmethod
    async def add_turn(self, session_id: str, turn: Turn) -> None:
        """Append a turn to the session history."""

    @abstractmethod
    async def get_history(self, session_id: str) -> list[Turn]:
        """Return all turns for the session."""

    @abstractmethod
    async def clear(self, session_id: str) -> None:
        """Remove session history."""


class InMemoryConversationStore(ConversationStore):
    """Simple in-memory session store."""

    def __init__(self) -> None:
        self._sessions: dict[str, list[Turn]] = {}

    async def add_turn(self, session_id: str, turn: Turn) -> None:
        self._sessions.setdefault(session_id, []).append(turn)

    async def get_history(self, session_id: str) -> list[Turn]:
        return list(self._sessions.get(session_id, []))

    async def clear(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)
