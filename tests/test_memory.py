"""Tests for profile and pattern memory stores."""

import pytest

from dharma_agent.memory.pattern_store import InMemoryPatternStore
from dharma_agent.memory.profile_store import InMemoryProfileStore


class TestInMemoryProfileStore:
    @pytest.mark.asyncio
    async def test_profiles_are_isolated(self):
        store = InMemoryProfileStore()
        profile_a = await store.get("a")
        profile_a.remember_theme("Loving Speech and Deep Listening")
        await store.save(profile_a)

        profile_b = await store.get("b")
        assert profile_b.recurring_themes == []

    @pytest.mark.asyncio
    async def test_save_persists_distilled_fields(self):
        store = InMemoryProfileStore()
        profile = await store.get("a")
        profile.remember_practice("Take three breaths.")
        profile.last_outcome = "helpful"
        await store.save(profile)

        loaded = await store.get("a")
        assert loaded.helpful_practices == ["Take three breaths."]
        assert loaded.last_outcome == "helpful"


class TestInMemoryPatternStore:
    @pytest.mark.asyncio
    async def test_record_tracks_success_and_failure(self):
        store = InMemoryPatternStore()
        await store.record(
            memory_id="a",
            skill_id="review",
            cue="Loving Speech and Deep Listening",
            next_step="Remove contempt.",
            practice="Pause before sending.",
            outcome="helpful",
        )
        await store.record(
            memory_id="a",
            skill_id="review",
            cue="Loving Speech and Deep Listening",
            next_step="Remove contempt.",
            practice="Pause before sending.",
            outcome="unhelpful",
        )

        patterns = await store.list_for_memory("a")
        assert len(patterns) == 1
        assert patterns[0].success_count == 1
        assert patterns[0].failure_count == 1
