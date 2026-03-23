"""Pattern memory for interventions that helped or failed."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class InterventionPattern:
    """A compact reusable pattern captured from prior exchanges."""

    pattern_id: str
    memory_id: str
    skill_id: str
    cue: str
    next_step: str
    practice: str
    success_count: int = 0
    failure_count: int = 0
    last_outcome: str | None = None


class PatternStore(ABC):
    """Abstract store for distilled intervention patterns."""

    @abstractmethod
    async def list_for_memory(self, memory_id: str) -> list[InterventionPattern]:
        """Return patterns for a memory id."""

    @abstractmethod
    async def record(
        self,
        *,
        memory_id: str,
        skill_id: str,
        cue: str,
        next_step: str,
        practice: str,
        outcome: str,
    ) -> InterventionPattern:
        """Create or update a pattern entry."""


class InMemoryPatternStore(PatternStore):
    """In-memory pattern store."""

    def __init__(self) -> None:
        self._patterns: dict[str, InterventionPattern] = {}

    async def list_for_memory(self, memory_id: str) -> list[InterventionPattern]:
        patterns = [
            pattern
            for pattern in self._patterns.values()
            if pattern.memory_id == memory_id
        ]
        return [
            InterventionPattern(
                pattern_id=pattern.pattern_id,
                memory_id=pattern.memory_id,
                skill_id=pattern.skill_id,
                cue=pattern.cue,
                next_step=pattern.next_step,
                practice=pattern.practice,
                success_count=pattern.success_count,
                failure_count=pattern.failure_count,
                last_outcome=pattern.last_outcome,
            )
            for pattern in patterns
        ]

    async def record(
        self,
        *,
        memory_id: str,
        skill_id: str,
        cue: str,
        next_step: str,
        practice: str,
        outcome: str,
    ) -> InterventionPattern:
        pattern_id = f"{memory_id}:{skill_id}:{cue}"
        pattern = self._patterns.get(
            pattern_id,
            InterventionPattern(
                pattern_id=pattern_id,
                memory_id=memory_id,
                skill_id=skill_id,
                cue=cue,
                next_step=next_step,
                practice=practice,
            ),
        )
        pattern.next_step = next_step or pattern.next_step
        pattern.practice = practice or pattern.practice
        pattern.last_outcome = outcome
        if outcome == "helpful":
            pattern.success_count += 1
        elif outcome == "unhelpful":
            pattern.failure_count += 1
        self._patterns[pattern_id] = pattern
        return InterventionPattern(
            pattern_id=pattern.pattern_id,
            memory_id=pattern.memory_id,
            skill_id=pattern.skill_id,
            cue=pattern.cue,
            next_step=pattern.next_step,
            practice=pattern.practice,
            success_count=pattern.success_count,
            failure_count=pattern.failure_count,
            last_outcome=pattern.last_outcome,
        )
