# Generalization Plan — Multi-Domain Catalog Agent

## Goal

Transform the restaurant-specific agent into a domain-agnostic platform that can be deployed for any business with a product/service catalog — restaurants, hair salons, software companies, construction firms, etc.

The pitch: "Add an AI sales assistant to your website in 10 minutes. Upload your catalog, embed the widget, it learns your customers."

---

## What Changes (and What Doesn't)

**Stays the same:** LangGraph graph, RAG pipeline architecture, guardrail pipeline structure, A2A protocol, MCP server, widget embed mechanism, Railway deployment.

**Gets generalized:** Data models, tool names/descriptions, system prompts, guardrail keyword lists, tenant config, preference extraction, seed data.

---

## Stories

### GEN-1: Generalize Data Models
**Files:** `core/models/menu.py`, `core/models/preference.py`, `core/models/tenant.py`, `core/agent/state.py`, `core/models/session.py`

**Changes:**
- `MenuItem` → `CatalogItem` with `attributes: dict` replacing `spice_level`, `allergens`, `dietary_tags`
- `UserTasteProfile` → `CustomerProfile` with domain-agnostic fields:
  - `positive_signals`, `negative_signals` stay (already generic enough)
  - `dietary_hard_stops` → `hard_stops` (works for allergens, budget limits, style constraints)
  - `adventure_score` → `openness_score` (applies to any domain)
- `TenantConfig`:
  - `restaurant_name` → `business_name`
  - Remove `google_place_id`, `yelp_business_id` (move to `domain_config: dict`)
  - Add `industry: str` (e.g. "restaurant", "salon", "software", "construction")
  - `widget_welcome_message` default → "Hi! How can I help you today?"
- Update all imports and references across the codebase
- Update DB seed: `core/db/init.py`, `core/db/seed.py`
- Update API route `/menu` → `/catalog`, tags and descriptions

**Acceptance criteria:**
- All existing tests pass with renamed models
- `uv run pytest tests/ -v` green

---

### GEN-2: Generalize Tools
**Files:** `core/tools/menu_fetcher.py`, `core/tools/dish_recommender.py`, `core/tools/review_retrieval.py`

**Changes:**
- `MenuFetcherTool` → `CatalogFetcherTool` — fetch `CatalogItem`s, category filter becomes generic
- `DishRecommenderTool` → `RecommenderTool` — same scoring logic, allergen → hard_stop constraint check
- `ReviewRetrievalTool` stays (reviews are universal), update `dish_mentioned` → `item_mentioned`
- Tool names used in agent: `menu_fetcher` → `catalog_fetcher`, `dish_recommender` → `recommender`
- `get_cuisine_info` → `get_domain_context` (A2A call to domain expert)

**Acceptance criteria:**
- Agent still completes a recommendation conversation end-to-end
- Tests pass

---

### GEN-3: Generalize Agent Prompts
**Files:** `core/agent/nodes.py`, `core/agent/prompts.py` (if exists)

**Changes:**
- System prompt: inject `business_name` and `industry` from tenant config at runtime
  - Template: "You are a helpful assistant for {business_name}. You help customers find {industry_item_noun} they'll love."
- Tool descriptions: replace "dish", "menu", "restaurant" with `{item_noun}`, `{catalog_noun}`, `{business_type}`
- Out-of-scope fallback message: "I can only help with {business_type} questions."
- Industry config map (in tenant or a separate `IndustryConfig`):
  ```python
  INDUSTRY_VOCAB = {
      "restaurant": {"item_noun": "dish", "catalog_noun": "menu", "business_type": "food and restaurant"},
      "salon":      {"item_noun": "service", "catalog_noun": "services", "business_type": "hair and beauty"},
      "software":   {"item_noun": "product", "catalog_noun": "catalog", "business_type": "software and products"},
  }
  ```

**Acceptance criteria:**
- Prompt changes dynamically based on tenant's `industry`
- Tests pass

---

### GEN-4: Generalize Guardrails
**Files:** `core/guardrails/layer1_input.py`, `core/guardrails/layer2_tool.py`, `core/guardrails/layer3_output.py`

**Changes:**
- Layer 1 — Scope classifier:
  - `_FOOD_KEYWORDS` → `_SCOPE_KEYWORDS` loaded from tenant config or `IndustryConfig`
  - Each industry provides its own keyword set
  - Out-of-scope message uses tenant's `business_type`
- Layer 2 — Tool execution:
  - `AllergenCircuitBreaker` → `HardStopConstraintChecker` — same logic, renamed fields
  - `MenuGroundingValidator` → `CatalogGroundingValidator`
- Layer 3 — Output:
  - `HallucinationChecker` validates against `CatalogItem` names (not dish names)
  - `ScopeDriftChecker` uses industry keyword list

**Acceptance criteria:**
- Guardrails still block out-of-scope, still enforce hard stops
- Tests pass

---

### GEN-5: Generalize Preference Extraction
**Files:** `core/preferences/profile.py`

**Changes:**
- `PreferenceExtractor` currently hardcodes food allergens and vegan/vegetarian patterns
- Move allergen keyword list → `domain_config` on tenant (each industry defines its own constraint keywords)
- Vegan/vegetarian patterns → generic "lifestyle/preference" patterns loaded from industry config
- `adventure_score` update words → domain-agnostic or loaded from industry config
- `UserTasteProfile` already renamed to `CustomerProfile` in GEN-1

**Acceptance criteria:**
- Preference extraction works for non-food domains (no food-specific hard-coding)
- Tests pass

---

### GEN-6: Self-Serve Onboarding API
**Files:** new `api/routes/onboarding.py`, update `api/routes/tenants.py`

**Changes:**
- `POST /onboard` — create tenant + upload catalog in one step
  - Body: `business_name`, `industry`, `catalog` (JSON array of items), `welcome_message`
  - Returns: `tenant_id`, `api_key`, embed snippet
- `POST /tenants/{tenant_id}/catalog/upload` — CSV or JSON catalog upload endpoint
  - Parses into `CatalogItem` rows, stores per tenant
- `GET /catalog` — replaces `GET /menu`
- Widget embed snippet generated at onboarding: `<script src="...?tenant={id}"></script>`

**Acceptance criteria:**
- Can create a new non-restaurant tenant via API
- Can upload a catalog CSV
- Widget loads for that tenant with correct greeting

---

## Implementation Order

```
GEN-1 (models)
  → GEN-2 (tools depend on models)
  → GEN-3 (prompts depend on tenant config shape)
  → GEN-4 (guardrails depend on models + tenant config)
  → GEN-5 (preference extraction depends on CustomerProfile)
  → GEN-6 (onboarding API — independent, builds on all above)
```

---

## What This Enables

| Industry | Catalog | Hard Stops | Scope Keywords |
|---|---|---|---|
| Restaurant | dishes | allergens | food, menu, dish, cuisine |
| Hair salon | services | chemical sensitivities | hair, cut, color, style |
| Software | products/plans | budget, platform | feature, integration, API, plan |
| Construction | services | budget, timeline | build, renovation, material |

Same codebase. Different tenant config. No code changes per customer.
