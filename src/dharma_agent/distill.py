"""Outcome detection and lightweight memory distillation."""

from __future__ import annotations

from dataclasses import dataclass

from dharma_agent.contracts import WisdomResult
from dharma_agent.memory.pattern_store import PatternStore
from dharma_agent.memory.profile_store import ProfileStore
from dharma_agent.memory.session_store import Turn


POSITIVE_OUTCOME_HINTS = (
    "that helped",
    "this helped",
    "it helped",
    "that worked",
    "it worked",
    "i sent it",
    "i tried that",
    "it went well",
    "we worked it out",
    "that was useful",
)

NEGATIVE_OUTCOME_HINTS = (
    "that did not help",
    "this did not help",
    "that didn't help",
    "this didn't help",
    "it didn't work",
    "it did not work",
    "that made it worse",
    "it got worse",
    "backfired",
    "that felt off",
)


@dataclass
class OutcomeSignal:
    """Normalized outcome update from a user follow-up."""

    outcome: str
    summary: str


def detect_outcome_signal(user_message: str) -> OutcomeSignal | None:
    """Detect whether a user follow-up reports how prior guidance went."""
    lower = user_message.lower()
    for hint in POSITIVE_OUTCOME_HINTS:
        if hint in lower:
            return OutcomeSignal(outcome="helpful", summary=user_message.strip())
    for hint in NEGATIVE_OUTCOME_HINTS:
        if hint in lower:
            return OutcomeSignal(outcome="unhelpful", summary=user_message.strip())
    return None


async def record_outcome(
    *,
    memory_id: str,
    signal: OutcomeSignal,
    last_assistant_turn: Turn,
    profile_store: ProfileStore,
    pattern_store: PatternStore,
) -> None:
    """Persist a simple outcome signal back into profile and pattern memory."""
    profile = await profile_store.get(memory_id)
    metadata = last_assistant_turn.metadata
    skill_id = str(metadata.get("skill_id") or "reflect")
    result = WisdomResult.from_dict(metadata.get("result") or {})

    profile.last_skill_id = skill_id
    profile.last_outcome = signal.outcome
    for training in result.relevant_trainings:
        profile.remember_theme(training)
    if signal.outcome == "helpful":
        if result.practice:
            profile.remember_practice(result.practice)
        if result.next_step:
            profile.remember_next_step(result.next_step)
    await profile_store.save(profile)

    cue = ", ".join(result.relevant_trainings) or skill_id
    await pattern_store.record(
        memory_id=memory_id,
        skill_id=skill_id,
        cue=cue,
        next_step=result.next_step,
        practice=result.practice,
        outcome=signal.outcome,
    )


def build_outcome_result(signal: OutcomeSignal) -> WisdomResult:
    """Build a short response after learning from a reported outcome."""
    if signal.outcome == "helpful":
        return WisdomResult(
            acknowledgement="Thank you for telling me how it went.",
            insight=(
                "I will treat that as a useful pattern to reuse when a similar "
                "moment comes up again."
            ),
            next_step=(
                "Notice what made it work so you can repeat that steady tone "
                "next time."
            ),
            follow_up_question=(
                "Do you want to build on what worked, or look at the next part "
                "of the situation?"
            ),
        )

    return WisdomResult(
        acknowledgement="Thank you for telling me that it did not help.",
        insight=(
            "That is still useful. We can treat it as feedback and choose a "
            "different response instead of repeating the same move."
        ),
        next_step=(
            "Tell me which part missed the mark, or paste what happened next, "
            "and I will help you revise."
        ),
        follow_up_question="What felt most off: the tone, the timing, or the actual advice?",
    )
