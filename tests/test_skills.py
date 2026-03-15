"""Tests for individual skill handlers."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from dharma_agent.conversation import Turn
from dharma_agent.skills.teach import handle_teach, _fallback_teach
from dharma_agent.skills.reflect import handle_reflect
from dharma_agent.skills.guide import handle_guide


# ---------------------------------------------------------------------------
# Teach fallback (detailed — has the most logic)
# ---------------------------------------------------------------------------


class TestTeachFallback:
    """Tests for teach skill static fallback responses."""

    def test_specific_training_by_number(self):
        result = _fallback_teach("Tell me about training 1")
        assert "Reverence For Life" in result
        assert "First" in result

    def test_specific_training_by_name(self):
        result = _fallback_teach("What is true love?")
        assert "True Love" in result

    def test_deep_listening_by_name(self):
        result = _fallback_teach("Tell me about deep listening")
        assert "Loving Speech" in result

    def test_all_trainings_default(self):
        result = _fallback_teach("What are the trainings?")
        assert "Reverence For Life" in result
        assert "True Happiness" in result
        assert "True Love" in result
        assert "Loving Speech" in result
        assert "Nourishment and Healing" in result


# ---------------------------------------------------------------------------
# Skills with mocked Anthropic client
# ---------------------------------------------------------------------------


def _mock_client(response_text: str):
    client = AsyncMock()
    response = MagicMock()
    response.content = [MagicMock(text=response_text)]
    client.messages.create = AsyncMock(return_value=response)
    return client


class TestSkillsWithClient:
    """Tests for skill handlers with a mocked Anthropic client."""

    @pytest.mark.asyncio
    async def test_teach_calls_claude(self):
        client = _mock_client("Here is the teaching...")
        result = await handle_teach("Explain the first training", client)
        assert result == "Here is the teaching..."
        client.messages.create.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_reflect_calls_claude(self):
        client = _mock_client("Here is my reflection...")
        result = await handle_reflect("I am struggling", client)
        assert result == "Here is my reflection..."
        client.messages.create.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_guide_calls_claude(self):
        client = _mock_client("Consider this alternative...")
        result = await handle_guide("Should I send this angry email?", client)
        assert result == "Consider this alternative..."
        client.messages.create.assert_awaited_once()


# ---------------------------------------------------------------------------
# Skills in fallback mode (client=None)
# ---------------------------------------------------------------------------


class TestSkillsFallbackMode:
    """Tests for all skills when no client is available."""

    @pytest.mark.asyncio
    async def test_teach_fallback(self):
        result = await handle_teach("What are the trainings?", None)
        assert "Five Mindfulness Trainings" in result

    @pytest.mark.asyncio
    async def test_reflect_fallback(self):
        result = await handle_reflect("I am angry", None)
        assert "compassion" in result.lower()

    @pytest.mark.asyncio
    async def test_guide_fallback(self):
        result = await handle_guide("Should I quit?", None)
        assert "trainings" in result.lower()


# ---------------------------------------------------------------------------
# Skills with conversation history
# ---------------------------------------------------------------------------


class TestSkillsWithHistory:
    """Tests for skill handlers passing conversation history to Claude."""

    @pytest.mark.asyncio
    async def test_teach_passes_history_to_claude(self):
        client = _mock_client("Follow-up teaching...")
        history = [
            Turn("user", "Tell me about the first training"),
            Turn("assistant", "The first training is Reverence For Life..."),
        ]
        result = await handle_teach("How does that apply to anger?", client, history=history)
        assert result == "Follow-up teaching..."

        call_kwargs = client.messages.create.call_args.kwargs
        messages = call_kwargs["messages"]
        assert len(messages) == 3  # 2 history + 1 current
        assert messages[0] == {"role": "user", "content": "Tell me about the first training"}
        assert messages[1] == {"role": "assistant", "content": "The first training is Reverence For Life..."}
        assert messages[2] == {"role": "user", "content": "How does that apply to anger?"}

    @pytest.mark.asyncio
    async def test_reflect_passes_history_to_claude(self):
        client = _mock_client("Deeper reflection...")
        history = [
            Turn("user", "I feel angry"),
            Turn("assistant", "I hear you..."),
        ]
        result = await handle_reflect("It keeps coming back", client, history=history)
        assert result == "Deeper reflection..."

        messages = client.messages.create.call_args.kwargs["messages"]
        assert len(messages) == 3

    @pytest.mark.asyncio
    async def test_guide_passes_history_to_claude(self):
        client = _mock_client("Further guidance...")
        history = [
            Turn("user", "Should I quit my job?"),
            Turn("assistant", "Let's reflect on that..."),
        ]
        result = await handle_guide("But I'm so unhappy", client, history=history)
        assert result == "Further guidance..."

        messages = client.messages.create.call_args.kwargs["messages"]
        assert len(messages) == 3

    @pytest.mark.asyncio
    async def test_no_history_sends_single_message(self):
        client = _mock_client("Fresh response")
        result = await handle_teach("What are the trainings?", client, history=None)
        assert result == "Fresh response"

        messages = client.messages.create.call_args.kwargs["messages"]
        assert len(messages) == 1
        assert messages[0] == {"role": "user", "content": "What are the trainings?"}
