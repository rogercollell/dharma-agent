"""Guide skill — evaluate actions and suggest mindful alternatives."""

from __future__ import annotations

from typing import TYPE_CHECKING

from dharma_agent.conversation import Turn, build_messages
from dharma_agent.trainings import ALL_TRAININGS_TEXT, SYSTEM_PROMPT

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


FALLBACK_GUIDE = """\
Before acting, you might consider how the Five Mindfulness Trainings relate \
to this situation:

{trainings}

The trainings are not rules — they are invitations to look deeply. Whatever \
you choose, may it come from a place of compassion and clarity."""


async def handle_guide(
    user_message: str,
    client: anthropic.AsyncAnthropic | None,
    history: list[Turn] | None = None,
) -> str:
    """Offer mindful guidance on a proposed action."""
    if client is None:
        return FALLBACK_GUIDE.format(trainings=ALL_TRAININGS_TEXT)

    response = await client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        system=f"{SYSTEM_PROMPT}\n\n{GUIDE_INSTRUCTION}",
        messages=build_messages(history, user_message),
    )
    return response.content[0].text
