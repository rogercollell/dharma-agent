"""Tests for the Dharma Agent executor — routing, error handling, streaming, memory."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

import anthropic
from a2a.server.events import EventQueue
from a2a.types import Message, TaskStatusUpdateEvent, TaskState

from dharma_agent.conversation import InMemoryConversationStore
from dharma_agent.executor import _detect_skill, DharmaAgentExecutor
from tests.conftest import make_request_context


# ---------------------------------------------------------------------------
# Skill routing
# ---------------------------------------------------------------------------


class TestDetectSkill:
    """Tests for keyword-based skill routing."""

    def test_teach_keywords(self):
        assert _detect_skill("Explain the first training") == "teach"
        assert _detect_skill("What are the Five Trainings?") == "teach"
        assert _detect_skill("Tell me about True Love") == "teach"
        assert _detect_skill("Describe reverence for life") == "teach"

    def test_guide_keywords(self):
        assert _detect_skill("Should I send this angry email?") == "guide"
        assert _detect_skill("I want to quit my job") == "guide"
        assert _detect_skill("I'm thinking of cutting someone out") == "guide"
        assert _detect_skill("Is it okay to lie here?") == "guide"

    def test_default_to_reflect(self):
        assert _detect_skill("I feel overwhelmed") == "reflect"
        assert _detect_skill("Life is hard lately") == "reflect"
        assert _detect_skill("Hello") == "reflect"


# ---------------------------------------------------------------------------
# Fallback mode (no Anthropic client)
# ---------------------------------------------------------------------------


def _make_executor(client=None, store=None):
    """Create executor without calling __init__, injecting client and store."""
    executor = DharmaAgentExecutor.__new__(DharmaAgentExecutor)
    executor._client = client
    executor._store = store or InMemoryConversationStore()
    return executor


class TestExecutorFallbackMode:
    """Tests for executor with no Anthropic client (fallback mode)."""

    @pytest.mark.asyncio
    async def test_teach_fallback_returns_training_text(self):
        executor = _make_executor()
        queue = EventQueue()
        ctx = make_request_context("Explain the first training")
        await executor.execute(ctx, queue)

        # Should get: working → message → completed
        event1 = await queue.dequeue_event(no_wait=True)
        assert isinstance(event1, TaskStatusUpdateEvent)
        assert event1.status.state == TaskState.working

        event2 = await queue.dequeue_event(no_wait=True)
        assert isinstance(event2, Message)
        text = event2.parts[0].root.text
        assert "Reverence For Life" in text

        event3 = await queue.dequeue_event(no_wait=True)
        assert isinstance(event3, TaskStatusUpdateEvent)
        assert event3.status.state == TaskState.completed
        assert event3.final is True

    @pytest.mark.asyncio
    async def test_empty_input_returns_welcome(self):
        executor = _make_executor()
        queue = EventQueue()
        ctx = make_request_context("   ")
        await executor.execute(ctx, queue)

        event1 = await queue.dequeue_event(no_wait=True)
        assert isinstance(event1, Message)
        assert "ready" in event1.parts[0].root.text.lower()

        event2 = await queue.dequeue_event(no_wait=True)
        assert isinstance(event2, TaskStatusUpdateEvent)
        assert event2.status.state == TaskState.completed

    @pytest.mark.asyncio
    async def test_reflect_fallback(self):
        executor = _make_executor()
        queue = EventQueue()
        ctx = make_request_context("I feel so lost")
        await executor.execute(ctx, queue)

        await queue.dequeue_event(no_wait=True)  # working
        event = await queue.dequeue_event(no_wait=True)
        assert isinstance(event, Message)
        assert "compassion" in event.parts[0].root.text.lower() or "trainings" in event.parts[0].root.text.lower()

    @pytest.mark.asyncio
    async def test_guide_fallback(self):
        executor = _make_executor()
        queue = EventQueue()
        ctx = make_request_context("Should I quit my job?")
        await executor.execute(ctx, queue)

        await queue.dequeue_event(no_wait=True)  # working
        event = await queue.dequeue_event(no_wait=True)
        assert isinstance(event, Message)
        assert "trainings" in event.parts[0].root.text.lower() or "mindful" in event.parts[0].root.text.lower()


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------


class TestExecutorErrorHandling:
    """Tests for error handling when Claude API fails."""

    @pytest.mark.asyncio
    async def test_api_connection_error(self):
        client = AsyncMock()
        client.messages.create = AsyncMock(
            side_effect=anthropic.APIConnectionError(request=MagicMock())
        )
        executor = _make_executor(client)
        queue = EventQueue()
        ctx = make_request_context("Explain the trainings")
        await executor.execute(ctx, queue)

        # working event
        event1 = await queue.dequeue_event(no_wait=True)
        assert isinstance(event1, TaskStatusUpdateEvent)
        assert event1.status.state == TaskState.working

        # failed event with compassionate message
        event2 = await queue.dequeue_event(no_wait=True)
        assert isinstance(event2, TaskStatusUpdateEvent)
        assert event2.status.state == TaskState.failed
        assert event2.final is True
        assert "trouble" in event2.status.message.parts[0].root.text.lower()

    @pytest.mark.asyncio
    async def test_rate_limit_error(self):
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.headers = {}
        client = AsyncMock()
        client.messages.create = AsyncMock(
            side_effect=anthropic.RateLimitError(
                message="rate limited",
                response=mock_response,
                body=None,
            )
        )
        executor = _make_executor(client)
        queue = EventQueue()
        ctx = make_request_context("I feel overwhelmed")
        await executor.execute(ctx, queue)

        await queue.dequeue_event(no_wait=True)  # working
        event = await queue.dequeue_event(no_wait=True)
        assert isinstance(event, TaskStatusUpdateEvent)
        assert event.status.state == TaskState.failed
        assert "rest" in event.status.message.parts[0].root.text.lower()

    @pytest.mark.asyncio
    async def test_authentication_error(self):
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.headers = {}
        client = AsyncMock()
        client.messages.create = AsyncMock(
            side_effect=anthropic.AuthenticationError(
                message="invalid key",
                response=mock_response,
                body=None,
            )
        )
        executor = _make_executor(client)
        queue = EventQueue()
        ctx = make_request_context("Explain the trainings")
        await executor.execute(ctx, queue)

        await queue.dequeue_event(no_wait=True)  # working
        event = await queue.dequeue_event(no_wait=True)
        assert isinstance(event, TaskStatusUpdateEvent)
        assert event.status.state == TaskState.failed
        assert "configuration" in event.status.message.parts[0].root.text.lower()

    @pytest.mark.asyncio
    async def test_unexpected_exception(self):
        client = AsyncMock()
        client.messages.create = AsyncMock(side_effect=RuntimeError("boom"))
        executor = _make_executor(client)
        queue = EventQueue()
        ctx = make_request_context("Guide me please")
        await executor.execute(ctx, queue)

        await queue.dequeue_event(no_wait=True)  # working
        event = await queue.dequeue_event(no_wait=True)
        assert isinstance(event, TaskStatusUpdateEvent)
        assert event.status.state == TaskState.failed
        assert "unexpected" in event.status.message.parts[0].root.text.lower()


# ---------------------------------------------------------------------------
# Cancel
# ---------------------------------------------------------------------------


class TestExecutorCancel:
    """Tests for cancel behavior."""

    @pytest.mark.asyncio
    async def test_cancel_enqueues_canceled_state(self):
        executor = _make_executor()
        queue = EventQueue()
        ctx = make_request_context("")
        await executor.cancel(ctx, queue)

        event = await queue.dequeue_event(no_wait=True)
        assert isinstance(event, TaskStatusUpdateEvent)
        assert event.status.state == TaskState.canceled
        assert event.final is True
        assert "canceled" in event.status.message.parts[0].root.text.lower()


# ---------------------------------------------------------------------------
# Conversation memory
# ---------------------------------------------------------------------------


class TestExecutorMemory:
    """Tests for conversation memory across messages."""

    @pytest.mark.asyncio
    async def test_second_message_has_history(self):
        """Second message in the same session receives history from the first."""
        store = InMemoryConversationStore()
        executor = _make_executor(store=store)
        session_id = "test-session-1"

        # First message
        ctx1 = make_request_context("Explain the first training", context_id=session_id)
        queue1 = EventQueue()
        await executor.execute(ctx1, queue1)

        # Verify history was recorded (user turn + assistant turn)
        history = await store.get_history(session_id)
        assert len(history) == 2
        assert history[0].role == "user"
        assert history[0].content == "Explain the first training"
        assert history[1].role == "assistant"
        assert "Reverence For Life" in history[1].content

        # Second message — should receive the history from message 1
        ctx2 = make_request_context("How does that apply to anger?", context_id=session_id)
        queue2 = EventQueue()

        # Patch the reflect handler to capture the history argument
        with patch("dharma_agent.executor.handle_reflect") as mock_handler:
            mock_handler.return_value = "A mindful response about anger."
            await executor.execute(ctx2, queue2)
            mock_handler.assert_awaited_once()
            call_kwargs = mock_handler.call_args
            passed_history = call_kwargs.kwargs.get("history") or call_kwargs[1].get("history")
            assert passed_history is not None
            assert len(passed_history) == 2  # from message 1

    @pytest.mark.asyncio
    async def test_different_contexts_isolated(self):
        """Different context_ids produce independent conversation histories."""
        store = InMemoryConversationStore()
        executor = _make_executor(store=store)

        # Session A
        ctx_a = make_request_context("Explain the trainings", context_id="session-a")
        await executor.execute(ctx_a, EventQueue())

        # Session B
        ctx_b = make_request_context("I feel lost", context_id="session-b")
        await executor.execute(ctx_b, EventQueue())

        history_a = await store.get_history("session-a")
        history_b = await store.get_history("session-b")

        assert len(history_a) == 2  # user + assistant
        assert len(history_b) == 2
        assert "trainings" in history_a[0].content.lower()
        assert "lost" in history_b[0].content.lower()

    @pytest.mark.asyncio
    async def test_error_not_recorded_in_history(self):
        """When the skill handler raises, the error is NOT stored as a turn."""
        client = AsyncMock()
        client.messages.create = AsyncMock(side_effect=RuntimeError("boom"))
        store = InMemoryConversationStore()
        executor = _make_executor(client=client, store=store)

        ctx = make_request_context("Explain the trainings", context_id="err-session")
        await executor.execute(ctx, EventQueue())

        history = await store.get_history("err-session")
        # Only the user turn should be recorded, not an error "assistant" turn
        assert len(history) == 1
        assert history[0].role == "user"
