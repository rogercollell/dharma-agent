"""Structured result contracts for Dharma Agent skills."""

from __future__ import annotations

from dataclasses import dataclass, field
import json
from typing import Any


@dataclass
class WisdomResult:
    """Stable internal shape shared across skills."""

    acknowledgement: str = ""
    insight: str = ""
    relevant_trainings: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    next_step: str = ""
    draft_response: str | None = None
    practice: str = ""
    follow_up_question: str = ""
    needs_escalation: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation."""
        return {
            "acknowledgement": self.acknowledgement,
            "insight": self.insight,
            "relevant_trainings": list(self.relevant_trainings),
            "risks": list(self.risks),
            "next_step": self.next_step,
            "draft_response": self.draft_response,
            "practice": self.practice,
            "follow_up_question": self.follow_up_question,
            "needs_escalation": self.needs_escalation,
        }

    def with_defaults(self, defaults: "WisdomResult") -> "WisdomResult":
        """Fill empty fields with values from defaults."""
        return WisdomResult(
            acknowledgement=self.acknowledgement or defaults.acknowledgement,
            insight=self.insight or defaults.insight,
            relevant_trainings=self.relevant_trainings or defaults.relevant_trainings,
            risks=self.risks or defaults.risks,
            next_step=self.next_step or defaults.next_step,
            draft_response=self.draft_response or defaults.draft_response,
            practice=self.practice or defaults.practice,
            follow_up_question=(
                self.follow_up_question or defaults.follow_up_question
            ),
            needs_escalation=self.needs_escalation or defaults.needs_escalation,
        )

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "WisdomResult":
        """Build from a dict, ignoring unexpected fields."""
        return cls(
            acknowledgement=str(payload.get("acknowledgement") or ""),
            insight=str(payload.get("insight") or ""),
            relevant_trainings=_as_string_list(payload.get("relevant_trainings")),
            risks=_as_string_list(payload.get("risks")),
            next_step=str(payload.get("next_step") or ""),
            draft_response=_as_optional_string(payload.get("draft_response")),
            practice=str(payload.get("practice") or ""),
            follow_up_question=str(payload.get("follow_up_question") or ""),
            needs_escalation=bool(payload.get("needs_escalation", False)),
        )

    @classmethod
    def from_text(
        cls,
        text: str,
        defaults: "WisdomResult" | None = None,
    ) -> "WisdomResult":
        """Parse model output, accepting JSON or falling back to plain text."""
        cleaned = _strip_code_fence(text.strip())
        try:
            payload = json.loads(cleaned)
        except json.JSONDecodeError:
            result = cls(insight=text.strip())
        else:
            result = cls.from_dict(payload)

        return result.with_defaults(defaults) if defaults is not None else result


def coerce_wisdom_result(
    raw_result: WisdomResult | str,
    *,
    skill_id: str,
) -> WisdomResult:
    """Normalize legacy string skill returns into WisdomResult."""
    if isinstance(raw_result, WisdomResult):
        return raw_result

    if skill_id == "respond":
        return WisdomResult(
            acknowledgement="Here is a calmer draft you can adapt.",
            draft_response=raw_result,
            next_step="Adjust the draft so it matches the exact truth of your situation.",
        )

    return WisdomResult(insight=raw_result)


def _strip_code_fence(text: str) -> str:
    if not text.startswith("```"):
        return text

    lines = text.splitlines()
    if len(lines) >= 3 and lines[-1].strip() == "```":
        return "\n".join(lines[1:-1]).strip()
    return text


def _as_string_list(value: Any) -> list[str]:
    if not value:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return [str(value).strip()] if str(value).strip() else []


def _as_optional_string(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
