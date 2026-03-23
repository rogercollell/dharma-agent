"""Review skill — inspect a draft action or reply for likely harm."""

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


REVIEW_INSTRUCTION = """\
The user wants a review of a proposed action, draft message, or line of advice.

Your role:
- identify where harm, manipulation, coldness, avoidance, or overconfidence may show up
- name the main risk plainly
- preserve honesty and autonomy
- give one concrete revision or next step

Do not be preachy. Be clear, practical, and calm."""


def _fallback_review(
    user_message: str,
    profile: UserProfile | None,
    patterns: list[InterventionPattern] | None,
) -> WisdomResult:
    trainings = suggest_relevant_trainings(user_message)
    lower = user_message.lower()
    risks: list[str] = []
    if any(word in lower for word in ("always", "never", "every time")):
        risks.append("absolute language can make the other person feel judged instead of heard")
    if any(word in lower for word in ("idiot", "stupid", "hate", "shut up")):
        risks.append("contempt tends to close the conversation immediately")
    if any(word in lower for word in ("!", "all caps")):
        risks.append("high heat in the wording can overpower the actual point you want to make")
    if not risks:
        risks = [
            "the main risk is sounding more certain or harsher than you intend",
            "if the other person feels cornered, they may react defensively instead of honestly",
        ]

    prior_pattern = next(
        (
            pattern for pattern in (patterns or [])
            if pattern.success_count > pattern.failure_count
        ),
        None,
    )
    next_step = (
        prior_pattern.next_step
        if prior_pattern
        else "Keep the truth, remove any contempt, and end with one clear request or question."
    )

    return WisdomResult(
        acknowledgement="I can review it for truthfulness, tone, and likely harm.",
        insight=(
            "The wisest review usually asks: does this say what is true, without using more force than necessary?"
        ),
        relevant_trainings=trainings,
        risks=risks,
        next_step=next_step,
        practice=(
            profile.helpful_practices[0]
            if profile and profile.helpful_practices
            else "Read it once as if you were the receiver. Notice where the body tightens."
        ),
        follow_up_question="Do you want me to rewrite it, or just point out the sharpest risk?",
    )


async def handle_review(
    user_message: str,
    client: anthropic.AsyncAnthropic | None,
    history: list[Turn] | None = None,
    profile: UserProfile | None = None,
    patterns: list[InterventionPattern] | None = None,
) -> WisdomResult:
    """Review a proposed action or message for likely harm."""
    fallback = _fallback_review(user_message, profile, patterns)
    return await complete_wisdom_result(
        user_message=user_message,
        client=client,
        history=history,
        instruction=REVIEW_INSTRUCTION,
        fallback=fallback,
        profile=profile,
        patterns=patterns,
    )
