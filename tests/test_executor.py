"""Tests for the Dharma Agent executor."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

import anthropic
from a2a.server.events import EventQueue
from a2a.types import Message, TaskState, TaskStatusUpdateEvent

from dharma_agent.contracts import WisdomResult
from dharma_agent.conversation import InMemoryConversationStore
from dharma_agent.executor import _detect_skill, DharmaAgentExecutor
from dharma_agent.memory.pattern_store import InMemoryPatternStore
from dharma_agent.memory.profile_store import InMemoryProfileStore
from tests.conftest import make_request_context


def _make_executor(client=None, store=None):
    """Create executor without calling __init__, injecting stores directly."""
    executor = DharmaAgentExecutor.__new__(DharmaAgentExecutor)
    executor._client = client
    executor._store = store or InMemoryConversationStore()
    executor._profile_store = InMemoryProfileStore()
    executor._pattern_store = InMemoryPatternStore()
    return executor


class TestDetectSkill:
    """Tests for keyword-based skill routing."""

    def test_teach_keywords(self):
        assert _detect_skill("Explain the first training") == "teach"
        assert _detect_skill("What are the Five Trainings?") == "teach"

    def test_review_keywords(self):
        assert _detect_skill("Should I send this angry email?") == "review"
        assert _detect_skill("Review this note before I send it") == "review"

    def test_respond_keywords(self):
        assert _detect_skill("Help me reply to this message") == "respond"
        assert _detect_skill("Rewrite this text more calmly") == "respond"

    def test_default_to_reflect(self):
        assert _detect_skill("I feel overwhelmed") == "reflect"
        assert _detect_skill("Life is hard lately") == "reflect"


class TestExecutorFallbackMode:
    """Tests for fallback mode with structured rendering."""

    @pytest.mark.asyncio
    async def test_teach_fallback_returns_rendered_result(self):
        executor = _make_executor()
        queue = EventQueue()
        ctx = make_request_context("Explain the first training")
        await executor.execute(ctx, queue)

        event1 = await queue.dequeue_event(no_wait=True)
        assert isinstance(event1, TaskStatusUpdateEvent)
        assert event1.status.state == TaskState.working

        event2 = await queue.dequeue_event(no_wait=True)
        assert isinstance(event2, Message)
        text = event2.parts[0].root.text
        assert "Reverence For Life" in text
        assert "Next step:" in text

        event3 = await queue.dequeue_event(no_wait=True)
        assert isinstance(event3, TaskStatusUpdateEvent)
        assert event3.status.state == TaskState.completed

    @pytest.mark.asyncio
    async def test_reflect_fallback(self):
        executor = _make_executor()
        queue = EventQueue()
        ctx = make_request_context("I feel so lost")
        await executor.execute(ctx, queue)

        await queue.dequeue_event(no_wait=True)  # working
        event = await queue.dequeue_event(no_wait=True)
        assert isinstance(event, Message)
        text = event.parts[0].root.text
        assert "Thank you for sharing" in text
        assert "Question:" in text

    @pytest.mark.asyncio
    async def test_review_fallback(self):
        executor = _make_executor()
        queue = EventQueue()
        ctx = make_request_context("Should I quit my job?")
        await executor.execute(ctx, queue)

        await queue.dequeue_event(no_wait=True)  # working
        event = await queue.dequeue_event(no_wait=True)
        assert isinstance(event, Message)
        text = event.parts[0].root.text
        assert "Risks to watch:" in text
        assert "Next step:" in text


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
        await executor.execute(make_request_context("Explain the trainings"), queue)

        await queue.dequeue_event(no_wait=True)  # working
        event = await queue.dequeue_event(no_wait=True)
        assert isinstance(event, TaskStatusUpdateEvent)
        assert event.status.state == TaskState.failed
        assert "trouble" in event.status.message.parts[0].root.text.lower()

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
        await executor.execute(make_request_context("I feel overwhelmed"), queue)

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
        await executor.execute(make_request_context("Explain the trainings"), queue)

        await queue.dequeue_event(no_wait=True)  # working
        event = await queue.dequeue_event(no_wait=True)
        assert isinstance(event, TaskStatusUpdateEvent)
        assert event.status.state == TaskState.failed
        assert "configuration" in event.status.message.parts[0].root.text.lower()


class TestExecutorMemory:
    """Tests for session history and learning feedback."""

    @pytest.mark.asyncio
    async def test_second_message_has_history(self):
        store = InMemoryConversationStore()
        executor = _make_executor(store=store)
        session_id = "test-session-1"

        await executor.execute(
            make_request_context("Explain the first training", context_id=session_id),
            EventQueue(),
        )

        history = await store.get_history(session_id)
        assert len(history) == 2
        assert history[0].role == "user"
        assert history[1].metadata["skill_id"] == "teach"

        with patch(
            "dharma_agent.executor.handle_reflect",
            new=AsyncMock(return_value=WisdomResult(insight="A mindful response.")),
        ) as mock_handler:
            await executor.execute(
                make_request_context("How does that apply to anger?", context_id=session_id),
                EventQueue(),
            )
            passed_history = mock_handler.await_args.kwargs["history"]
            assert len(passed_history) == 2

    @pytest.mark.asyncio
    async def test_different_contexts_isolated(self):
        store = InMemoryConversationStore()
        executor = _make_executor(store=store)

        await executor.execute(
            make_request_context("Explain the trainings", context_id="session-a"),
            EventQueue(),
        )
        await executor.execute(
            make_request_context("I feel lost", context_id="session-b"),
            EventQueue(),
        )

        history_a = await store.get_history("session-a")
        history_b = await store.get_history("session-b")

        assert len(history_a) == 2
        assert len(history_b) == 2
        assert "trainings" in history_a[0].content.lower()
        assert "lost" in history_b[0].content.lower()

    @pytest.mark.asyncio
    async def test_outcome_updates_profile_and_patterns(self):
        executor = _make_executor()
        session_id = "feedback-loop"

        await executor.execute(
            make_request_context("Help me reply to this message", context_id=session_id),
            EventQueue(),
        )
        queue = EventQueue()
        await executor.execute(
            make_request_context("That helped a lot", context_id=session_id),
            queue,
        )

        await queue.dequeue_event(no_wait=True)  # working
        event = await queue.dequeue_event(no_wait=True)
        assert isinstance(event, Message)
        assert "useful pattern" in event.parts[0].root.text.lower()

        profile = await executor._profile_store.get(session_id)
        patterns = await executor._pattern_store.list_for_memory(session_id)
        assert profile.last_outcome == "helpful"
        assert patterns
        assert patterns[0].success_count == 1

    @pytest.mark.asyncio
    async def test_error_not_recorded_as_assistant_turn(self):
        client = AsyncMock()
        client.messages.create = AsyncMock(side_effect=RuntimeError("boom"))
        store = InMemoryConversationStore()
        executor = _make_executor(client=client, store=store)

        session_id = "err-session"
        await executor.execute(
            make_request_context("Explain the trainings", context_id=session_id),
            EventQueue(),
        )

        history = await store.get_history(session_id)
        assert len(history) == 1
        assert history[0].role == "user"


class TestExecutorCancel:
    """Tests for cancel behavior."""

    @pytest.mark.asyncio
    async def test_cancel_enqueues_canceled_state(self):
        executor = _make_executor()
        queue = EventQueue()
        await executor.cancel(make_request_context(""), queue)

        event = await queue.dequeue_event(no_wait=True)
        assert isinstance(event, TaskStatusUpdateEvent)
        assert event.status.state == TaskState.canceled
        assert "canceled" in event.status.message.parts[0].root.text.lower()
