"""Agent Card and skill definitions for Dharma Agent."""

from a2a.types import AgentCard, AgentCapabilities, AgentSkill


teach_skill = AgentSkill(
    id="teach",
    name="Teach the Five Mindfulness Trainings",
    description=(
        "Explain any of the Five Mindfulness Trainings with context and "
        "examples from the tradition of Thich Nhat Hanh."
    ),
    tags=["mindfulness", "buddhism", "five-trainings", "education"],
    examples=[
        "Explain the first training",
        "What are the Five Mindfulness Trainings?",
        "Tell me about True Love",
        "What does Reverence for Life mean?",
    ],
)

reflect_skill = AgentSkill(
    id="reflect",
    name="Reflect and clarify",
    description=(
        "Reflect on a situation, feeling, or challenge through the lens of "
        "the Five Mindfulness Trainings and surface one clear next step."
    ),
    tags=["mindfulness", "reflection", "ethics", "decision-making"],
    examples=[
        "I'm struggling with anger at a coworker",
        "How should I think about this ethical dilemma?",
        "I feel overwhelmed by the news",
        "I'm not sure if I'm being fair to someone",
    ],
)

respond_skill = AgentSkill(
    id="respond",
    name="Craft a wiser reply",
    description=(
        "Help draft a reply that is honest, calm, and less likely to escalate."
    ),
    tags=["mindfulness", "communication", "drafting", "compassion"],
    examples=[
        "Help me reply to this message without escalating",
        "Draft a kinder response to my coworker",
        "I need to answer this email firmly but calmly",
        "Rewrite this text so it stays honest and respectful",
    ],
)

review_skill = AgentSkill(
    id="review",
    name="Review for likely harm",
    description=(
        "Review a proposed action, draft, or piece of advice for likely harm, "
        "coldness, manipulation, or unnecessary escalation."
    ),
    tags=["mindfulness", "review", "ethics", "communication"],
    examples=[
        "Review this message before I send it",
        "Does this sound too harsh?",
        "What harm could this advice cause?",
        "Should I send this angry email to my boss?",
    ],
)


def build_agent_card(url: str = "http://0.0.0.0:9999/") -> AgentCard:
    """Build the Agent Card for Dharma Agent."""
    return AgentCard(
        name="Dharma Agent",
        description=(
            "An agent rooted in the Five Mindfulness Trainings — offering "
            "teachings, reflections, and mindful guidance to humans and AI "
            "agents alike."
        ),
        url=url,
        version="0.1.0",
        defaultInputModes=["text"],
        defaultOutputModes=["text"],
        capabilities=AgentCapabilities(streaming=True),
        skills=[teach_skill, reflect_skill, respond_skill, review_skill],
    )
