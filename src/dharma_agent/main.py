"""Dharma Agent — A2A server entry point."""

import uvicorn
from dotenv import load_dotenv
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore

from dharma_agent.agent_card import build_agent_card
from dharma_agent.executor import DharmaAgentExecutor


HOST = "0.0.0.0"
PORT = 9999


def main() -> None:
    load_dotenv()

    agent_card = build_agent_card(host=HOST, port=PORT)

    request_handler = DefaultRequestHandler(
        agent_executor=DharmaAgentExecutor(),
        task_store=InMemoryTaskStore(),
    )

    app_builder = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=request_handler,
    )

    print(f"🪷 Dharma Agent listening on http://{HOST}:{PORT}")
    print(f"   Agent Card: http://{HOST}:{PORT}/.well-known/agent.json")
    uvicorn.run(app_builder.build(), host=HOST, port=PORT)


if __name__ == "__main__":
    main()
