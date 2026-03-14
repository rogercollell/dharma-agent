"""Dharma Agent Executor — routes requests to skill handlers."""

from __future__ import annotations

import os

from typing_extensions import override

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.utils import new_agent_text_message

from dharma_agent.skills.teach import handle_teach
from dharma_agent.skills.reflect import handle_reflect
from dharma_agent.skills.guide import handle_guide


# Keywords used for simple skill routing when no explicit skill ID is provided
TEACH_KEYWORDS = {
    "teach", "explain", "what is", "what are", "tell me about",
    "training", "trainings", "describe", "learn", "overview",
}
GUIDE_KEYWORDS = {
    "should i", "i want to", "i'm going to", "i'm thinking of",
    "is it ok", "is it okay", "would it be", "can i", "help me decide",
    "what should", "guide",
}


def _detect_skill(user_input: str) -> str:
    """Detect which skill to use based on the user's message content.

    Falls back to 'reflect' as the most generally useful skill.
    """
    lower = user_input.lower()

    for keyword in TEACH_KEYWORDS:
        if keyword in lower:
            return "teach"

    for keyword in GUIDE_KEYWORDS:
        if keyword in lower:
            return "guide"

    # Default: reflect is the most versatile and compassionate response
    return "reflect"


def _build_client():
    """Build Anthropic client if an API key is available, else None."""
    if os.environ.get("ANTHROPIC_API_KEY"):
        import anthropic
        return anthropic.AsyncAnthropic()
    return None


class DharmaAgentExecutor(AgentExecutor):
    """Routes incoming A2A requests to the appropriate mindfulness skill."""

    def __init__(self) -> None:
        self._client = _build_client()
        if self._client is None:
            print("  (no ANTHROPIC_API_KEY found — running in fallback mode)")

    @override
    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        user_input = context.get_user_input()
        if not user_input.strip():
            await event_queue.enqueue_event(
                new_agent_text_message(
                    "I'm here whenever you're ready. "
                    "You can ask me to teach, reflect, or guide — "
                    "all rooted in the Five Mindfulness Trainings."
                )
            )
            return

        # Route to the appropriate skill handler
        skill_id = _detect_skill(user_input)

        handlers = {
            "teach": handle_teach,
            "reflect": handle_reflect,
            "guide": handle_guide,
        }
        handler = handlers[skill_id]
        result = await handler(user_input, self._client)

        await event_queue.enqueue_event(new_agent_text_message(result))

    @override
    async def cancel(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        raise Exception("cancel not supported")
