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
    name="Reflect through the lens of the Trainings",
    description=(
        "Reflect on a situation, feeling, or challenge through the lens of "
        "the Five Mindfulness Trainings. Offers gentle perspective without judgment."
    ),
    tags=["mindfulness", "reflection", "ethics", "decision-making"],
    examples=[
        "I'm struggling with anger at a coworker",
        "How should I think about this ethical dilemma?",
        "I feel overwhelmed by the news",
        "I'm not sure if I'm being fair to someone",
    ],
)

guide_skill = AgentSkill(
    id="guide",
    name="Mindful guidance for actions",
    description=(
        "Evaluate a proposed action or behavior and suggest a more mindful "
        "alternative if appropriate. Compassionate, never preachy."
    ),
    tags=["mindfulness", "guidance", "behavior", "compassion"],
    examples=[
        "I want to send an angry email to my boss",
        "Should I buy this product?",
        "I'm thinking of cutting someone out of my life",
        "How can I respond to this hurtful comment?",
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
        skills=[teach_skill, reflect_skill, guide_skill],
    )
