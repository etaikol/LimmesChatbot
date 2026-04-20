# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Project context for Claude Code. Global preferences live in `~/.claude/CLAUDE.md` (user identity, Hebrew/RTL, skill calibration — don't repeat here). This file covers only what's non-obvious from the code.

> **Before resuming work, read `docs/FEATURES.md`** — that's the live index of what's built and what's next.

## What this is

Python 3.10+ multi-channel RAG chatbot template. Production-grade, not a toy. Currently runs two clients: Limmes (interior design, Hebrew) and Cannabis (Thai dispensary, multilingual). Channels: web widget, WhatsApp (Twilio), Telegram, LINE, CLI. See [`docs/FEATURES.md`](../docs/FEATURES.md) for the capability matrix.

## Stack

- **Python 3.10+**, FastAPI + uvicorn, LangChain (LCEL), Chroma, Pydantic v2, Loguru.
- **No build step.** No Node, no bundler. Admin UI is inline HTML/CSS/JS in `chatbot/api/routes/admin_ui.py`.
- **No Docker required for dev** — `python -m scripts.serve --reload` is enough.

## Commands

```bash
cp .env.example .env                # first-time setup — fill in API keys
python -m scripts.serve --reload    # dev server on :8000 (hot reload)
ACTIVE_CLIENT=limmes python -m scripts.serve --reload  # run a specific client
python -m scripts.chat              # CLI REPL
python -m scripts.ingest            # rebuild vector store from data/
python -m scripts.scrape            # scrape URLs → data/scraped/
pytest                              # run all tests
pytest tests/test_spam.py -v        # run a single test file
pytest -k "test_gibberish" -v       # run tests matching a name pattern
```

## Architecture seams — read before editing

1. **One engine, many channels.** `chatbot/core/engine.py` is the only place retrieval + LLM + memory meet. Channels (`chatbot/channels/*`) are thin adapters that call `Chatbot.ask()`. **Don't add business logic in a channel.**
2. **Profile = client + personality.** `chatbot/core/profile.py` merges `config/clients/<id>.yaml` + `config/personalities/<tone>.yaml` into a single `ChatbotProfile`. The system prompt is rebuilt **per request** (language override lives there too).
3. **Pipeline order matters.** `engine.ask()`: sanitize → spam/injection → budget guard → **handoff gate** → retrieve → LLM → memory → analytics. Skipping a stage = security or cost hole.
4. **Handoff gates the LLM.** When a session is in handoff (`.handoff/`), messages route to a live agent and never hit the LLM. Check `HandoffManager.is_active(session_id)` before any LLM assumption.
5. **Vector store auto-rebuilds.** `chatbot/rag/vectorstore.py` SHA-256's file sizes + mtimes in `data/` → triggers rebuild when anything changes. So dropping a PDF in `data/<client>/` and restarting is enough; no manual ingest needed (though `scripts.ingest` still works).
6. **Hybrid retrieval.** `chatbot/rag/hybrid.py` merges vector + BM25 via RRF. Better for product codes / proper nouns.
7. **Prompt injection is logged by default, not blocked.** Set `BLOCK_PROMPT_INJECTION=true` in `.env` for strict mode.

## Directories that look optional but aren't

These are runtime state — don't commit, don't delete on a whim:

| Dir | Contents | Created by |
|---|---|---|
| `.sessions/` | Per-session conversation JSON | `SessionStore(file)` |
| `.budget/` | Daily token/USD spend | `BudgetGuard` |
| `.handoff/` | Live-agent queue | `HandoffManager` |
| `.fallback/` | Unanswered questions log | `fallback_log.py` |
| `.analytics/` | Event counters | `analytics.py` |
| `.feedback/` | Thumbs up/down | `feedback.py` |
| `.user_memory/` | Long-term per-user facts | `user_memory.py` |

All should be in `.gitignore` (verify when onboarding a new env).

## Config files (YAML-driven, not code)

- `config/clients/<id>.yaml` — client identity, contact, URLs, data dir, personality link.
- `config/personalities/<tone>.yaml` — tone + behavior rules. Swapping = one-line config change.
- `config/products/<id>.yaml` — structured catalog (injected without indexing each item).
- `config/users.json` — admin/viewer accounts (PBKDF2 hashes). Created by `chatbot/security/users.py`.

**Never hardcode client content in Python.** If a string is specific to Limmes or Cannabis, it goes in YAML.

## Testing pattern — dependency injection

`Chatbot.__init__` accepts every subsystem as an optional kwarg (`retriever`, `llm`, `memory`, `budget`, `spam_tracker`, `handoff_manager`, etc.). Tests pass lightweight fakes rather than hitting real LLMs or disk:

```python
bot = Chatbot(
    profile=some_profile,
    settings=test_settings,
    llm=FakeLLM(),
    memory=SessionStore("memory"),
    budget=BudgetGuard(..., daily_token_cap=0),  # disabled
)
```

This is the established pattern — don't reach for `monkeypatch` or `unittest.mock` when constructor injection does the job.

## Gotchas

- **Vector store changes don't rebuild on YAML-only edits** — the hash covers `data/`, not `config/`. Restart the server to pick up personality/client YAML changes.
- **LINE Rich Menu edits require publishing to LINE's servers** — it's not just a local config. Use the admin dashboard or `line_rich_menu.py` CLI.
- **Admin SPA is a single ~2.5k-line file** (`admin_ui.py`) by design. Don't try to modularize it — the tradeoff (no build step, one-file copy) is the point.
- **`admin_ui.py.bak` exists** — untracked backup. Don't accidentally restore from it.
- **Two clients share the codebase.** When writing logic, check whether it's client-specific (goes in YAML) or template-level (goes in code). If unsure, ask.

## Conventions

- **Python style:** snake_case, 4-space indent, type hints on public APIs, Pydantic models for config & HTTP.
- **Error handling:** raise `ChatbotError` subclasses (see `chatbot/exceptions.py`) so the API layer maps them to user-safe messages.
- **Logging:** Loguru. `logger.info()` is the norm; use `logger.bind(session_id=...)` for scoped context.
- **No emojis in code or docs** (user preference — breaks console rendering on Windows).
- **Settings via env,** never `os.environ.get()` scattered in modules. Add new vars to `chatbot/settings.py`.

## Model routing — Opus vs Sonnet

I (Etai) switch models by task shape. Use this calibration when I don't specify:

| Model | Task shape | Examples |
|---|---|---|
| **Opus** | Design / architecture / cross-cutting reasoning | New feature design, prompt engineering for a personality, debugging a bug that spans 3+ modules, evaluating whether to refactor, planning a roadmap item |
| **Sonnet** | Execution within a clear spec | Single-file edits, writing tests for an existing function, doc updates, typo fixes, adding a config option, wiring an existing helper into a new channel |

**If a task is ambiguous in scope — ask me before assuming.** A 5-second clarification saves a wrong refactor.

## When I ask for help on this project

- **Rate work by difficulty × impact** (Low/Med/High) when proposing next steps. I'll pick by ROI — your opinion matters more than neutral listing.
- **Check `docs/FEATURES.md` first** before suggesting new features — often it's already built.
- **Explain WHY on non-obvious code** (e.g., why we hash mtimes, why handoff bypasses LLM). I'm learning, not just applying.
- **Terse summary at end** — what changed, file paths, one or two sentences. I read the diff myself.

## Related docs

- [`docs/FEATURES.md`](../docs/FEATURES.md) — capability index + roadmap
- [`docs/ARCHITECTURE.md`](../docs/ARCHITECTURE.md) — module map
- [`docs/SECURITY.md`](../docs/SECURITY.md) — rate limits, budgets, auth
- [`docs/CUSTOMIZATION.md`](../docs/CUSTOMIZATION.md) — new client / new personality
- [`docs/DEPLOYMENT.md`](../docs/DEPLOYMENT.md) — production deploy (large — collapse planned)
- [`docs/USAGE_GUIDE.md`](../docs/USAGE_GUIDE.md) — end-user / admin walkthrough
