# Restaurant Agent

Multi-tenant restaurant chat agent with RAG, A2A, and MCP.

## Quick Start

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync --dev

# Copy env
cp .env.example .env
# Edit .env with your API keys

# Run tests
uv run pytest tests/ -v

# Start dev server
uv run uvicorn api.main:app --reload --port 8000

# Or with Docker
docker-compose -f docker/docker-compose.yml up --build
```

## Build Order
See CLAUDE.md for full architecture and conventions.

Week 1: Foundation — multi-tenant, DB, FastAPI skeleton
Week 2: RAG pipeline — Google Places → ChromaDB → retrieval
Week 3: Core agent — LangGraph + session + preference model
Week 4: Tools + Guardrails
Week 5: A2A + MCP
Week 6: Evaluation pipeline + widget + EKS deploy
