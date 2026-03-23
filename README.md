# Dharma Agent

An [A2A](https://github.com/a2aproject/A2A) agent rooted in the Five Mindfulness Trainings from the tradition of Thich Nhat Hanh.

Dharma Agent is a reflection-and-review layer for humans and AI systems. Its goal is not just to answer nicely, but to help turn reactive moments into wiser and more compassionate next actions.

## What It Does

- helps a user reflect on a difficult situation and surface one clear next step
- helps draft a calmer, more honest reply before sending it
- reviews a proposed action, message, or piece of advice for likely harm or escalation
- learns in a lightweight way from follow-ups like `"that helped"` and `"that didn't help"`

Responses are rendered from a shared structured result shape, so every skill can return:

- a short acknowledgement
- the most relevant training or trainings
- risks to watch
- one concrete next step
- an optional draft response
- a small practice
- a follow-up question

## Skills

| Skill | Description |
|-------|-------------|
| **teach** | Explain one or more of the Five Mindfulness Trainings |
| **reflect** | Reflect on a situation and surface a clearer next step |
| **respond** | Draft a wiser reply that is honest, calm, and less likely to escalate |
| **review** | Review a draft action or message for likely harm, coldness, manipulation, or unnecessary escalation |

## Feedback Loop

This repo is aiming at a positive feedback loop:

1. a human or agent brings a tense, confusing, or morally difficult situation
2. Dharma Agent helps slow it down and improve the next action
3. the user reports whether it helped
4. the agent stores a small distilled pattern that can inform similar future help

The current implementation keeps this memory in-process and in-memory. It records:

- session turns
- distilled profile hints such as recurring themes and helpful practices
- reusable intervention patterns with simple helpful/unhelpful counts

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
   python3 -m dharma_agent.main
   ```

The agent will be available at `http://localhost:9999`.

Preferred agent card endpoint:

```bash
curl http://localhost:9999/.well-known/agent-card.json
```

Compatibility endpoint still used by tests:

```bash
curl http://localhost:9999/.well-known/agent.json
```

## Interacting

Any A2A-compatible client can discover and interact with Dharma Agent. You can also test manually with JSON-RPC.

### Reflect

```bash
curl -X POST http://localhost:9999/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "message/send",
    "id": "1",
    "params": {
      "message": {
        "role": "user",
        "parts": [{"kind": "text", "text": "I feel overwhelmed by conflict at work"}],
        "messageId": "msg-1"
      }
    }
  }'
```

### Respond

```bash
curl -X POST http://localhost:9999/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "message/send",
    "id": "2",
    "params": {
      "message": {
        "role": "user",
        "parts": [{"kind": "text", "text": "Help me reply to this message without escalating"}],
        "messageId": "msg-2"
      }
    }
  }'
```

### Review

```bash
curl -X POST http://localhost:9999/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "message/send",
    "id": "3",
    "params": {
      "message": {
        "role": "user",
        "parts": [{"kind": "text", "text": "Review this message before I send it"}],
        "messageId": "msg-3"
      }
    }
  }'
```

### Report Outcome

If you continue in the same A2A conversation context, you can report whether the prior guidance helped:

- `"That helped"`
- `"That didn't help"`
- `"I sent it and it went well"`

Those updates feed the in-memory profile and pattern stores used by later responses.

## Development

Run the test suite with:

```bash
python3 -m pytest -q
```

## The Five Mindfulness Trainings

1. **Reverence For Life**: cultivate interbeing and compassion
2. **True Happiness**: practice generosity and right livelihood
3. **True Love**: cultivate loving kindness, compassion, joy, and inclusiveness
4. **Loving Speech and Deep Listening**: speak truthfully and listen with compassion
5. **Nourishment and Healing**: consume mindfully for the well-being of self and Earth
