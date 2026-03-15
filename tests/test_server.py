"""Integration tests for the Dharma Agent A2A server."""

import pytest
from unittest.mock import patch

import httpx
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore

from dharma_agent.agent_card import build_agent_card
from dharma_agent.executor import DharmaAgentExecutor


@pytest.fixture
def app():
    """Build a test Starlette app with no Anthropic client (fallback mode)."""
    with patch.dict("os.environ", {"ANTHROPIC_API_KEY": ""}, clear=False):
        agent_card = build_agent_card(url="http://localhost:9999/")
        executor = DharmaAgentExecutor()
        handler = DefaultRequestHandler(
            agent_executor=executor,
            task_store=InMemoryTaskStore(),
        )
        app_builder = A2AStarletteApplication(
            agent_card=agent_card,
            http_handler=handler,
        )
        return app_builder.build()


# ---------------------------------------------------------------------------
# Agent Card
# ---------------------------------------------------------------------------


class TestAgentCard:
    """Tests for the /.well-known/agent.json endpoint."""

    @pytest.mark.asyncio
    async def test_get_agent_card(self, app):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/.well-known/agent.json")
            assert resp.status_code == 200
            data = resp.json()
            assert data["name"] == "Dharma Agent"
            assert data["capabilities"]["streaming"] is True
            assert len(data["skills"]) == 3
            skill_ids = [s["id"] for s in data["skills"]]
            assert "teach" in skill_ids
            assert "reflect" in skill_ids
            assert "guide" in skill_ids


# ---------------------------------------------------------------------------
# message/send
# ---------------------------------------------------------------------------


class TestMessageSend:
    """Tests for the message/send JSON-RPC endpoint."""

    @pytest.mark.asyncio
    async def test_send_teach_message(self, app):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            payload = {
                "jsonrpc": "2.0",
                "id": "1",
                "method": "message/send",
                "params": {
                    "message": {
                        "role": "user",
                        "parts": [{"kind": "text", "text": "Explain the first training"}],
                        "messageId": "msg-1",
                    }
                },
            }
            resp = await client.post("/", json=payload)
            assert resp.status_code == 200
            data = resp.json()
            assert "error" not in data
            assert "result" in data

    @pytest.mark.asyncio
    async def test_send_empty_message(self, app):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            payload = {
                "jsonrpc": "2.0",
                "id": "2",
                "method": "message/send",
                "params": {
                    "message": {
                        "role": "user",
                        "parts": [{"kind": "text", "text": "   "}],
                        "messageId": "msg-2",
                    }
                },
            }
            resp = await client.post("/", json=payload)
            assert resp.status_code == 200
            data = resp.json()
            assert "error" not in data


# ---------------------------------------------------------------------------
# message/stream
# ---------------------------------------------------------------------------


class TestMessageStream:
    """Tests for the message/stream SSE endpoint."""

    @pytest.mark.asyncio
    async def test_stream_returns_sse(self, app):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            payload = {
                "jsonrpc": "2.0",
                "id": "3",
                "method": "message/stream",
                "params": {
                    "message": {
                        "role": "user",
                        "parts": [{"kind": "text", "text": "What are the trainings?"}],
                        "messageId": "msg-3",
                    }
                },
            }
            resp = await client.post("/", json=payload)
            assert resp.status_code == 200
            assert "text/event-stream" in resp.headers.get("content-type", "")
