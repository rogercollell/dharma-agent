"""Profile memory distilled from prior useful exchanges."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class UserProfile:
    """Distilled memory for repeated help in the same context."""

    memory_id: str
    recurring_themes: list[str] = field(default_factory=list)
    helpful_practices: list[str] = field(default_factory=list)
    effective_next_steps: list[str] = field(default_factory=list)
    last_skill_id: str | None = None
    last_outcome: str | None = None

    def remember_theme(self, theme: str) -> None:
        _remember(self.recurring_themes, theme)

    def remember_practice(self, practice: str) -> None:
        _remember(self.helpful_practices, practice)

    def remember_next_step(self, next_step: str) -> None:
        _remember(self.effective_next_steps, next_step)


class ProfileStore(ABC):
    """Abstract store for distilled user memory."""

    @abstractmethod
    async def get(self, memory_id: str) -> UserProfile:
        """Load or initialize the profile for a memory id."""

    @abstractmethod
    async def save(self, profile: UserProfile) -> None:
        """Persist the profile."""


class InMemoryProfileStore(ProfileStore):
    """In-memory profile store."""

    def __init__(self) -> None:
        self._profiles: dict[str, UserProfile] = {}

    async def get(self, memory_id: str) -> UserProfile:
        if memory_id not in self._profiles:
            self._profiles[memory_id] = UserProfile(memory_id=memory_id)
        profile = self._profiles[memory_id]
        return UserProfile(
            memory_id=profile.memory_id,
            recurring_themes=list(profile.recurring_themes),
            helpful_practices=list(profile.helpful_practices),
            effective_next_steps=list(profile.effective_next_steps),
            last_skill_id=profile.last_skill_id,
            last_outcome=profile.last_outcome,
        )

    async def save(self, profile: UserProfile) -> None:
        self._profiles[profile.memory_id] = UserProfile(
            memory_id=profile.memory_id,
            recurring_themes=list(profile.recurring_themes),
            helpful_practices=list(profile.helpful_practices),
            effective_next_steps=list(profile.effective_next_steps),
            last_skill_id=profile.last_skill_id,
            last_outcome=profile.last_outcome,
        )


def _remember(items: list[str], value: str) -> None:
    cleaned = value.strip()
    if not cleaned or cleaned in items:
        return
    items.append(cleaned)
