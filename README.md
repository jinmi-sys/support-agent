# Support Agent

![MiMo Powered](https://img.shields.io/badge/Powered_by-MiMo_V2.5_Pro-10B981?style=flat-square&logo=xiaomi&logoColor=white)
![Python 3.11+](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)
![License: MIT](https://img.shields.io/badge/License-MIT-10B981?style=flat-square)
![Tests](https://img.shields.io/badge/Tests-Passing-10B981?style=flat-square)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=flat-square&logo=docker&logoColor=white)

**AI-powered autonomous customer support agent** built on Xiaomi MiMo-V2.5-Pro. Handles ticket triage, sentiment analysis, knowledge retrieval, and multi-channel resolution — fully autonomous, production-ready.

---

## Overview

Support Agent leverages Xiaomi's MiMo-V2.5-Pro reasoning model to deliver intelligent, context-aware customer support across email, live chat, and Discord. The system autonomously triages incoming tickets by priority, analyzes customer sentiment in real-time, retrieves relevant knowledge base articles via RAG, and resolves issues with minimal human intervention.

MiMo's advanced reasoning capabilities power every decision point — from understanding nuanced customer frustration to selecting the optimal resolution strategy based on historical patterns and knowledge base context.

## Key Features

- **🎯 Intelligent Ticket Triage** — MiMo-driven priority classification (P0-P3) with automatic category detection and SLA assignment
- **😊 Sentiment Analysis** — Real-time emotional state detection with trend tracking across conversation turns
- **📚 Knowledge Retrieval** — RAG-based semantic search over knowledge base with vector embeddings and relevance scoring
- **💬 Multi-Channel Resolution** — Unified support across email, live chat, and Discord with channel-specific formatting
- **🧠 MiMo Reasoning** — Deep chain-of-thought reasoning for complex issue resolution, escalation decisions, and response generation
- **📊 Metrics & Analytics** — Track resolution rates, response times, CSAT scores, and agent performance
- **🔄 Autonomous Workflow** — End-to-end ticket lifecycle management from intake to resolution without manual routing
- **🐳 Docker Ready** — Full containerized deployment with Redis and PostgreSQL

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      SUPPORT AGENT SYSTEM                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                      │
│  │  Email    │  │ Live Chat│  │ Discord  │   ◄── Channel Layer  │
│  │ Channel   │  │ Channel  │  │ Channel  │                      │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘                      │
│       │              │              │                            │
│       └──────────────┼──────────────┘                           │
│                      ▼                                           │
│  ┌─────────────────────────────────────┐                        │
│  │         Support Engine              │   ◄── Orchestration    │
│  │  (Intake → Triage → Resolve)        │                        │
│  └───────────┬──────────┬──────────────┘                        │
│              │          │                                        │
│    ┌─────────▼──┐  ┌───▼──────────┐                            │
│    │   Triage   │  │  Sentiment   │   ◄── Analysis Layer       │
│    │  (P0-P3)   │  │  Analysis    │                            │
│    └─────────┬──┘  └───┬──────────┘                            │
│              │          │                                        │
│              └────┬─────┘                                        │
│                   ▼                                              │
│  ┌─────────────────────────────────────┐                        │
│  │          Knowledge Base             │   ◄── RAG Pipeline    │
│  │  Retriever ← → Embeddings          │                        │
│  └───────────────┬─────────────────────┘                        │
│                  ▼                                               │
│  ┌─────────────────────────────────────┐                        │
│  │      MiMo V2.5-Pro Integration      │   ◄── LLM Core       │
│  │  Client + Prompts + Reasoning       │                        │
│  └─────────────────────────────────────┘                        │
│                                                                  │
│  ┌─────────────────────────────────────┐                        │
│  │        Utils & Infrastructure       │                        │
│  │  Logger · Config · Metrics          │   ◄── Foundation      │
│  └─────────────────────────────────────┘                        │
└─────────────────────────────────────────────────────────────────┘
```

## Quick Start

### Prerequisites

- Python 3.11+
- Redis 7+
- PostgreSQL 15+
- MiMo API key (from Xiaomi)

### Installation

```bash
# Clone the repository
git clone https://github.com/jinmi-sys/support-agent.git
cd support-agent

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Copy environment template
cp .env.example .env
# Edit .env with your API keys

# Run the agent
python -m support_agent
```

### Docker Deployment

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f support-agent
```

### CLI Usage

```bash
# Process a single ticket
support-agent process --ticket-id TICKET-001 --channel email

# Start the multi-channel listener
support-agent listen --channels email,chat,discord

# Run triage on pending tickets
support-agent triage --status pending

# View metrics
support-agent metrics --period 24h
```

## Configuration

Configuration is managed via `config/config.yaml` or environment variables:

```yaml
# MiMo Configuration
mimo:
  api_key: "${MIMO_API_KEY}"
  model: "MiMo-V2.5-Pro"
  max_tokens: 4096
  temperature: 0.3

# Knowledge Base
knowledge:
  embedding_model: "text-embedding-3-small"
  chunk_size: 512
  top_k: 5

# Channels
channels:
  email:
    imap_host: "imap.gmail.com"
    smtp_host: "smtp.gmail.com"
  chat:
    websocket_url: "wss://chat.example.com/ws"
  discord:
    token: "${DISCORD_BOT_TOKEN}"

# Database
database:
  url: "postgresql://user:pass@localhost:5432/support_agent"

# Redis
redis:
  url: "redis://localhost:6379/0"
```

## API Reference

### REST Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/tickets` | Create new support ticket |
| `GET` | `/api/v1/tickets/{id}` | Get ticket details |
| `POST` | `/api/v1/tickets/{id}/resolve` | Trigger autonomous resolution |
| `GET` | `/api/v1/metrics` | Get support metrics |
| `POST` | `/api/v1/triage` | Classify ticket priority |
| `POST` | `/api/v1/sentiment` | Analyze text sentiment |

### Python API

```python
from support_agent.core.engine import SupportEngine
from support_agent.mimo_integration.client import MiMoClient

# Initialize engine
engine = SupportEngine(config_path="config/config.yaml")

# Process a ticket
result = await engine.process_ticket(
    ticket_id="TICKET-001",
    subject="Payment not processed",
    body="I made a payment 3 days ago but my order still shows unpaid...",
    channel="email",
    customer_email="user@example.com"
)

print(result.priority)      # P1
print(result.sentiment)      # frustrated
print(result.resolution)     # Full resolution text
print(result.confidence)     # 0.94
```

## Project Structure

```
support-agent/
├── src/support_agent/
│   ├── __init__.py
│   ├── __main__.py              # CLI entry point
│   ├── core/
│   │   ├── engine.py            # Main support engine
│   │   ├── triage.py            # Ticket priority classification
│   │   ├── sentiment.py         # Sentiment analysis
│   │   └── resolver.py          # Autonomous resolution
│   ├── channels/
│   │   ├── __init__.py          # Channel abstraction
│   │   ├── email_channel.py     # Email support
│   │   ├── chat_channel.py      # Live chat
│   │   └── discord_channel.py   # Discord support
│   ├── knowledge/
│   │   ├── __init__.py          # Knowledge base module
│   │   ├── retriever.py         # RAG retrieval
│   │   └── embeddings.py        # Vector embeddings
│   ├── mimo_integration/
│   │   ├── __init__.py          # MiMo client
│   │   ├── client.py            # API client
│   │   └── prompts.py           # System prompts
│   └── utils/
│       ├── __init__.py
│       ├── logger.py            # Structured logging
│       ├── config.py            # Configuration
│       └── metrics.py           # Metrics tracking
├── tests/
│   ├── test_engine.py
│   ├── test_triage.py
│   └── test_sentiment.py
├── config/
│   └── config.example.yaml
├── docs/
│   └── index.html               # Live demo dashboard
├── scripts/
│   └── setup.sh
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
├── .env.example
├── .gitignore
├── LICENSE
└── CHANGELOG.md
```

## License

MIT License — see [LICENSE](LICENSE) for details.

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

---

Built with ❤️ using [Xiaomi MiMo-V2.5-Pro](https://github.com/XiaomiMiMo/MiMo)
