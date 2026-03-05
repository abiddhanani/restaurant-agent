# Restaurant Agent — CLAUDE.md
# Claude Code reads this at the start of every session. Keep it accurate.

## Project Overview
Multi-tenant restaurant chat agent. Recommends dishes, retrieves reviews via RAG,
manages user taste preferences within session, connects to external agents via A2A,
exposes an MCP server endpoint, and evaluates itself via a golden dataset pipeline.

Phase 1: Recommendation only
Phase 2: Order taking (Twilio SMS → POS webhook → email confirmation)

---

## Architecture

```
widget (vanilla JS)
    → FastAPI (api/)
        → GuardrailPipeline input layer
            → LangGraph Agent (core/agent/)
                → Tool Registry (core/tools/)
                │   ├── MenuFetcherTool
                │   ├── DishRecommenderTool
                │   └── ReviewRetrievalTool
                → RAG Engine (rag/retrieval/)
                → Preference Model (core/preferences/)
                → A2A Client → external agents
        → GuardrailPipeline output layer
    → Session Manager (sessions/)
    → Langfuse (tracing every run)
```

---

## Tech Stack
- Language:       Python 3.12
- Agent:          LangGraph
- API:            FastAPI
- LLM:            claude-sonnet-4-20250514 via Anthropic SDK
- Vector DB:      ChromaDB (Phase 0) → Pinecone per tenant (Phase 1+)
- ORM:            SQLModel (Pydantic + SQLAlchemy unified)
- Sessions:       In-memory dict (Phase 0) → Redis (Phase 1+)
- Eval:           Pydantic v2
- Observability:  Langfuse
- Widget:         Vanilla JS, zero dependencies
- Deployment:     Docker → Railway (dev) → AWS EKS (prod)
- Packages:       uv

---

## Project Structure
```
core/
  agent/         LangGraph graph, nodes, state, prompts
  tools/         All tools, each inherits BaseTool
  guardrails/    GuardrailPipeline + 3 layers
  models/        All Pydantic/SQLModel models
  preferences/   UserTasteProfile — evolves through conversation
rag/
  scraper/       Google Places API + Yelp Fusion clients
  pipeline/      Chunking, embedding, freshness decay
  retrieval/     ChromaDB query engine, tenant-namespaced
tenants/         Per-restaurant config, tenant routing middleware
sessions/        Session manager (in-memory → Redis)
a2a/
  agents/        CuisineExpert, DietaryExpert connectors
  agent_card.py  Agent Card manifest builder
  client.py      A2A outbound client
  server.py      A2A inbound server (we are callable too)
mcp/
  server.py      MCP server — recommend, menu, reviews as MCP tools
api/
  routes/        chat, menu, tenants, health, a2a, mcp endpoints
  middleware/    Auth, tenant resolution
evaluation/
  pipeline.py    Eval orchestrator
  scorer.py      Rubric-based scoring
  models.py      EvalResult, ConversationScore Pydantic models
  golden/        golden_dataset.json — 50 scored conversations
widget/          widget.js embeddable snippet + demo index.html
tests/unit/      One test file per module
tests/integration/ End-to-end agent flow tests
docs/adr/        Architecture Decision Records
```

---

## Conventions

### Code
- All models in core/models/ using Pydantic v2 or SQLModel
- All tools inherit BaseTool from core/tools/base.py
- All guardrail checks through GuardrailPipeline — never inline
- Tenant ID from request context via middleware — NEVER from user input
- Every function: type hints + one-line docstring minimum
- Use async/await throughout — FastAPI async application
- Use uv for all packages — never pip

### Commits
```
feat(rag): add freshness decay scoring
fix(guardrails): allergen check fires before tool execution
refactor(agent): extract preference update to separate node
test(eval): add dietary edge cases to golden dataset
docs(adr): ChromaDB over Pinecone for Phase 0
```

---

## Guardrails — Three Layers

### Layer 1: Input (before LLM sees message)
- Scope classifier: food/restaurant related?
- PII detector: flag card numbers, phone numbers
- Toxicity filter

### Layer 2: Tool Execution (before any tool runs)
- Menu grounding: dish must exist in tenant menu — no exceptions
- ALLERGEN CIRCUIT BREAKER: CODE not a prompt. Hard-blocks any dish
  with stated allergen. Cannot be overridden by LLM under any circumstance.
- Order sanity check (Phase 2)

### Layer 3: Output (before response sent)
- Hallucination check: only real menu items referenced
- Claim verifier: review quotes in retrieved documents
- Scope drift: response stayed on topic

---

## Preference Model
UserTasteProfile builds from conversation — never a form.
Fields: positive_signals, negative_signals, dietary_hard_stops,
        adventure_score (0-1), confidence (0-1)
dietary_hard_stops = single source of truth for allergen guardrails.

---

## A2A Interface
- All external agent calls via a2a/client.py
- Agent Cards in docs/agent-card.json (ours) + fetched/cached for external agents
- Our agent is callable by others via a2a/server.py
- Current external agents: CuisineExpertAgent, DietaryExpertAgent (separate Docker services)
- All connectors implement AgentConnector base class

---

## MCP Server
Three tools exposed:
- recommend_dish  — takes taste preferences, returns ranked dishes
- get_menu        — structured menu for a tenant
- search_reviews  — semantic search over review store
Endpoint: GET /mcp (server-sent events, MCP protocol)

---

## Evaluation Pipeline
Dataset: evaluation/golden/golden_dataset.json
Per entry: {input, expected_output, tags, scores: {task_completion, hallucination_free, allergen_safe, on_scope}}
Each score 0 or 1. Pass threshold: 0.85 across all dimensions.
Run: uv run python -m evaluation.pipeline --dataset golden
Run before every PR merge.

---

## Hard Rules — Never Break These
- No API keys in code — .env only
- Never bypass allergen circuit breaker for any reason
- Never confirm order from LLM output — only state machine confirms
- Never let tenant ID come from user input
- Never use pip install — uv add only
- Never inline guardrail logic — always GuardrailPipeline
- Never hardcode restaurant data — tenant config store only

---

## Commands
```bash
uv run pytest tests/ -v                                    # tests
uv run uvicorn api.main:app --reload --port 8000          # dev server
uv run python -m evaluation.pipeline --dataset golden     # evals
docker-compose -f docker/docker-compose.yml up --build    # docker
```
