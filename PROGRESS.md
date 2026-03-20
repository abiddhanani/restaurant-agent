# Restaurant Agent — Progress Tracker

**Last Updated:** 2026-03-19
**Current Story:** RA-12

---

## Sprint Overview (6 Weeks → Phase 0 MVP)

| Week | Stories | Status |
|------|---------|--------|
| 1 | RA-1 – RA-3 | ✅ Complete |
| 2 | RA-4 – RA-6 | ✅ Complete |
| 3 | RA-7 – RA-10 | ✅ Complete |
| 4 | RA-11 – RA-14 | 🔄 In Progress |
| 5 | RA-15 – RA-18 | ⬜ Not Started |
| 6 | RA-19 – RA-21 | ⬜ Not Started |

---

## Week 1: Foundation & Database

### RA-1: Project Foundation & Database Setup
**Status:** ✅ Complete
**Jira:** RA-1
**Objective:** Working FastAPI app with SQLite, basic tenant config

### RA-2: Multi-Tenant Middleware & Routing
**Status:** ✅ Complete
**Jira:** RA-2
**Objective:** Tenant isolation working end-to-end

### RA-3: Menu Data Model & CRUD
**Status:** ✅ Complete
**Jira:** RA-3
**Objective:** Load and query menu items per tenant

---

## Week 2: RAG Pipeline

### RA-4: Google Places API Integration
**Status:** ✅ Complete
**Jira:** RA-4
**Objective:** Fetch real reviews from Google Places API

### RA-5: Review Chunking & Embedding
**Status:** ✅ Complete
**Jira:** RA-5
**Objective:** Chunk reviews, embed, store in ChromaDB

### RA-6: Retrieval Engine with Freshness Scoring
**Status:** ✅ Complete
**Jira:** RA-6
**Objective:** Query ChromaDB with freshness decay working

---

## Week 3: Agent Core & A2A

### RA-7: LangGraph Agent Graph Foundation
**Status:** ✅ Complete
**Jira:** RA-7
**Objective:** Basic conversational agent running

### RA-8: Session Management (In-Memory)
**Status:** ✅ Complete
**Jira:** RA-8
**Objective:** Session persistence across messages

### RA-9: Preference Model Integration
**Status:** ✅ Complete
**Jira:** RA-9
**Objective:** Taste profile evolves through conversation

### RA-10: A2A Server & Agent Card
**Status:** ✅ Complete
**Jira:** RA-10
**Objective:** Agent Card served, A2A endpoint working

---

## Week 4: Tools

### RA-11: Menu Fetcher Tool
**Status:** ✅ Complete
**Jira:** RA-11
**Objective:** Agent can query available dishes

### RA-12: Review Retrieval Tool
**Status:** ⬜ Not Started
**Jira:** RA-12
**Objective:** Agent retrieves relevant reviews from ChromaDB

### RA-13: Dish Recommender Tool
**Status:** ⬜ Not Started
**Jira:** RA-13
**Objective:** Cross-reference menu + taste profile + reviews

### RA-14: External Cuisine Agent (Stub)
**Status:** ⬜ Not Started
**Jira:** RA-14
**Objective:** A2A client calls external cuisine expert

---

## Week 5: Guardrails & MCP

### RA-15: Input Guardrails (Layer 1)
**Status:** ⬜ Not Started
**Jira:** RA-15
**Objective:** Scope, PII, toxicity filtering

### RA-16: Tool Execution Guardrails (Layer 2)
**Status:** ⬜ Not Started
**Jira:** RA-16
**Objective:** Allergen circuit breaker, menu grounding

### RA-17: Output Guardrails (Layer 3)
**Status:** ⬜ Not Started
**Jira:** RA-17
**Objective:** Hallucination check, grounding verification

### RA-18: MCP Server Implementation
**Status:** ⬜ Not Started
**Jira:** RA-18
**Objective:** MCP endpoint working, testable from Claude

---

## Week 6: Evaluation & Deployment

### RA-19: Golden Dataset & Eval Pipeline
**Status:** ⬜ Not Started
**Jira:** RA-19
**Objective:** 10+ scored conversations, pipeline running

### RA-20: Embeddable Widget
**Status:** ⬜ Not Started
**Jira:** RA-20
**Objective:** Widget embeddable on test restaurant site

### RA-21: Deploy to Railway + Observability
**Status:** ⬜ Not Started
**Jira:** RA-21
**Objective:** Live deployment, Langfuse tracing working

---

## How to Use This Tracker

1. **Start a story:** Pull the Jira story (e.g. `RA-2`) for full acceptance criteria and tasks
2. **Implement** with Claude Code, following CLAUDE.md conventions
3. **Run tests** — `uv run pytest tests/ -v`
4. **Mark story complete** — change status from ⬜ to ✅ and update "Last Updated"
5. **Transition Jira ticket** to Done
6. **Commit** after each story completion

---

## Story Status Legend

- ⬜ Not Started
- 🔄 In Progress
- ✅ Complete
- ⏸️ Blocked (note reason in Jira ticket)

---

## Notes

- Each story is independently testable
- Don't start RA-4 until RA-1–RA-3 are ✅ (dependencies matter)
- If a story is blocked, move to next available story in same week
- Update "Last Updated" and "Current Story" at top when you start work
