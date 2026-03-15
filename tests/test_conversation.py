"""Tests for conversation memory store and message building."""

import pytest

from dharma_agent.conversation import (
    Turn,
    InMemoryConversationStore,
    build_messages,
)


# ---------------------------------------------------------------------------
# InMemoryConversationStore
# ---------------------------------------------------------------------------


class TestInMemoryConversationStore:
    """Tests for the in-memory conversation store."""

    @pytest.mark.asyncio
    async def test_add_and_retrieve(self):
        store = InMemoryConversationStore()
        await store.add_turn("s1", Turn("user", "Hello"))
        await store.add_turn("s1", Turn("assistant", "Hi there"))
        history = await store.get_history("s1")
        assert len(history) == 2
        assert history[0].role == "user"
        assert history[0].content == "Hello"
        assert history[1].role == "assistant"
        assert history[1].content == "Hi there"

    @pytest.mark.asyncio
    async def test_empty_history(self):
        store = InMemoryConversationStore()
        history = await store.get_history("nonexistent")
        assert history == []

    @pytest.mark.asyncio
    async def test_multiple_sessions_isolated(self):
        store = InMemoryConversationStore()
        await store.add_turn("s1", Turn("user", "Message for session 1"))
        await store.add_turn("s2", Turn("user", "Message for session 2"))
        h1 = await store.get_history("s1")
        h2 = await store.get_history("s2")
        assert len(h1) == 1
        assert len(h2) == 1
        assert h1[0].content == "Message for session 1"
        assert h2[0].content == "Message for session 2"

    @pytest.mark.asyncio
    async def test_clear(self):
        store = InMemoryConversationStore()
        await store.add_turn("s1", Turn("user", "Hello"))
        await store.add_turn("s2", Turn("user", "Hi"))
        await store.clear("s1")
        assert await store.get_history("s1") == []
        assert len(await store.get_history("s2")) == 1  # unaffected

    @pytest.mark.asyncio
    async def test_history_is_copy(self):
        store = InMemoryConversationStore()
        await store.add_turn("s1", Turn("user", "Hello"))
        history = await store.get_history("s1")
        history.append(Turn("assistant", "Injected"))
        # Original should be unaffected
        assert len(await store.get_history("s1")) == 1


# ---------------------------------------------------------------------------
# build_messages
# ---------------------------------------------------------------------------


class TestBuildMessages:
    """Tests for the Anthropic messages format builder."""

    def test_no_history(self):
        messages = build_messages(None, "Hello")
        assert messages == [{"role": "user", "content": "Hello"}]

    def test_empty_history(self):
        messages = build_messages([], "Hello")
        assert messages == [{"role": "user", "content": "Hello"}]

    def test_with_history(self):
        history = [
            Turn("user", "First question"),
            Turn("assistant", "First answer"),
        ]
        messages = build_messages(history, "Follow-up")
        assert len(messages) == 3
        assert messages[0] == {"role": "user", "content": "First question"}
        assert messages[1] == {"role": "assistant", "content": "First answer"}
        assert messages[2] == {"role": "user", "content": "Follow-up"}

    def test_multi_turn_history(self):
        history = [
            Turn("user", "Q1"),
            Turn("assistant", "A1"),
            Turn("user", "Q2"),
            Turn("assistant", "A2"),
        ]
        messages = build_messages(history, "Q3")
        assert len(messages) == 5
        assert messages[-1] == {"role": "user", "content": "Q3"}
