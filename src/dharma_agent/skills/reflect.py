"""Reflect skill — apply the Trainings to a situation."""

from __future__ import annotations

from typing import TYPE_CHECKING

from dharma_agent.contracts import WisdomResult
from dharma_agent.conversation import Turn
from dharma_agent.memory.pattern_store import InterventionPattern
from dharma_agent.memory.profile_store import UserProfile
from dharma_agent.skills.common import complete_wisdom_result
from dharma_agent.trainings import suggest_relevant_trainings

if TYPE_CHECKING:
    import anthropic


REFLECT_INSTRUCTION = """\
The user is sharing a situation, feeling, or challenge and asking you to \
reflect on it through the lens of the Five Mindfulness Trainings.

Your role: listen deeply, identify which trainings are most relevant, and \
offer gentle insight. Never lecture or moralize. Meet the person where they \
are — with compassion and without judgment.

Structure your response around:
1. Acknowledge what they're experiencing
2. Identify which training(s) speak to this situation and why
3. Offer a perspective or reflection that might help them see more clearly

Keep it personal and warm, not academic."""


async def handle_reflect(
    user_message: str,
    client: anthropic.AsyncAnthropic | None,
    history: list[Turn] | None = None,
    profile: UserProfile | None = None,
    patterns: list[InterventionPattern] | None = None,
) -> WisdomResult:
    """Reflect on a situation through the Five Mindfulness Trainings."""
    trainings = suggest_relevant_trainings(user_message)
    fallback = WisdomResult(
        acknowledgement="Thank you for sharing what is happening.",
        insight=(
            "The trainings invite us to slow down enough to see the feeling, "
            "the story we are telling about it, and the next action we are "
            "leaning toward."
        ),
        relevant_trainings=trainings,
        next_step="Name the strongest feeling in one plain sentence before trying to solve everything at once.",
        practice=(
            profile.helpful_practices[0]
            if profile and profile.helpful_practices
            else "Take three quiet breaths and notice where this lands in the body."
        ),
        follow_up_question="What feels most alive right now: hurt, fear, anger, grief, or confusion?",
    )
    return await complete_wisdom_result(
        user_message=user_message,
        client=client,
        history=history,
        instruction=REFLECT_INSTRUCTION,
        fallback=fallback,
        profile=profile,
        patterns=patterns,
    )
