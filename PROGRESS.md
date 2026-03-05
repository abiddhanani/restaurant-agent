# Restaurant Agent — Progress Tracker

**Last Updated:** Not started
**Current Story:** S01 (Foundation)

---

## Sprint Overview (6 Weeks → Phase 0 MVP)

| Week | Stories | Status |
|------|---------|--------|
| 1 | S01-S03 | ⬜ Not Started |
| 2 | S04-S06 | ⬜ Not Started |
| 3 | S07-S10 | ⬜ Not Started |
| 4 | S11-S14 | ⬜ Not Started |
| 5 | S15-S18 | ⬜ Not Started |
| 6 | S19-S21 | ⬜ Not Started |

---

## Week 1: Foundation & Database

### S01: Project Foundation & Database Setup
**Status:** ⬜ Not Started  
**File:** [docs/stories/S01-foundation.md](docs/stories/S01-foundation.md)  
**Objective:** Working FastAPI app with SQLite, basic tenant config

### S02: Multi-Tenant Middleware & Routing
**Status:** ⬜ Not Started  
**File:** [docs/stories/S02-multitenant.md](docs/stories/S02-multitenant.md)  
**Objective:** Tenant isolation working end-to-end

### S03: Menu Data Model & CRUD
**Status:** ⬜ Not Started  
**File:** [docs/stories/S03-menu-crud.md](docs/stories/S03-menu-crud.md)  
**Objective:** Load and query menu items per tenant

---

## Week 2: RAG Pipeline

### S04: Google Places API Integration
**Status:** ⬜ Not Started  
**File:** [docs/stories/S04-google-places.md](docs/stories/S04-google-places.md)  
**Objective:** Fetch real reviews from Google Places API

### S05: Review Chunking & Embedding
**Status:** ⬜ Not Started  
**File:** [docs/stories/S05-chunking-embedding.md](docs/stories/S05-chunking-embedding.md)  
**Objective:** Chunk reviews, embed, store in ChromaDB

### S06: Retrieval Engine with Freshness Scoring
**Status:** ⬜ Not Started  
**File:** [docs/stories/S06-retrieval-engine.md](docs/stories/S06-retrieval-engine.md)  
**Objective:** Query ChromaDB with freshness decay working

---

## Week 3: Agent Core & A2A

### S07: LangGraph Agent Graph Foundation
**Status:** ⬜ Not Started  
**File:** [docs/stories/S07-langgraph-foundation.md](docs/stories/S07-langgraph-foundation.md)  
**Objective:** Basic conversational agent running

### S08: Session Management (In-Memory)
**Status:** ⬜ Not Started  
**File:** [docs/stories/S08-session-management.md](docs/stories/S08-session-management.md)  
**Objective:** Session persistence across messages

### S09: Preference Model Integration
**Status:** ⬜ Not Started  
**File:** [docs/stories/S09-preference-model.md](docs/stories/S09-preference-model.md)  
**Objective:** Taste profile evolves through conversation

### S10: A2A Server & Agent Card
**Status:** ⬜ Not Started  
**File:** [docs/stories/S10-a2a-server.md](docs/stories/S10-a2a-server.md)  
**Objective:** Agent Card served, A2A endpoint working

---

## Week 4: Tools

### S11: Menu Fetcher Tool
**Status:** ⬜ Not Started  
**File:** [docs/stories/S11-menu-fetcher-tool.md](docs/stories/S11-menu-fetcher-tool.md)  
**Objective:** Agent can query available dishes

### S12: Review Retrieval Tool
**Status:** ⬜ Not Started  
**File:** [docs/stories/S12-review-retrieval-tool.md](docs/stories/S12-review-retrieval-tool.md)  
**Objective:** Agent retrieves relevant reviews from ChromaDB

### S13: Dish Recommender Tool
**Status:** ⬜ Not Started  
**File:** [docs/stories/S13-dish-recommender.md](docs/stories/S13-dish-recommender.md)  
**Objective:** Cross-reference menu + taste profile + reviews

### S14: External Cuisine Agent (Stub)
**Status:** ⬜ Not Started  
**File:** [docs/stories/S14-cuisine-agent-stub.md](docs/stories/S14-cuisine-agent-stub.md)  
**Objective:** A2A client calls external cuisine expert

---

## Week 5: Guardrails & MCP

### S15: Input Guardrails (Layer 1)
**Status:** ⬜ Not Started  
**File:** [docs/stories/S15-input-guardrails.md](docs/stories/S15-input-guardrails.md)  
**Objective:** Scope, PII, toxicity filtering

### S16: Tool Execution Guardrails (Layer 2)
**Status:** ⬜ Not Started  
**File:** [docs/stories/S16-tool-guardrails.md](docs/stories/S16-tool-guardrails.md)  
**Objective:** Allergen circuit breaker, menu grounding

### S17: Output Guardrails (Layer 3)
**Status:** ⬜ Not Started  
**File:** [docs/stories/S17-output-guardrails.md](docs/stories/S17-output-guardrails.md)  
**Objective:** Hallucination check, grounding verification

### S18: MCP Server Implementation
**Status:** ⬜ Not Started  
**File:** [docs/stories/S18-mcp-server.md](docs/stories/S18-mcp-server.md)  
**Objective:** MCP endpoint working, testable from Claude

---

## Week 6: Evaluation & Deployment

### S19: Golden Dataset & Eval Pipeline
**Status:** ⬜ Not Started  
**File:** [docs/stories/S19-eval-pipeline.md](docs/stories/S19-eval-pipeline.md)  
**Objective:** 10+ scored conversations, pipeline running

### S20: Embeddable Widget
**Status:** ⬜ Not Started  
**File:** [docs/stories/S20-widget.md](docs/stories/S20-widget.md)  
**Objective:** Widget embeddable on test restaurant site

### S21: Deploy to Railway + Observability
**Status:** ⬜ Not Started  
**File:** [docs/stories/S21-deploy.md](docs/stories/S21-deploy.md)  
**Objective:** Live deployment, Langfuse tracing working

---

## How to Use This Tracker

1. **Start a story:** Open the story file in `docs/stories/`
2. **Check off tasks** as you complete them (in the story file)
3. **Run tests** listed in "Acceptance Criteria"
4. **Mark story complete** when all checkboxes + tests pass
5. **Update this file** — change status from ⬜ to ✅ and update "Last Updated"
6. **Commit** after each story completion

---

## Story Status Legend

- ⬜ Not Started
- 🔄 In Progress  
- ✅ Complete
- ⏸️ Blocked (note reason in story file)

---

## Notes

- Each story is independently testable
- Don't start S04 until S01-S03 are ✅ (dependencies matter)
- If a story is blocked, move to next available story in same week
- Update "Last Updated" and "Current Story" at top when you start work
