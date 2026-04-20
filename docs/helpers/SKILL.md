---
name: create-claude-md
description: Use when starting work in a new project directory, when asked to create or improve CLAUDE.md, or when project context is missing and Claude is giving generic responses.
---

# Create CLAUDE.md

## Overview

Read the project, extract only what isn't obvious from the code, write it down. A good CLAUDE.md saves repeated context across sessions without bloating prompts with redundant info.

## When to Use

- No CLAUDE.md exists in the project root
- User says "create a CLAUDE.md for this project"
- Claude is giving generic answers that don't fit the project's actual stack or conventions

## Process

### 1. Read the project structure

```bash
ls                          # root layout
cat package.json            # or pyproject.toml, go.mod, etc.
```

Also check for: `README.md`, `tsconfig.json`, `.env.example`, `vercel.json`, `docker-compose.yml`

### 2. Identify what's non-obvious

Only include things Claude couldn't infer from reading a file:
- The *purpose* of the project (one sentence)
- Non-standard commands or scripts
- Patterns or conventions the team has adopted
- Things to always avoid (e.g., "don't use X library", "never mutate Y")
- Environment setup quirks

Skip: framework boilerplate, standard npm scripts, obvious tech stack facts

### 3. Write the file

**Minimal template:**

```markdown
# Project Name

## What this is
One sentence.

## Stack
- Key tech only (skip obvious defaults)

## Commands
- `npm run dev` — start dev server
- `npm test` — run tests
- Any non-standard scripts

## Conventions
- Patterns or rules specific to this codebase

## Notes
- Gotchas, quirks, things to watch out for
```

Drop any section that has nothing worth saying.

## Quick Reference

| Signal | Action |
|--------|--------|
| Monorepo | Note which packages/apps exist and what each does |
| Custom build pipeline | Document the exact commands and order |
| Shared lib/utils | Name and describe key internal packages |
| Auth or env setup | Note required env vars and where to get them |
| Multiple DB schemas | Clarify which ORM, migration tool, and folder structure |

## Common Mistakes

- **Too verbose** — Don't describe things Claude can read in the code. If it's in `package.json`, skip it.
- **Too generic** — "Use TypeScript best practices" is useless. Write the actual rule.
- **Stale conventions** — If you see a pattern in the code, describe it accurately. Don't invent conventions.
- **Missing commands** — Always include non-standard build/test/run commands. These cause the most friction.
