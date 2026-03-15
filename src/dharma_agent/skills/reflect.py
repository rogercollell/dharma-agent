"""Reflect skill — apply the Trainings to a situation."""

from __future__ import annotations

from typing import TYPE_CHECKING

from dharma_agent.conversation import Turn, build_messages
from dharma_agent.trainings import ALL_TRAININGS_TEXT, SYSTEM_PROMPT

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


FALLBACK_REFLECT = """\
Thank you for sharing. The Five Mindfulness Trainings invite us to look \
deeply into our experience with compassion and without judgment.

Here are the trainings — consider which ones speak to your situation:

{trainings}

Take a moment to breathe and sit with whichever training resonates most. \
There is no rush."""


async def handle_reflect(
    user_message: str,
    client: anthropic.AsyncAnthropic | None,
    history: list[Turn] | None = None,
) -> str:
    """Reflect on a situation through the Five Mindfulness Trainings."""
    if client is None:
        return FALLBACK_REFLECT.format(trainings=ALL_TRAININGS_TEXT)

    response = await client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        system=f"{SYSTEM_PROMPT}\n\n{REFLECT_INSTRUCTION}",
        messages=build_messages(history, user_message),
    )
    return response.content[0].text
