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
- Docker is available for production via `docker-compose.yml` (includes a daily backup sidecar).

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

**Installed entry-points** (after `pip install -e .`):
`chatbot-serve`, `chatbot-chat`, `chatbot-ingest`, `chatbot-scrape`

## Architecture seams — read before editing

1. **One engine, many channels.** `chatbot/core/engine.py` is the only place retrieval + LLM + memory meet. Channels (`chatbot/channels/*`) are thin adapters that call `Chatbot.ask()`. **Don't add business logic in a channel.**
2. **Profile = client + personality.** `chatbot/core/profile.py` merges `config/clients/<id>.yaml` + `config/personalities/<tone>.yaml` into a single `ChatbotProfile`. The system prompt is rebuilt **per request** (language override lives there too).
3. **Pipeline order matters.** `engine.ask()`: sanitize → prompt-injection check → handoff gate → spam check → budget guard → **LLM** → memory → fallback log → analytics. Skipping a stage = security or cost hole.
4. **Handoff gates the LLM.** When a session is in handoff (`.handoff/`), messages route to a live agent and never hit the LLM. Check `HandoffManager.is_active(session_id)` before any LLM assumption.
5. **Vector store auto-rebuilds.** `chatbot/rag/vectorstore.py` SHA-256's file sizes + mtimes in `data/` → triggers rebuild when anything changes. So dropping a PDF in `data/<client>/` and restarting is enough; no manual ingest needed (though `scripts.ingest` still works).
6. **Hybrid retrieval.** `chatbot/rag/hybrid.py` merges vector + BM25 via RRF. Better for product codes / proper nouns. **Opt-in** — set `HYBRID_SEARCH_ENABLED=true`.
7. **Prompt injection is blocked by default.** `BLOCK_PROMPT_INJECTION` defaults to `true` in `chatbot/settings.py`. Set it to `false` in `.env` to log-only mode (not recommended for production).
8. **Prompt templates live in `chatbot/core/prompts.py`.** Includes `RAG_CHAT_TEMPLATE` (main chat), `TRANSLATE_TEMPLATE`, and `REWRITE_TEMPLATE` (standalone-query rewriting). Edit there to tune wording without touching glue code.

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
| `.vectorstore/` | Chroma vector DB | `vectorstore.py` |
| `logs/<client>/` | Loguru rotated log files | `logging_setup.py` |

All should be in `.gitignore` (verify when onboarding a new env).

## Config files (YAML-driven, not code)

- `config/clients/<id>.yaml` — client identity, contact, URLs, data dir, personality link. Three clients: `limmes`, `cannabis`, `default`.
- `config/personalities/<tone>.yaml` — tone + behavior rules. Swapping = one-line config change. Available: `design_studio`, `thai_budtender`, `clinic`, `friendly_official`, `official`, `sales`, `default`.
- `config/products/<id>.yaml` — structured catalog (injected without indexing each item).
- `config/users.json` — admin/viewer accounts (PBKDF2 hashes). Created by `chatbot/security/users.py`.

**Never hardcode client content in Python.** If a string is specific to Limmes or Cannabis, it goes in YAML.

## Opt-in feature flags

Several subsystems default to `false` and must be explicitly enabled in `.env`:

| Setting | Default | What it enables |
|---|---|---|
| `HYBRID_SEARCH_ENABLED` | `false` | BM25+vector hybrid retrieval |
| `AB_TESTING_ENABLED` | `false` | Deterministic session→variant A/B splits |
| `FEEDBACK_ENABLED` | `false` | Per-answer thumbs-up/down persistence |
| `ANALYTICS_ENABLED` | `false` | Question/session telemetry to `.analytics/` |
| `USER_MEMORY_ENABLED` | `false` | Long-term per-user facts to `.user_memory/` |
| `HANDOFF_ENABLED` | `true` | Human-agent handoff queue |
| `SPAM_DETECTION_ENABLED` | `true` | Gibberish/spam blocking before LLM |
| `RATE_LIMIT_ENABLED` | `true` | Token-bucket per-IP + per-session |

Enabling analytics/feedback/user_memory means data is persisted to local disk — review privacy implications before turning on.

## Security defaults worth knowing

- `API_STRICT_CORS=true` (default) — the server **refuses to start** if `API_CORS_ORIGINS` is `*` or empty. Set it to your real domain(s).
- `BLOCK_PROMPT_INJECTION=true` (default) — suspicious messages get HTTP 400, not just a log line.
- `ADMIN_API_KEY` — required to enable the admin dashboard. When empty, `/admin` is disabled.
- `CHATBOT_API_KEY` — optional shared secret for the `/chat` endpoint (e.g. for WordPress embeds). Empty = open access (rate limiting still applies).
- `/docs` and `/redoc` are only available when `DEBUG=true`. They're suppressed in production.
- `Images/` directory at project root is served as static files at `/images` if it exists.

## Testing pattern — dependency injection

`Chatbot.__init__` accepts every subsystem as an optional kwarg (`retriever`, `llm`, `memory`, `budget`, `spam_tracker`, `handoff_manager`, `ab_test_manager`, `analytics_tracker`, `feedback_store`, `user_memory_store`, etc.). Tests pass lightweight fakes rather than hitting real LLMs or disk:

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

Test files live in `tests/` and cover: analytics, budget, contact, exceptions, fallback_log, handoff, language_detection, memory, products, profile, push, rate_limit, sanitize, settings, spam.

## Docker

```bash
docker compose up -d           # start chatbot + backup sidecar
docker compose logs -f chatbot # tail logs
```

`docker-compose.yml` mounts `data/` and `config/` read-only. Vectorstore, sessions, and budget are in named volumes. A backup sidecar (`alpine`) copies them daily; set `BACKUP_KEEP_DAYS` (default 7). A commented-out PostgreSQL service block is ready to uncomment.

## Module map (quick reference)

```
chatbot/
  api/
    app.py               FastAPI factory + lifespan (bot, rate limiters, admin)
    schemas.py           Pydantic request/response models
    routes/
      chat.py            POST /chat — main chat endpoint (IP+session rate limits)
      webhooks.py        /webhook/whatsapp, /webhook/telegram, /webhook/line
      widget.py          Embeddable web widget + demo page
      admin.py           REST API behind X-Admin-Key
      admin_ui.py        Single-file SPA (~2.5k lines, no build step)
      health.py          GET /health
  channels/
    cli.py               REPL (quit / clear / sources)
    whatsapp.py          Twilio adapter, HMAC validation
    telegram.py          Direct httpx, webhook secret
    line.py              LINE Messaging, HMAC-SHA256
    line_flex.py         Flex Message builders (cards, carousels)
    line_imagemap.py     Imagemap (tappable image regions)
    line_rich_menu.py    Rich Menu create/list/set-default/delete CLI
    line_login.py        LINE Login OAuth 2.0 (name/picture/email → user memory)
  core/
    engine.py            Chatbot class — single entry point for all channels
    profile.py           ChatbotProfile (client + personality merge)
    prompts.py           RAG_CHAT_TEMPLATE, REWRITE_TEMPLATE, TRANSLATE_TEMPLATE
    memory.py            ConversationMemory + SessionStore (memory/file/postgres)
    handoff.py           HandoffManager — human-agent queue
    fallback_log.py      Log questions the bot couldn't answer
    analytics.py         Event tracker (batched writes to .analytics/)
    feedback.py          Thumbs up/down store
    ab_testing.py        ABTestManager — deterministic session→variant, persisted
    user_memory.py       Long-term per-user facts
    products.py          ProductCatalog — YAML catalog → system prompt injection
    contact.py           Contact/lead capture + optional email delivery
    push.py              LINE Push API wrapper (handoff replies, campaigns)
  i18n/
    detect.py            Zero-dep language detector (Unicode blocks + stop words)
    messages.py          UI strings in 12 languages + LanguageInfo metadata
  llm/
    providers.py         Swappable ChatOpenAI / ChatAnthropic behind BaseChatModel
    chains.py            LCEL pipeline: rewrite → retrieve → format → prompt → LLM
  rag/
    loaders.py           PDF, DOCX, TXT, MD, HTML, CSV, JSON loaders
    ingestion.py         Document ingestion pipeline
    retriever.py         RAGRetriever (vector-only or hybrid)
    vectorstore.py       Chroma, SHA-256 auto-rebuild on data/ changes
    hybrid.py            BM25 + vector merged via RRF (opt-in)
  security/
    budget.py            Daily token & USD caps + BudgetGuard
    rate_limit.py        Token-bucket per-IP + per-session
    sanitize.py          Input sanitizer + 12-phrase prompt-injection heuristic
    spam.py              Gibberish (Thai/CJK aware), duplicate, progressive cooldown
    headers.py           Security headers + Content-Length body-cap middleware
    users.py             Admin auth, PBKDF2-HMAC-SHA256, session tokens
  tools/
    scraper.py           httpx + BeautifulSoup → data/scraped/
    translator.py        LLM-backed translator
  persistence/
    database.py          psycopg3 PostgreSQL backend (opt-in)
  exceptions.py          ChatbotError hierarchy (ConfigError, LLMError, etc.)
  settings.py            All config via pydantic-settings / .env
  logging_setup.py       Loguru setup (pretty or JSON, auto-rotated per client)
```

## Gotchas

- **Vector store changes don't rebuild on YAML-only edits** — the hash covers `data/`, not `config/`. Restart the server to pick up personality/client YAML changes.
- **LINE Rich Menu edits require publishing to LINE's servers** — it's not just a local config. Use the admin dashboard or `line_rich_menu.py` CLI.
- **Admin SPA is a single ~2.5k-line file** (`admin_ui.py`) by design. Don't try to modularize it — the tradeoff (no build step, one-file copy) is the point.
- **`admin_ui.py.bak` exists** — untracked backup. Don't accidentally restore from it.
- **Two clients share the codebase.** When writing logic, check whether it's client-specific (goes in YAML) or template-level (goes in code). If unsure, ask.
- **CORS will reject the server at startup if misconfigured.** `API_STRICT_CORS=true` is the default. Always set `API_CORS_ORIGINS` before deploying.
- **`docs/helpers/CLAUDE.md`** — this is guidance for a *separate* WordPress theme project (Limes), not the chatbot. Don't confuse it with this file.
- **`_limmes_raw.txt`** — raw source data at project root, not part of the Python package.
- **Feature flags default to off.** Analytics, feedback, A/B testing, user memory, and hybrid search must be explicitly enabled. Don't assume they're active in a fresh clone.

## Conventions

- **Python style:** snake_case, 4-space indent, type hints on public APIs, Pydantic models for config & HTTP.
- **Error handling:** raise `ChatbotError` subclasses (see `chatbot/exceptions.py`) so the API layer maps them to user-safe messages.
- **Logging:** Loguru. `logger.info()` is the norm; use `logger.bind(session_id=...)` for scoped context.
- **No emojis in code or docs** (user preference — breaks console rendering on Windows).
- **Settings via env,** never `os.environ.get()` scattered in modules. Add new vars to `chatbot/settings.py`.
- **New languages** go in `chatbot/i18n/messages.py` — append to `SUPPORTED_LANGUAGES` and `MESSAGES`. The detector in `detect.py` may also need updating for Unicode coverage.

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
- [`docs/DEPLOYMENT.md`](../docs/DEPLOYMENT.md) — production deploy
- [`docs/USAGE_GUIDE.md`](../docs/USAGE_GUIDE.md) — end-user / admin walkthrough
- [`docs/TEMPLATE.md`](../docs/TEMPLATE.md) — template reuse guide
