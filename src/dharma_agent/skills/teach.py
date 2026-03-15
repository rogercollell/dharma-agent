"""Teach skill — explain the Five Mindfulness Trainings."""

from __future__ import annotations

from typing import TYPE_CHECKING

from dharma_agent.conversation import Turn, build_messages
from dharma_agent.trainings import (
    ALL_TRAININGS_TEXT,
    SYSTEM_PROMPT,
    TRAININGS_BY_NAME,
    ALL_TRAININGS,
)

if TYPE_CHECKING:
    import anthropic


TEACH_INSTRUCTION = """\
The user is asking you to teach about the Five Mindfulness Trainings.

Your role: explain the requested training(s) with warmth, clarity, and \
accessibility. Use everyday language. If the user asks about a specific \
training, focus on that one in depth. If they ask generally, give a clear \
overview of all five.

Offer context about why each training matters in daily life. You may share \
brief examples of how the training applies to common situations.

Keep your response focused and not too long — teach with care, not volume."""


def _fallback_teach(user_message: str) -> str:
    """Return the training text directly when no LLM is available."""
    lower = user_message.lower()

    # Check for a specific training by number
    for num, text in ALL_TRAININGS.items():
        if f"training {num}" in lower or f"#{num}" in lower:
            return f"Here is the {_ordinal(num)} Mindfulness Training:\n\n{text}"

    # Check for a specific training by name
    for name, text in TRAININGS_BY_NAME.items():
        if name in lower:
            return f"Here is the training on {name.title()}:\n\n{text}"

    # Default: return all five
    return (
        "Here are the Five Mindfulness Trainings, from the tradition of "
        "Thich Nhat Hanh:\n\n" + ALL_TRAININGS_TEXT
    )


def _ordinal(num: str) -> str:
    suffixes = {"1": "First", "2": "Second", "3": "Third", "4": "Fourth", "5": "Fifth"}
    return suffixes.get(num, num)


async def handle_teach(
    user_message: str,
    client: anthropic.AsyncAnthropic | None,
    history: list[Turn] | None = None,
) -> str:
    """Generate a teaching response about the Five Mindfulness Trainings."""
    if client is None:
        return _fallback_teach(user_message)

    response = await client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        system=f"{SYSTEM_PROMPT}\n\n{TEACH_INSTRUCTION}",
        messages=build_messages(history, user_message),
    )
    return response.content[0].text
