# Vibe Engineering Workflow Guide

This guide explains how to use the story-based tracking system with Claude Code.

---

## Daily Workflow

### 1. Check Where You Are
```bash
# Open the progress tracker
cat PROGRESS.md

# Find your current story
# Example: S01 is "Not Started" ⬜
```

### 2. Open the Story
```bash
# Open the story file
cat docs/stories/S01-foundation.md

# Or open in your editor
code docs/stories/S01-foundation.md
```

### 3. Start Claude Code Session
```bash
# In your project directory
claude

# Claude Code reads CLAUDE.md automatically and knows all conventions
```

### 4. Work on the Story
Tell Claude Code:
```
I'm working on S01 - Project Foundation. 
Read docs/stories/S01-foundation.md and implement all tasks.
Follow the acceptance criteria and run the tests when done.
```

Claude Code will:
- Read the story file
- Understand the tasks
- Implement them one by one
- Run tests
- Fix failures

### 5. Check Off Tasks
As you complete each task, update the story file:
```markdown
- [x] Verify `uv sync` installs all dependencies
- [x] Create SQLite database initialization script
- [ ] Implement `TenantConfig` table creation  ← still working on this
```

### 6. Run Acceptance Tests
```bash
# Story tells you which tests to run
uv run pytest tests/unit/test_db_connection.py -v

# If tests fail, tell Claude Code:
# "Tests failed. Read the error output and fix it."
```

### 7. Manual Verification
Each story has manual verification steps. Do these yourself:
```bash
# Example from S01
curl http://localhost:8000/health
# Should return: {"status":"ok"...}
```

### 8. Mark Story Complete
When all tasks ✅ and all tests pass:

**Update the story file:**
```markdown
## Definition of Done
- [x] All tasks checked off
- [x] All tests pass
- [x] Manual verification completed
- [x] Code committed
- [x] Status updated in PROGRESS.md
```

**Update PROGRESS.md:**
```markdown
### S01: Project Foundation & Database Setup
**Status:** ✅ Complete  ← change from ⬜
```

**Update "Last Updated" and "Current Story" at top:**
```markdown
**Last Updated:** 2025-01-15
**Current Story:** S02 (Multi-Tenant Middleware)
```

### 9. Commit Your Work
```bash
git add .
git commit -m "feat(foundation): FastAPI + SQLite + tenant config

- Database initialization working
- TenantConfig table created
- Health endpoint live
- All S01 acceptance criteria met

Story: S01 complete"

git push
```

### 10. Move to Next Story
```bash
# Open PROGRESS.md, find next story
# Repeat from step 2
```

---

## Tips for Success

### Working with Claude Code
```
❌ Don't say: "Write me a FastAPI app"
✅ Do say: "I'm on S01. Read docs/stories/S01-foundation.md 
           and implement the tasks following CLAUDE.md conventions."
```

### When You Get Stuck
```
1. Read the story's "Implementation Notes" section
2. Ask Claude Code: "What's blocking S01 from completing?"
3. Check dependencies: Did previous stories finish?
4. Look at similar stories for patterns
```

### Taking Breaks
```
Before you stop for the day:
1. Check off completed tasks in the story file
2. Add notes in the story under "Blockers" if stuck
3. Update PROGRESS.md with current status
4. Commit what you have

When you come back:
1. Read PROGRESS.md — you'll know exactly where you were
2. Open the current story
3. Continue from first unchecked task
```

### Story Dependencies
```
Some stories depend on others:
- S02 needs S01 complete (can't test middleware without DB)
- S05 needs S04 complete (can't embed without data)
- S13 needs S11+S12 complete (recommender uses other tools)

The PROGRESS.md shows weeks — finish week's stories before moving to next.
```

### When Tests Fail
```
1. Read the test output carefully
2. Tell Claude Code the exact error
3. Claude Code will fix and re-run
4. Repeat until green

Don't skip failing tests — they catch real issues.
```

### Refining Stories Mid-Flight
```
If you discover a story needs more work than estimated:
1. Add tasks to the story file
2. Update "Estimated Time"
3. Don't feel bad — it's a discovery process
4. Finish the story properly before moving on
```

---

## Example Full Session

```bash
# Morning: Start S01
cat PROGRESS.md  # See S01 is next
cat docs/stories/S01-foundation.md  # Read the story

# Open Claude Code
claude

# Tell Claude:
"I'm working on S01 - Project Foundation & Database Setup.
Read docs/stories/S01-foundation.md and implement all tasks.
Start with task 1: verify uv sync works."

# Claude Code works through tasks...
# You check off each one as it completes
# ...
# All tasks done

# Run acceptance tests
uv run pytest tests/unit/test_db_connection.py -v
# ✅ All pass

# Manual verification
curl http://localhost:8000/health
# ✅ Returns 200

# Update story status to ✅
# Update PROGRESS.md
# Commit

git add .
git commit -m "feat(foundation): S01 complete"
git push

# Done for the day. Tomorrow starts S02.
```

---

## Tracking Multiple Sessions

If you work on this across multiple days/weeks, PROGRESS.md is your source of truth:

```markdown
**Last Updated:** 2025-01-20
**Current Story:** S07 (LangGraph Foundation)

Week 1: ✅✅✅ (S01-S03 complete)
Week 2: ✅✅✅ (S04-S06 complete)
Week 3: 🔄⬜⬜⬜ (S07 in progress, S08-S10 not started)
```

One glance tells you exactly where you are.

---

## Celebration Points

- ✅ First story done → You have a working foundation
- ✅ Week 1 done → Database + tenant isolation working
- ✅ Week 2 done → RAG pipeline live with real reviews
- ✅ Week 3 done → Conversational agent working
- ✅ Week 4 done → Full recommendation engine
- ✅ Week 5 done → Production-grade guardrails
- ✅ Week 6 done → **DEPLOYED MVP** 🎉

Each week is a real milestone. Ship it, demo it, celebrate it.
