"""Conversation helpers and compatibility exports."""

from __future__ import annotations

from dharma_agent.memory.session_store import (
    ConversationStore,
    InMemoryConversationStore,
    Turn,
)


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
