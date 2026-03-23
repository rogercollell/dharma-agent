"""Guide skill — evaluate actions and suggest mindful alternatives."""

from __future__ import annotations

from typing import TYPE_CHECKING

from dharma_agent.conversation import Turn
from dharma_agent.contracts import WisdomResult
from dharma_agent.memory.pattern_store import InterventionPattern
from dharma_agent.memory.profile_store import UserProfile
from dharma_agent.skills.review import handle_review

if TYPE_CHECKING:
    import anthropic


GUIDE_INSTRUCTION = """\
The user is describing an action they're considering or a behavior they want \
guidance on. Your role: gently assess it against the Five Mindfulness Trainings \
and, if appropriate, suggest a more mindful alternative.

Important principles:
- Be compassionate, never preachy or judgmental
- Acknowledge the feeling behind the action (anger, fear, hurt, etc.)
- If the action aligns with the trainings, affirm it warmly
- If it doesn't, offer an alternative as an invitation, not a command
- Honor the person's autonomy — they choose their path

Structure your response around:
1. Acknowledge the impulse or intention behind the action
2. Gently explore how the trainings relate to it
3. If helpful, offer a more mindful alternative or reframe"""

async def handle_guide(
    user_message: str,
    client: anthropic.AsyncAnthropic | None,
    history: list[Turn] | None = None,
    profile: UserProfile | None = None,
    patterns: list[InterventionPattern] | None = None,
) -> WisdomResult:
    """Compatibility wrapper that delegates guide requests to review."""
    return await handle_review(
        user_message=user_message,
        client=client,
        history=history,
        profile=profile,
        patterns=patterns,
    )
