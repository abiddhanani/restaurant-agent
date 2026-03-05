# 🚀 Quick Start — Restaurant Agent

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

**Read these 3 files in order:**

1. **CLAUDE.md** — Conventions Claude Code follows  
2. **PROGRESS.md** — Master tracker of all 21 stories  
3. **docs/WORKFLOW.md** — How to work story-by-story

**Key insight:** You don't need to remember everything. CLAUDE.md tells Claude Code what to do. PROGRESS.md tells you where you are. Story files tell you what to build.

---

## Step 3: Start Your First Story (30 minutes)

```bash
# 1. Open the tracker
cat PROGRESS.md

# Current story: S01 - Project Foundation

# 2. Read the story
cat docs/stories/S01-foundation.md

# 3. Start Claude Code
claude

# 4. Tell Claude Code:
```

**Paste this into Claude Code:**
```
I'm working on S01 - Project Foundation & Database Setup.
Read docs/stories/S01-foundation.md and implement all tasks in order.
Follow all conventions in CLAUDE.md.
Run tests after each task.
```

**Claude Code will:**
- Read the story file
- Read CLAUDE.md for conventions
- Implement database initialization
- Create tenant config table
- Seed demo data
- Run tests
- Fix any failures

**You:**
- Watch it work
- Check off tasks in the story file as they complete
- Run the manual verification steps yourself
- Mark story complete when done

---

## Step 4: Track Your Progress (ongoing)

After S01 completes:

**Update PROGRESS.md:**
```markdown
**Last Updated:** 2025-01-15  ← today's date
**Current Story:** S02        ← next story

### S01: Project Foundation & Database Setup
**Status:** ✅ Complete       ← change from ⬜ to ✅
```

**Commit:**
```bash
git add .
git commit -m "feat(foundation): S01 complete - database initialized"
git push
```

**Move to S02:**
```bash
cat docs/stories/S02-multitenant.md
claude
# Tell Claude Code: "I'm on S02. Read docs/stories/S02-multitenant.md..."
```

---

## The 6-Week Sprint

| Week | Goal | Stories | Hours |
|------|------|---------|-------|
| 1 | Foundation + DB | S01-S03 | 10-14h |
| 2 | RAG Pipeline | S04-S06 | 13-16h |
| 3 | Agent Core + A2A | S07-S10 | 17-22h |
| 4 | Tools | S11-S14 | 17-21h |
| 5 | Guardrails + MCP | S15-S18 | 18-21h |
| 6 | Eval + Deploy | S19-S21 | 16-21h |
| **Total** | **Working MVP** | **21 stories** | **~100 hours** |

**Realistic pace:** 10-15 hours/week = 6-8 weeks to Phase 0 MVP

---

## What You Get at the End

After completing all 21 stories:

✅ Multi-tenant restaurant agent  
✅ RAG pipeline with real Google Reviews  
✅ Taste profile that evolves through conversation  
✅ 3-layer production guardrails  
✅ A2A and MCP interfaces (future-ready)  
✅ Embeddable widget  
✅ Deployed and live on Railway  
✅ Langfuse observability  
✅ Eval pipeline with golden dataset  

**And most importantly:**  
✅ A codebase you fully understand because you built it story by story

---

## Your First Command

```bash
claude
```

Then tell it:
```
Read PROGRESS.md and docs/stories/S01-foundation.md.
I'm starting S01. Implement all tasks following CLAUDE.md conventions.
```

That's it. You're building.

---

## Getting Help

**If stuck on a story:**
1. Read the story's "Implementation Notes"
2. Ask Claude Code: "What's blocking this task?"
3. Check if previous stories are actually complete

**If a story seems wrong:**
1. Refine it — add tasks, update estimates
2. Stories are guides, not contracts
3. Document changes in the story file

**If you need to take a break:**
1. Check off completed tasks
2. Update PROGRESS.md
3. Commit
4. When you return, PROGRESS.md tells you exactly where you were

---

## Important Reminders

- Each story is independently testable — don't skip tests
- CLAUDE.md has the conventions — Claude Code reads it every session
- Stories have dependencies — finish Week 1 before Week 2
- Commit after each story — clear checkpoints
- This is vibe engineering — refine as you discover

**Now go build.**
