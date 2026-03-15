"""Shared test fixtures for Dharma Agent."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from a2a.server.agent_execution import RequestContext
from a2a.server.events import EventQueue
from a2a.types import Message, MessageSendParams, Part, Role, TextPart


def make_request_context(
    text: str,
    context_id: str | None = None,
) -> RequestContext:
    """Create a RequestContext from a plain text string.

    Args:
        text: The user message text.
        context_id: Optional conversation session ID. If provided, allows
            multiple requests to share the same conversation history.
    """
    message = Message(
        role=Role.user,
        parts=[Part(root=TextPart(text=text))],
        messageId="test-msg-id",
        context_id=context_id,
    )
    params = MessageSendParams(message=message)
    return RequestContext(request=params)


@pytest.fixture
def mock_anthropic_client():
    """A mock Anthropic AsyncAnthropic client that returns canned text."""
    client = AsyncMock()
    response = MagicMock()
    response.content = [MagicMock(text="Mocked mindful response")]
    client.messages.create = AsyncMock(return_value=response)
    return client


@pytest.fixture
def event_queue():
    """A fresh EventQueue for test assertions."""
    return EventQueue()
