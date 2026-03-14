"""Dharma Agent Executor — routes requests to skill handlers."""

from __future__ import annotations

import logging
import os

from typing_extensions import override

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.types import TaskState, TaskStatus, TaskStatusUpdateEvent
from a2a.utils import new_agent_text_message

from dharma_agent.skills.teach import handle_teach
from dharma_agent.skills.reflect import handle_reflect
from dharma_agent.skills.guide import handle_guide

logger = logging.getLogger(__name__)


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

    async def _enqueue_error(
        self,
        context: RequestContext,
        event_queue: EventQueue,
        message_text: str,
    ) -> None:
        """Enqueue a failed status event with a compassionate error message."""
        await event_queue.enqueue_event(
            TaskStatusUpdateEvent(
                task_id=context.task_id or "",
                context_id=context.context_id or "",
                final=True,
                status=TaskStatus(
                    state=TaskState.failed,
                    message=new_agent_text_message(message_text),
                ),
            )
        )

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
            await event_queue.enqueue_event(
                TaskStatusUpdateEvent(
                    task_id=context.task_id or "",
                    context_id=context.context_id or "",
                    final=True,
                    status=TaskStatus(state=TaskState.completed),
                )
            )
            return

        # Signal that processing has started
        await event_queue.enqueue_event(
            TaskStatusUpdateEvent(
                task_id=context.task_id or "",
                context_id=context.context_id or "",
                final=False,
                status=TaskStatus(state=TaskState.working),
            )
        )

        # Route to the appropriate skill handler
        skill_id = _detect_skill(user_input)

        handlers = {
            "teach": handle_teach,
            "reflect": handle_reflect,
            "guide": handle_guide,
        }
        handler = handlers[skill_id]

        try:
            result = await handler(user_input, self._client)
        except Exception as exc:
            # Import anthropic only when we need to check error types
            try:
                import anthropic as _anthropic
            except ImportError:
                _anthropic = None

            if _anthropic and isinstance(exc, _anthropic.APIConnectionError):
                logger.exception("Failed to connect to Claude API")
                await self._enqueue_error(
                    context, event_queue,
                    "I'm having trouble reaching my teacher right now. "
                    "Please try again in a moment.",
                )
            elif _anthropic and isinstance(exc, _anthropic.RateLimitError):
                logger.exception("Claude API rate limit reached")
                await self._enqueue_error(
                    context, event_queue,
                    "I need a moment of rest — too many requests right now. "
                    "Please try again shortly.",
                )
            elif _anthropic and isinstance(exc, _anthropic.AuthenticationError):
                logger.exception("Claude API authentication failed")
                await self._enqueue_error(
                    context, event_queue,
                    "There is a configuration issue preventing me from "
                    "responding fully. The administrator may need to check "
                    "the API key.",
                )
            elif _anthropic and isinstance(exc, _anthropic.APIError):
                logger.exception("Claude API error: %s", exc)
                await self._enqueue_error(
                    context, event_queue,
                    "Something unexpected happened while I was reflecting. "
                    "Please try again.",
                )
            else:
                logger.exception("Unexpected error in skill handler: %s", exc)
                await self._enqueue_error(
                    context, event_queue,
                    "I encountered an unexpected difficulty. "
                    "Please try again, and if this persists, "
                    "let the administrator know.",
                )
            return

        await event_queue.enqueue_event(new_agent_text_message(result))

        # Signal completion
        await event_queue.enqueue_event(
            TaskStatusUpdateEvent(
                task_id=context.task_id or "",
                context_id=context.context_id or "",
                final=True,
                status=TaskStatus(state=TaskState.completed),
            )
        )

    @override
    async def cancel(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        await event_queue.enqueue_event(
            TaskStatusUpdateEvent(
                task_id=context.task_id or "",
                context_id=context.context_id or "",
                final=True,
                status=TaskStatus(
                    state=TaskState.canceled,
                    message=new_agent_text_message(
                        "This task has been canceled. "
                        "I am here whenever you are ready."
                    ),
                ),
            )
        )
