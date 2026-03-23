"""User-facing rendering for structured wisdom results."""

from __future__ import annotations

from dharma_agent.contracts import WisdomResult


def render_wisdom_result(result: WisdomResult) -> str:
    """Render a structured result into concise user-facing text."""
    sections: list[str] = []

    if result.needs_escalation:
        sections.append(
            "This sounds bigger than simple reflection alone. Please consider "
            "reaching out to a trusted person or qualified local support now."
        )

    if result.acknowledgement:
        sections.append(result.acknowledgement)

    if result.insight:
        sections.append(result.insight)

    if result.relevant_trainings:
        label = "Relevant training" if len(result.relevant_trainings) == 1 else "Relevant trainings"
        sections.append(f"{label}: {', '.join(result.relevant_trainings)}")

    if result.risks:
        sections.append("Risks to watch:\n- " + "\n- ".join(result.risks))

    if result.next_step:
        sections.append(f"Next step: {result.next_step}")

    if result.draft_response:
        sections.append(f"Draft response:\n{result.draft_response}")

    if result.practice:
        sections.append(f"Practice: {result.practice}")

    if result.follow_up_question:
        sections.append(f"Question: {result.follow_up_question}")

    return "\n\n".join(section for section in sections if section)
