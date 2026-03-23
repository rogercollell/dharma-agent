"""Teach skill — explain the Five Mindfulness Trainings."""

from __future__ import annotations

from typing import TYPE_CHECKING

from dharma_agent.contracts import WisdomResult
from dharma_agent.conversation import Turn
from dharma_agent.memory.pattern_store import InterventionPattern
from dharma_agent.memory.profile_store import UserProfile
from dharma_agent.skills.common import complete_wisdom_result
from dharma_agent.trainings import (
    ALL_TRAININGS_TEXT,
    TRAININGS_BY_NAME,
    ALL_TRAININGS,
    TRAINING_NAME_BY_NUMBER,
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


def _fallback_teach(user_message: str) -> WisdomResult:
    """Return a structured teaching response when no LLM is available."""
    lower = user_message.lower()

    # Check for a specific training by number
    for num, text in ALL_TRAININGS.items():
        if f"training {num}" in lower or f"#{num}" in lower:
            training_name = TRAINING_NAME_BY_NUMBER[num]
            return WisdomResult(
                acknowledgement=f"Here is the {_ordinal(num)} Mindfulness Training.",
                insight=text,
                relevant_trainings=[training_name],
                next_step="Take one sentence from this training and ask where it touches your daily life right now.",
                practice="Read it once slowly, then notice which line creates the most resistance or relief.",
                follow_up_question="Do you want the core meaning in simpler everyday language too?",
            )

    # Check for a specific training by name
    for name, text in TRAININGS_BY_NAME.items():
        if name in lower:
            return WisdomResult(
                acknowledgement=f"Here is the training on {name.title()}.",
                insight=text,
                relevant_trainings=[name.title()],
                next_step="Notice one place this training asks for a smaller, more concrete shift in daily life.",
                practice="Take one breath after each paragraph and let the language land before judging it.",
                follow_up_question="Do you want an example of how this could look in ordinary life?",
            )

    # Default: return all five
    return WisdomResult(
        acknowledgement=(
            "Here are the Five Mindfulness Trainings, from the tradition of "
            "Thich Nhat Hanh."
        ),
        insight=ALL_TRAININGS_TEXT,
        relevant_trainings=list(TRAINING_NAME_BY_NUMBER.values()),
        next_step="Choose the one training that feels most alive in your life right now before trying to hold all five at once.",
        practice="Read the titles only first, then notice which one your attention returns to.",
        follow_up_question="Do you want a plain-language summary of the one that stands out most?",
    )


def _ordinal(num: str) -> str:
    suffixes = {"1": "First", "2": "Second", "3": "Third", "4": "Fourth", "5": "Fifth"}
    return suffixes.get(num, num)


async def handle_teach(
    user_message: str,
    client: anthropic.AsyncAnthropic | None,
    history: list[Turn] | None = None,
    profile: UserProfile | None = None,
    patterns: list[InterventionPattern] | None = None,
) -> WisdomResult:
    """Generate a teaching response about the Five Mindfulness Trainings."""
    fallback = _fallback_teach(user_message)
    return await complete_wisdom_result(
        user_message=user_message,
        client=client,
        history=history,
        instruction=TEACH_INSTRUCTION,
        fallback=fallback,
        profile=profile,
        patterns=patterns,
    )
