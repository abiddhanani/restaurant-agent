# Quick Start — Restaurant Agent

**You have a complete scaffold. Here's how to start building.**

---

## Step 1: Setup (5 minutes)

```bash
# 1. Install Claude Code (if you haven't)
npm install -g @anthropic/claude-code

# 2. Copy environment variables
cp .env.example .env

# 3. Add your API keys to .env
# Required right now: ANTHROPIC_API_KEY
# Optional for later: GOOGLE_PLACES_API_KEY, LANGFUSE_*

# 4. Install dependencies
uv sync

# 5. Verify it works
uv run uvicorn api.main:app --reload
# Should start on http://localhost:8000
# Ctrl+C to stop
```

---

## Step 2: Understand the System (5 minutes)

**Read these files:**

1. **CLAUDE.md** — Conventions Claude Code follows
2. **PROGRESS.md** — Master tracker of all 21 stories
3. **docs/WORKFLOW.md** — How to work story-by-story

**Key insight:** Stories live in Jira (project: RA). PROGRESS.md tells you where you are. Pull the current Jira story to see what to build.

---

## Step 3: Start Your First Story (30 minutes)

```bash
# 1. Check the tracker
cat PROGRESS.md
# Current story: RA-2

# 2. Start Claude Code
claude
```

**Tell Claude Code:**
```
Pull Jira story RA-2 and implement all tasks.
Follow all conventions in CLAUDE.md.
Run tests after each task.
```

**Claude Code will:**
- Fetch the story from Jira
- Read CLAUDE.md for conventions
- Implement tasks in order
- Run tests and fix any failures

**You:**
- Watch it work
- Run manual verification steps yourself
- Transition the Jira ticket to Done when complete

---

## Step 4: Track Your Progress (ongoing)

After a story completes, update PROGRESS.md:

```markdown
**Last Updated:** 2026-03-07
**Current Story:** RA-3

### RA-2: Multi-Tenant Middleware & Routing
**Status:** ✅ Complete
```

**Commit:**
```bash
git add .
git commit -m "feat(tenant): RA-2 complete - multi-tenant middleware"
git push
```

---

## The 6-Week Sprint

| Week | Goal | Stories | Hours |
|------|------|---------|-------|
| 1 | Foundation + DB | RA-1–RA-3 | 10-14h |
| 2 | RAG Pipeline | RA-4–RA-6 | 13-16h |
| 3 | Agent Core + A2A | RA-7–RA-10 | 17-22h |
| 4 | Tools | RA-11–RA-14 | 17-21h |
| 5 | Guardrails + MCP | RA-15–RA-18 | 18-21h |
| 6 | Eval + Deploy | RA-19–RA-21 | 16-21h |
| **Total** | **Working MVP** | **21 stories** | **~100 hours** |

**Realistic pace:** 10-15 hours/week = 6-8 weeks to Phase 0 MVP

---

## What You Get at the End

After completing all 21 stories:

- Multi-tenant restaurant agent
- RAG pipeline with real Google Reviews
- Taste profile that evolves through conversation
- 3-layer production guardrails
- A2A and MCP interfaces (future-ready)
- Embeddable widget
- Deployed and live on Railway
- Langfuse observability
- Eval pipeline with golden dataset

---

## Your First Command

```bash
claude
```

Then tell it:
```
Pull Jira story RA-2 and implement all tasks following CLAUDE.md conventions.
```

That's it. You're building.

---

## Getting Help

**If stuck on a story:**
1. Re-read the Jira story's acceptance criteria
2. Ask Claude Code: "What's blocking this task?"
3. Check if previous stories are actually complete

**If a story seems wrong:**
1. Refine it directly in Jira
2. Stories are guides, not contracts
3. Document decisions in the Jira ticket comments

**If you need to take a break:**
1. Update PROGRESS.md with current status
2. Commit
3. When you return, PROGRESS.md tells you exactly where you were

---

## Important Reminders

- Each story is independently testable — don't skip tests
- CLAUDE.md has the conventions — Claude Code reads it every session
- Stories have dependencies — finish Week 1 before Week 2
- Commit after each story — clear checkpoints
