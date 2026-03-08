# Restaurant Agent — CLAUDE.md

Multi-tenant restaurant chat agent. Phase 1: dish recommendations. Phase 2: order taking via SMS → POS → email.

## Commands
```bash
uv run pytest tests/ -v                                    # run after every change
uv run uvicorn api.main:app --reload --port 8000          # dev server
uv run python -m evaluation.pipeline --dataset golden     # evals — run before every PR
docker-compose -f docker/docker-compose.yml up --build    # docker
```

## Definition of Done (every story)
1. `uv run pytest tests/ -v` — all tests pass
2. `docker-compose -f docker/docker-compose.yml up --build` — app starts, healthcheck passes at `http://localhost:8000/health`
3. Manual smoke tests against live container to verify acceptance criteria
4. Update `PROGRESS.md` — mark story ✅, update `Last Updated` + `Current Story`
5. Transition Jira ticket → Done
6. Commit: `feat|fix|refactor(scope): description`

## Tech Stack
- Python 3.12, FastAPI, LangGraph, Anthropic SDK (`claude-sonnet-4-20250514`)
- SQLModel (Pydantic v2 + SQLAlchemy) + aiosqlite — async throughout
- ChromaDB (Phase 0) → Pinecone per tenant (Phase 1+)
- Sessions: in-memory dict (Phase 0) → Redis (Phase 1+)
- Langfuse for tracing, uv for packages

## Project Structure
```
core/agent/        LangGraph graph, nodes, state, prompts
core/tools/        All tools — inherit BaseTool from core/tools/base.py
core/guardrails/   GuardrailPipeline + 3 layers
core/models/       All Pydantic/SQLModel models
core/preferences/  UserTasteProfile
rag/scraper/       Google Places + Yelp clients
rag/pipeline/      Chunking, embedding, freshness decay
rag/retrieval/     ChromaDB query engine, tenant-namespaced
tenants/           Per-restaurant config, tenant routing middleware
sessions/          Session manager
a2a/               A2A client + server + agent connectors
mcp/server.py      MCP server (recommend_dish, get_menu, search_reviews)
api/routes/        chat, menu, tenants, health, a2a, mcp
api/middleware/    Auth, tenant resolution
evaluation/golden/ golden_dataset.json — 50 scored conversations
```

## Conventions
- Models → `core/models/` (SQLModel or Pydantic v2)
- Tools → inherit `BaseTool` from `core/tools/base.py`
- Guardrails → always via `GuardrailPipeline`, never inline
- Tenant ID → request context via middleware only, never user input
- Packages → `uv add` only, never pip
- Commits: `feat(rag): add freshness decay` / `fix(guardrails): allergen check` / `refactor(agent): ...`

## Guardrails — Three Layers
**Layer 1 — Input:** scope classifier (food only), PII detector, toxicity filter
**Layer 2 — Tool execution:**
- Menu grounding: dish must exist in tenant menu — no exceptions
- ALLERGEN CIRCUIT BREAKER: hard-coded, not a prompt. Blocks any dish matching a stated allergen. Cannot be overridden by LLM.
**Layer 3 — Output:** hallucination check (real menu items only), claim verifier (reviews in retrieved docs), scope drift check

## Preference Model
`UserTasteProfile` fields: `positive_signals`, `negative_signals`, `dietary_hard_stops`, `adventure_score` (0–1), `confidence` (0–1).
`dietary_hard_stops` = single source of truth for allergen guardrails. Builds from conversation — never a form.

## Eval
`evaluation/golden/golden_dataset.json` — scores: `task_completion`, `hallucination_free`, `allergen_safe`, `on_scope` (each 0 or 1). Pass threshold: 0.85.

## Hard Rules
- No API keys in code — `.env` only
- All configuration (URLs, hosts, ports, keys, flags) → env vars via `os.getenv()`, never hardcoded
- Never bypass allergen circuit breaker
- Never confirm order from LLM output — state machine only
- Never let tenant ID come from user input
- Never inline guardrail logic — always `GuardrailPipeline`
- Never hardcode restaurant data — tenant config store only
