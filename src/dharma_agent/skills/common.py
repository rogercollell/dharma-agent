"""Shared helpers for Dharma Agent skills."""

from __future__ import annotations

from typing import TYPE_CHECKING

from dharma_agent.contracts import WisdomResult
from dharma_agent.conversation import Turn, build_messages
from dharma_agent.memory.pattern_store import InterventionPattern
from dharma_agent.memory.profile_store import UserProfile
from dharma_agent.trainings import SYSTEM_PROMPT

if TYPE_CHECKING:
    import anthropic


JSON_RESULT_INSTRUCTION = """\
Return JSON with exactly these keys:
- acknowledgement: short compassionate acknowledgement
- insight: the main perspective or teaching
- relevant_trainings: array of training names
- risks: array of short risk statements
- next_step: one concrete next step
- draft_response: optional response draft, or null
- practice: one small practice
- follow_up_question: one useful follow-up question
- needs_escalation: boolean"""


def build_memory_context(
    profile: UserProfile | None,
    patterns: list[InterventionPattern] | None,
) -> str:
    """Build compact context from profile and pattern memory."""
    lines: list[str] = []
    if profile:
        if profile.recurring_themes:
            lines.append(
                "Recurring themes: " + ", ".join(profile.recurring_themes[:3])
            )
        if profile.helpful_practices:
            lines.append(
                "Helpful practices before: "
                + "; ".join(profile.helpful_practices[:2])
            )
        if profile.effective_next_steps:
            lines.append(
                "Next steps that helped before: "
                + "; ".join(profile.effective_next_steps[:2])
            )

    strong_patterns = sorted(
        patterns or [],
        key=lambda pattern: (pattern.success_count - pattern.failure_count),
        reverse=True,
    )[:2]
    for pattern in strong_patterns:
        if pattern.success_count <= pattern.failure_count:
            continue
        lines.append(
            "Helpful pattern before: "
            f"{pattern.cue} -> {pattern.next_step}"
        )

    if not lines:
        return ""

    return "Memory to honor if still relevant:\n" + "\n".join(f"- {line}" for line in lines)


async def complete_wisdom_result(
    *,
    user_message: str,
    client: anthropic.AsyncAnthropic | None,
    history: list[Turn] | None,
    instruction: str,
    fallback: WisdomResult,
    profile: UserProfile | None = None,
    patterns: list[InterventionPattern] | None = None,
) -> WisdomResult:
    """Return fallback immediately or ask Claude for a structured result."""
    if client is None:
        return fallback

    memory_context = build_memory_context(profile, patterns)
    system_parts = [SYSTEM_PROMPT]
    if memory_context:
        system_parts.append(memory_context)
    system_parts.append(instruction)
    system_parts.append(JSON_RESULT_INSTRUCTION)

    response = await client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        system="\n\n".join(system_parts),
        messages=build_messages(history, user_message),
    )
    return WisdomResult.from_text(response.content[0].text, defaults=fallback)
