"""Respond skill — craft a wiser next message."""

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


RESPOND_INSTRUCTION = """\
The user wants help replying or writing a message in a wiser, more compassionate way.

Your role:
- preserve honesty without aggression
- reduce escalation without becoming vague or passive
- offer one concrete next step
- provide a draft response only if it would clearly help

Prefer practical language over abstract teaching."""


def _fallback_respond(
    user_message: str,
    profile: UserProfile | None,
    patterns: list[InterventionPattern] | None,
) -> WisdomResult:
    trainings = suggest_relevant_trainings(user_message)
    prior_step = profile.effective_next_steps[0] if profile and profile.effective_next_steps else ""
    prior_practice = profile.helpful_practices[0] if profile and profile.helpful_practices else ""
    prior_pattern = next(
        (
            pattern for pattern in (patterns or [])
            if pattern.success_count > pattern.failure_count
        ),
        None,
    )

    insight = (
        "A useful reply usually names the truth of what happened, avoids blame-heavy "
        "language, and makes one clear request."
    )
    if prior_pattern:
        insight += f" A pattern that has helped before here is: {prior_pattern.next_step}"

    next_step = prior_step or (
        "Cut the reply down to one observation, one feeling, and one clear request."
    )
    practice = prior_practice or (
        "Take three breaths, then read the draft once asking: is it true, necessary, and kind?"
    )

    return WisdomResult(
        acknowledgement="It sounds like you want to respond without adding more heat.",
        insight=insight,
        relevant_trainings=trainings,
        risks=[
            "replying from the peak of anger can harden the conflict",
            "explaining too much can bury the one point that matters most",
        ],
        next_step=next_step,
        draft_response=(
            "Hi — I want to respond honestly without escalating this. "
            "When that happened, I felt hurt and tense. "
            "I would like us to talk about it more directly and find a better way forward. "
            "Are you open to that?"
        ),
        practice=practice,
        follow_up_question="If you paste your actual draft, do you want me to tighten the tone or the clarity?",
    )


async def handle_respond(
    user_message: str,
    client: anthropic.AsyncAnthropic | None,
    history: list[Turn] | None = None,
    profile: UserProfile | None = None,
    patterns: list[InterventionPattern] | None = None,
) -> WisdomResult:
    """Craft a wiser next message."""
    fallback = _fallback_respond(user_message, profile, patterns)
    return await complete_wisdom_result(
        user_message=user_message,
        client=client,
        history=history,
        instruction=RESPOND_INSTRUCTION,
        fallback=fallback,
        profile=profile,
        patterns=patterns,
    )
