"""Conversation memory — session-scoped history for multi-turn dialogue."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class Turn:
    """A single turn in a conversation."""

    role: str  # "user" or "assistant"
    content: str


class ConversationStore(ABC):
    """Abstract conversation store.

    Swap implementations (in-memory → SQLite → Redis) without changing callers.
    """

    @abstractmethod
    async def add_turn(self, session_id: str, turn: Turn) -> None:
        """Append a turn to the session's history."""

    @abstractmethod
    async def get_history(self, session_id: str) -> list[Turn]:
        """Return all turns for this session (empty list if new)."""

    @abstractmethod
    async def clear(self, session_id: str) -> None:
        """Remove all history for this session."""


class InMemoryConversationStore(ConversationStore):
    """Session-scoped store — data lost on restart.

    Designed so a persistent backend can be substituted later.
    """

    def __init__(self) -> None:
        self._sessions: dict[str, list[Turn]] = {}

    async def add_turn(self, session_id: str, turn: Turn) -> None:
        if session_id not in self._sessions:
            self._sessions[session_id] = []
        self._sessions[session_id].append(turn)

    async def get_history(self, session_id: str) -> list[Turn]:
        return list(self._sessions.get(session_id, []))

    async def clear(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)


def build_messages(
    history: list[Turn] | None,
    user_message: str,
) -> list[dict[str, str]]:
    """Convert conversation history + current message into Anthropic messages format.

    Returns a list of {"role": ..., "content": ...} dicts ready to pass to
    ``client.messages.create(messages=...)``.
    """
    messages: list[dict[str, str]] = []
    if history:
        for turn in history:
            messages.append({"role": turn.role, "content": turn.content})
    messages.append({"role": "user", "content": user_message})
    return messages
