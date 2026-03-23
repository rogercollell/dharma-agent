"""Tests for structured skill handlers."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from dharma_agent.contracts import WisdomResult
from dharma_agent.conversation import Turn
from dharma_agent.memory.pattern_store import InterventionPattern
from dharma_agent.memory.profile_store import UserProfile
from dharma_agent.skills.guide import handle_guide
from dharma_agent.skills.reflect import handle_reflect
from dharma_agent.skills.respond import handle_respond
from dharma_agent.skills.review import handle_review
from dharma_agent.skills.teach import handle_teach, _fallback_teach


def _mock_client(response_text: str):
    client = AsyncMock()
    response = MagicMock()
    response.content = [MagicMock(text=response_text)]
    client.messages.create = AsyncMock(return_value=response)
    return client


class TestTeachFallback:
    """Tests for structured teaching fallbacks."""

    def test_specific_training_by_number(self):
        result = _fallback_teach("Tell me about training 1")
        assert result.relevant_trainings == ["Reverence For Life"]
        assert "Reverence For Life" in result.insight

    def test_specific_training_by_name(self):
        result = _fallback_teach("What is true love?")
        assert result.relevant_trainings == ["True Love"]
        assert "True Love" in result.insight

    def test_all_trainings_default(self):
        result = _fallback_teach("What are the trainings?")
        assert len(result.relevant_trainings) == 5
        assert "True Happiness" in result.insight


class TestSkillsWithClient:
    """Tests for JSON and plain-text client responses."""

    @pytest.mark.asyncio
    async def test_teach_parses_json_result(self):
        client = _mock_client(
            '{"acknowledgement":"Here you go.","insight":"A concise teaching.","relevant_trainings":["Reverence For Life"],"risks":[],"next_step":"Sit with one line.","draft_response":null,"practice":"Read it slowly.","follow_up_question":"Want an example?","needs_escalation":false}'
        )
        result = await handle_teach("Explain the first training", client)
        assert isinstance(result, WisdomResult)
        assert result.insight == "A concise teaching."
        assert result.relevant_trainings == ["Reverence For Life"]

    @pytest.mark.asyncio
    async def test_reflect_uses_plain_text_as_insight(self):
        client = _mock_client("Here is my reflection...")
        result = await handle_reflect("I am struggling", client)
        assert result.insight == "Here is my reflection..."
        assert result.next_step

    @pytest.mark.asyncio
    async def test_guide_delegates_to_review(self):
        client = _mock_client("Consider this alternative...")
        result = await handle_guide("Should I send this angry email?", client)
        assert result.insight == "Consider this alternative..."
        client.messages.create.assert_awaited_once()


class TestSkillsFallbackMode:
    """Tests for deterministic fallbacks."""

    @pytest.mark.asyncio
    async def test_reflect_fallback(self):
        result = await handle_reflect("I am angry", None)
        assert "slow down" in result.insight.lower()
        assert result.relevant_trainings

    @pytest.mark.asyncio
    async def test_review_fallback(self):
        result = await handle_review("Should I send this angry email?", None)
        assert result.risks
        assert result.next_step

    @pytest.mark.asyncio
    async def test_respond_uses_profile_and_patterns(self):
        profile = UserProfile(memory_id="s1")
        profile.remember_practice("Step away from the keyboard for one minute.")
        pattern = InterventionPattern(
            pattern_id="p1",
            memory_id="s1",
            skill_id="respond",
            cue="Loving Speech and Deep Listening",
            next_step="Lead with one feeling and one request.",
            practice="Step away from the keyboard for one minute.",
            success_count=2,
        )
        result = await handle_respond(
            "Help me reply to my coworker",
            None,
            profile=profile,
            patterns=[pattern],
        )
        assert "Lead with one feeling and one request." in result.insight
        assert result.practice == "Step away from the keyboard for one minute."


class TestSkillsWithHistory:
    """Tests for messages passed to Claude."""

    @pytest.mark.asyncio
    async def test_teach_passes_history_to_claude(self):
        client = _mock_client("Follow-up teaching...")
        history = [
            Turn("user", "Tell me about the first training"),
            Turn("assistant", "The first training is Reverence For Life..."),
        ]
        await handle_teach("How does that apply to anger?", client, history=history)

        call_kwargs = client.messages.create.call_args.kwargs
        messages = call_kwargs["messages"]
        assert len(messages) == 3
        assert messages[0] == {"role": "user", "content": "Tell me about the first training"}
        assert messages[2] == {"role": "user", "content": "How does that apply to anger?"}

    @pytest.mark.asyncio
    async def test_respond_passes_history_to_claude(self):
        client = _mock_client("A revised draft")
        history = [
            Turn("user", "Here is my first draft"),
            Turn("assistant", "Try softening the opening."),
        ]
        await handle_respond("Rewrite it more calmly", client, history=history)

        messages = client.messages.create.call_args.kwargs["messages"]
        assert len(messages) == 3
