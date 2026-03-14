"""Tests for individual skill handlers."""

import pytest
from unittest.mock import AsyncMock, MagicMock

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
