# Dharma Agent

An [A2A](https://github.com/a2aproject/A2A) agent rooted in the Five Mindfulness Trainings from the tradition of Thich Nhat Hanh.

Dharma Agent offers teachings, reflections, and mindful guidance to both humans and AI agents through the Agent-to-Agent protocol.

## Skills

| Skill | Description |
|-------|-------------|
| **teach** | Explain any of the Five Mindfulness Trainings with context and examples |
| **reflect** | Reflect on a situation through the lens of the Trainings |
| **guide** | Evaluate a proposed action and suggest a more mindful alternative |

## Setup

1. Clone and enter the project:
   ```bash
   cd dharma-agent
   ```

2. Create a `.env` file with your Anthropic API key:
   ```bash
   cp .env.example .env
   # Edit .env and add your key
   ```

3. Install dependencies:
   ```bash
   pip install -e .
   ```

4. Run the agent:
   ```bash
   python -m dharma_agent.main
   ```

The agent will be available at `http://localhost:9999` and its Agent Card at `http://localhost:9999/.well-known/agent.json`.

## Interacting

Any A2A-compatible client can discover and interact with Dharma Agent. You can also test manually:

```bash
# Check the Agent Card
curl http://localhost:9999/.well-known/agent.json

# Send a message (A2A JSON-RPC)
curl -X POST http://localhost:9999/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "message/send",
    "id": "1",
    "params": {
      "message": {
        "role": "user",
        "parts": [{"kind": "text", "text": "What are the Five Mindfulness Trainings?"}],
        "messageId": "msg-1"
      }
    }
  }'
```

## The Five Mindfulness Trainings

1. **Reverence For Life** — Cultivate interbeing and compassion
2. **True Happiness** — Practice generosity and right livelihood
3. **True Love** — Cultivate loving kindness, compassion, joy, and inclusiveness
4. **Loving Speech and Deep Listening** — Speak truthfully, listen with compassion
5. **Nourishment and Healing** — Consume mindfully for well-being of self and Earth
