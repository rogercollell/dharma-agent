"""Tests for outcome detection and distillation."""

import pytest

from dharma_agent.contracts import WisdomResult
from dharma_agent.distill import detect_outcome_signal, record_outcome
from dharma_agent.memory.pattern_store import InMemoryPatternStore
from dharma_agent.memory.profile_store import InMemoryProfileStore
from dharma_agent.memory.session_store import Turn


def test_detect_outcome_signal():
    helpful = detect_outcome_signal("That helped a lot")
    unhelpful = detect_outcome_signal("That didn't help")
    assert helpful is not None
    assert helpful.outcome == "helpful"
    assert unhelpful is not None
    assert unhelpful.outcome == "unhelpful"


@pytest.mark.asyncio
async def test_record_outcome_updates_profile_and_pattern():
    profile_store = InMemoryProfileStore()
    pattern_store = InMemoryPatternStore()
    turn = Turn(
        role="assistant",
        content="Rendered text",
        metadata={
            "skill_id": "respond",
            "result": WisdomResult(
                relevant_trainings=["Loving Speech and Deep Listening"],
                next_step="Lead with one feeling and one request.",
                practice="Take three breaths.",
            ).to_dict(),
        },
    )

    signal = detect_outcome_signal("That helped")
    assert signal is not None

    await record_outcome(
        memory_id="s1",
        signal=signal,
        last_assistant_turn=turn,
        profile_store=profile_store,
        pattern_store=pattern_store,
    )

    profile = await profile_store.get("s1")
    patterns = await pattern_store.list_for_memory("s1")
    assert profile.last_outcome == "helpful"
    assert "Take three breaths." in profile.helpful_practices
    assert patterns[0].success_count == 1
