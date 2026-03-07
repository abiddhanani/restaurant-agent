# Workflow Guide

This guide explains how to use the Jira-based story tracking system with Claude Code.

---

## Daily Workflow

### 1. Check Where You Are
```bash
cat PROGRESS.md
# Find your current story — e.g. RA-2
```

### 2. Pull the Story from Jira
Open Claude Code and say:
```
Pull Jira story RA-2
```
Claude Code will fetch the full story including tasks and acceptance criteria.

### 3. Start Claude Code Session
```bash
claude
# Claude Code reads CLAUDE.md automatically and knows all conventions
```

### 4. Work on the Story
Tell Claude Code:
```
Pull Jira story RA-2 and implement all tasks.
Follow the acceptance criteria and run the tests when done.
```

Claude Code will:
- Fetch the story from Jira
- Understand the tasks
- Implement them one by one
- Run tests and fix failures

### 5. Run Tests
```bash
uv run pytest tests/ -v

# If tests fail, tell Claude Code:
# "Tests failed. Read the error output and fix it."
```

### 6. Manual Verification
Each story has manual verification steps. Do these yourself:
```bash
# Example from RA-1
curl http://localhost:8000/health
# Should return: {"status":"ok"...}
```

### 7. Mark Story Complete

**Update PROGRESS.md:**
```markdown
### RA-2: Multi-Tenant Middleware & Routing
**Status:** ✅ Complete
```

**Update "Last Updated" and "Current Story" at top:**
```markdown
**Last Updated:** 2026-03-07
**Current Story:** RA-3
```

**Transition the Jira ticket to Done.**

### 8. Commit Your Work
```bash
git add .
git commit -m "feat(tenant): RA-2 complete - multi-tenant middleware

- Tenant resolution middleware working
- All acceptance criteria met

Story: RA-2"

git push
```

### 9. Move to Next Story
Open PROGRESS.md, find next story, repeat from step 2.

---

## Tips for Success

### Working with Claude Code
```
Don't say: "Write me a FastAPI app"
Do say:    "Pull Jira story RA-2 and implement the tasks following CLAUDE.md conventions."
```

### When You Get Stuck
```
1. Re-read the Jira story's acceptance criteria
2. Ask Claude Code: "What's blocking RA-2 from completing?"
3. Check dependencies: did previous stories finish?
4. Add a comment on the Jira ticket with the blocker
```

### Taking Breaks
```
Before you stop for the day:
1. Update PROGRESS.md with current status (🔄 In Progress)
2. Add a comment on the Jira ticket if blocked
3. Commit what you have

When you come back:
1. Read PROGRESS.md — you'll know exactly where you were
2. Pull the current Jira story
3. Continue from first incomplete task
```

### Story Dependencies
```
Some stories depend on others:
- RA-2 needs RA-1 complete (can't test middleware without DB)
- RA-5 needs RA-4 complete (can't embed without data)
- RA-13 needs RA-11 + RA-12 complete (recommender uses other tools)

PROGRESS.md shows weeks — finish week's stories before moving to next.
```

### When Tests Fail
```
1. Read the test output carefully
2. Tell Claude Code the exact error
3. Claude Code will fix and re-run
4. Repeat until green

Don't skip failing tests — they catch real issues.
```

---

## Example Full Session

```bash
# Morning: Start RA-2
cat PROGRESS.md  # See RA-2 is next

# Open Claude Code
claude

# Tell Claude:
"Pull Jira story RA-2 and implement all tasks.
Start with task 1."

# Claude Code works through tasks...
# All tasks done

# Run tests
uv run pytest tests/ -v
# All pass

# Manual verification
curl http://localhost:8000/health
# Returns 200

# Update PROGRESS.md — mark RA-2 ✅
# Transition Jira ticket to Done
# Commit

git add .
git commit -m "feat(tenant): RA-2 complete"
git push

# Done for the day. Tomorrow starts RA-3.
```

---

## Tracking Multiple Sessions

PROGRESS.md is your source of truth:

```markdown
**Last Updated:** 2026-03-21
**Current Story:** RA-7

Week 1: ✅✅✅ (RA-1–RA-3 complete)
Week 2: ✅✅✅ (RA-4–RA-6 complete)
Week 3: 🔄⬜⬜⬜ (RA-7 in progress, RA-8–RA-10 not started)
```

One glance tells you exactly where you are.

---

## Milestones

- ✅ RA-1 done → Working foundation
- ✅ Week 1 done → Database + tenant isolation working
- ✅ Week 2 done → RAG pipeline live with real reviews
- ✅ Week 3 done → Conversational agent working
- ✅ Week 4 done → Full recommendation engine
- ✅ Week 5 done → Production-grade guardrails
- ✅ Week 6 done → Deployed MVP
