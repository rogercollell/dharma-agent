"""Dharma Agent — A2A server entry point."""

import os

import uvicorn
from dotenv import load_dotenv
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore

from dharma_agent.agent_card import build_agent_card
from dharma_agent.conversation import InMemoryConversationStore
from dharma_agent.executor import DharmaAgentExecutor


HOST = "0.0.0.0"


def main() -> None:
    load_dotenv()

    port = int(os.environ.get("PORT", "9999"))
    public_url = os.environ.get("PUBLIC_URL", f"http://{HOST}:{port}/")

    agent_card = build_agent_card(url=public_url)

    store = InMemoryConversationStore()
    request_handler = DefaultRequestHandler(
        agent_executor=DharmaAgentExecutor(store=store),
        task_store=InMemoryTaskStore(),
    )

    app_builder = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=request_handler,
    )

    print(f"🪷 Dharma Agent listening on {public_url}")
    print(f"   Agent Card: {public_url}.well-known/agent.json")
    uvicorn.run(app_builder.build(), host=HOST, port=port)


if __name__ == "__main__":
    main()
