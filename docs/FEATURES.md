# Features & Roadmap

**Purpose:** single source of truth for what the chatbot can do today and what's still on the list. Treat this as the index — individual docs (ARCHITECTURE, SECURITY, CUSTOMIZATION, DEPLOYMENT, USAGE_GUIDE) go deeper per area.

Last audited: `feat/advanced-features` @ `4efa6f7` (Thai/CJK gibberish tests).

---

## Table of contents

### Built (current capabilities)
1. [Core engine & orchestration](#1-core-engine--orchestration)
2. [RAG — retrieval & knowledge base](#2-rag--retrieval--knowledge-base)
3. [LLM layer & providers](#3-llm-layer--providers)
4. [Channels](#4-channels)
5. [i18n — language detection & multilingual replies](#5-i18n--language-detection--multilingual-replies)
6. [Memory & sessions](#6-memory--sessions)
7. [User memory (long-term)](#7-user-memory-long-term)
8. [Handoff to human agent](#8-handoff-to-human-agent)
9. [Fallback logging](#9-fallback-logging)
10. [Analytics](#10-analytics)
11. [Feedback (thumbs up/down)](#11-feedback-thumbs-updown)
12. [A/B testing personalities](#12-ab-testing-personalities)
13. [Products catalog](#13-products-catalog)
14. [Contact / lead capture](#14-contact--lead-capture)
15. [Push & campaigns (LINE)](#15-push--campaigns-line)
16. [LINE advanced UI (Flex / Imagemap / Rich Menu / Login)](#16-line-advanced-ui)
17. [Admin dashboard & auth](#17-admin-dashboard--auth)
18. [Security stack](#18-security-stack)
19. [Tools (scraper, translator)](#19-tools-scraper-translator)
20. [Persistence backends](#20-persistence-backends)

### Not built (roadmap)
21. [Tier 1 — highest ROI next](#21-tier-1--highest-roi-next)
22. [Tier 2 — medium complexity](#22-tier-2--medium-complexity)
23. [Tier 3 — advanced / later](#23-tier-3--advanced--later)

---

## Built

### 1. Core engine & orchestration

- `chatbot/core/engine.py` — single `Chatbot` class; every channel calls the same pipeline: sanitize → spam/injection check → budget guard → handoff gate → retrieve → LLM → memory → analytics.
- Pluggable profile via `chatbot/core/profile.py` — merges a `ClientConfig` (YAML under `config/clients/`) with a `PersonalityConfig` (YAML under `config/personalities/`) into a single `ChatbotProfile` that rebuilds the system prompt per request.
- Retry-on-transient-failure wrapper (429 / timeout / conn reset) — 2 retries, exponential backoff.

### 2. RAG — retrieval & knowledge base

- **Loaders:** PDF, DOCX, TXT, MD, HTML, CSV, JSON (`chatbot/rag/loaders.py`).
- **Chunking:** `RecursiveCharacterTextSplitter`, default 1000 chars / 200 overlap.
- **Vector store:** Chroma (file-persistent, no external service). Auto-rebuild on source change via SHA-256 hash of file sizes + mtimes (`chatbot/rag/vectorstore.py`).
- **Hybrid retrieval:** `chatbot/rag/hybrid.py` — vector + BM25, merged with Reciprocal Rank Fusion (RRF). Deterministic doc IDs via SHA-256. Better for exact product codes / proper nouns.
- **Query rewriting:** follow-up questions are rewritten into standalone queries before retrieval (`REWRITE_TEMPLATE`).
- **Top-K & min-score filter** configurable.

### 3. LLM layer & providers

- `chatbot/llm/providers.py` — swappable `ChatOpenAI` / `ChatAnthropic` behind `BaseChatModel`.
- `chatbot/llm/chains.py` — LCEL pipeline: rewrite → retrieve → format → prompt → LLM → parse.

### 4. Channels

| Channel | File | Notes |
|---|---|---|
| Web widget | `chatbot/api/routes/widget.py` | Embeddable `<script>`; language picker; RTL auto-switch |
| CLI | `chatbot/channels/cli.py` | REPL with `quit`, `clear`, `sources` |
| WhatsApp | `chatbot/channels/whatsapp.py` | Twilio; HMAC signature validation; TwiML replies |
| Telegram | `chatbot/channels/telegram.py` | Direct httpx (no SDK); webhook secret |
| LINE | `chatbot/channels/line.py` | HMAC-SHA256; Flex / Imagemap / Rich Menu (see §16) |

### 5. i18n — language detection & multilingual replies

- 12 languages: English, Hebrew, Arabic, Farsi, Thai, French, Spanish, German, Russian, Japanese, Chinese, Hindi.
- Zero-dependency detector (`chatbot/i18n/detect.py`) — Unicode-block classification + stop-word disambiguation for Latin scripts. Returns `None` rather than guessing wrong.
- Per-request **language override** injected into the system prompt (highest priority).
- RTL auto-applied for Hebrew / Arabic / Farsi in the widget.

### 6. Memory & sessions

- `chatbot/core/memory.py` — `ConversationMemory` + pluggable `SessionStore`.
- Backends: `memory` (LRU-capped dict), `file` (atomic write-then-rename JSON per session), `postgres` (opt-in, `chatbot_sessions` JSONB).
- History window via `MAX_HISTORY_TURNS` (default 10).
- Per-session file locks to prevent write races.

### 7. User memory (long-term)

- `chatbot/core/user_memory.py` — free-text facts & preferences per user, timestamped, persisted to `.user_memory/`.
- Relevant entries injected at session start so the LLM can greet returning users and reference prior context.
- Populated automatically on LINE Login (see §16).

### 8. Handoff to human agent

- `chatbot/core/handoff.py` — persisted queue in `.handoff/`.
- Triggers: low-confidence answer, explicit user request ("talk to human"), admin takeover.
- While handoff is active, **all messages bypass the LLM** and route to the live-agent queue.
- `_auto_resolve_stale` reaps forgotten handoffs on every public method call.
- Admin can reply via dashboard → delivered back to the user's channel via `push.py`.

### 9. Fallback logging

- `chatbot/core/fallback_log.py` — detects answers containing fallback phrases ("I don't have that information", etc.) and logs the original question to `.fallback/`.
- Admins review this to find KB gaps and add content.

### 10. Analytics

- `chatbot/core/analytics.py` — event recorder: questions, response times, languages, sessions, unanswered rate, handoff rate, feedback.
- In-memory counters + batched JSON writes to `.analytics/`.
- Consumed by the admin dashboard for charts.

### 11. Feedback (thumbs up/down)

- `chatbot/core/feedback.py` — per-answer votes, stored in `.feedback/`, fed into analytics for answer-quality tracking.

### 12. A/B testing personalities

- `chatbot/core/ab_testing.py` — deterministic session → variant assignment via hash, with configurable traffic split.
- Variants are just personality YAMLs; no code change to switch.
- Conversion tracked through analytics.

### 13. Products catalog

- `chatbot/core/products.py` — structured catalog loaded from `config/products/<client_id>.yaml`.
- Injected into the retrieval context so the bot can talk about specific SKUs without indexing each one as a document.

### 14. Contact / lead capture

- `chatbot/core/contact.py` — captures contact-form-style messages (name / phone / email / question).
- Optional email delivery. Stored for admin review.

### 15. Push & campaigns (LINE)

- `chatbot/core/push.py` — LINE Push API wrapper with retry logic.
- Used for: admin handoff replies back to users, broadcast / campaign messages.

### 16. LINE advanced UI

- **Flex Messages** (`line_flex.py`) — product cards, contact cards, carousels, quick replies.
- **Imagemap** (`line_imagemap.py`) — full-width image with tappable regions (visual menus / campaign banners).
- **Rich Menu** (`line_rich_menu.py`) — 2-col / 3-col / 2×3 layouts, with CLI for create / list / set-default / delete.
- **LINE Login OAuth 2.0** (`line_login.py`) — auth URL, code exchange, profile fetch. Writes name / picture / email into user memory.

### 17. Admin dashboard & auth

- `chatbot/api/routes/admin_ui.py` — single-page SPA (inline HTML/CSS/JS, **no build step**).
- `chatbot/api/routes/admin.py` — REST API behind `X-Admin-Key` or session-token auth.
- `chatbot/security/users.py` — admin/viewer accounts; PBKDF2-HMAC-SHA256 password hashing; session tokens.
- Dashboard covers: overview, sessions, analytics, feedback, handoff queue, budget, config viewer/editor, log viewer, data-file CRUD, LINE rich-menu & flex preview.

### 18. Security stack

- `rate_limit.py` — token-bucket per IP + per session, thread-safe, idle-TTL eviction.
- `budget.py` — daily token & USD caps, durable state (`.budget/state.json`), pre-call estimates.
- `spam.py` — gibberish heuristics (including Thai/CJK), duplicate detection, progressive per-session cooldown.
- `sanitize.py` — input + session-ID sanitizers, 12-phrase prompt-injection heuristic (log or block).
- `headers.py` — hardening headers + `Content-Length` body cap middleware.
- `users.py` — admin auth (see §17).

### 19. Tools (scraper, translator)

- `chatbot/tools/scraper.py` — httpx + BeautifulSoup; cleans scripts/nav/styles; writes to `data/scraped/` for the standard ingestion pipeline.
- `chatbot/tools/translator.py` — LLM-backed translator using the configured provider; no external API key.

### 20. Persistence backends

- **File** (default) — JSON per session under `.sessions/`, atomic writes.
- **Memory** — LRU dict, good for tests / ephemeral.
- **Postgres** — `chatbot/persistence/database.py`, psycopg3, auto-creates schema, singleton pool.

---

## Not built

### 21. Tier 1 — highest ROI next

| # | Feature | Why it matters | Difficulty |
|---|---|---|---|
| T1.1 | **Tool / function calling** | Let the LLM call real functions — check availability, book a visit, send an email, query a sheet. Turns the bot from answerer into actor. | Med |
| T1.2 | **Streaming responses** | Perceived latency drops dramatically; WhatsApp/LINE can show typing-indicator while chunks stream. | Med |
| T1.3 | **Eval harness / regression suite** | Golden Q&A set run on every prompt change so we don't silently regress. Cheap insurance. | Med |
| T1.4 | **Self-healing KB** | Parse fallback log → suggest new doc snippets for admin to one-click approve into `data/`. | Med |
| T1.5 | **Cost attribution** | Dashboard shows tokens/USD **per client, per channel, per session**. Needed before billing multiple clients. | Low |

### 22. Tier 2 — medium complexity

| # | Feature | Notes |
|---|---|---|
| T2.1 | **Multimodal (image understanding)** | Customer sends photo of a room / curtain / product → bot responds. OpenAI `gpt-4o` and Anthropic `claude-opus/sonnet` both support it. |
| T2.2 | **Outbound webhooks** | On events (lead captured, handoff, low-confidence), POST to CRM / Google Sheets / Zapier. |
| T2.3 | **Proactive messaging** | Scheduled outreach — reminders, promos, follow-ups. Piggybacks on `push.py`. |
| T2.4 | **Prompt versioning + rollback** | Each personality YAML gets a version; admin can A/B and roll back without redeploying. |
| T2.5 | **Richer analytics** | Funnels (greet → question → handoff → lead), cohorts, drop-off points. Data is already collected; just needs views. |
| T2.6 | **Per-client data isolation** | Right now file paths are shared. For SaaS multi-tenant, each client's sessions / analytics / feedback / user-memory should live in namespaced dirs (partially done — finish it). |
| T2.7 | **Redis-backed rate limiter** | Required for horizontal scaling (multi-instance). Today's token-bucket is in-process only. |
| T2.8 | **Content filtering on LLM output** | Catch the model generating unsafe content before it reaches the user. |
| T2.9 | **Per-user authentication for widget** | All web users are anonymous today; optional JWT / API-key auth for enterprise deployments. |
| T2.10 | **Structured audit trail** | JSON log per chat turn for compliance / forensics. |

### 23. Tier 3 — advanced / later

| # | Feature | Notes |
|---|---|---|
| T3.1 | **Voice (STT → STT)** | WhatsApp voice note → Whisper → answer → TTS. Heavy-ish, infra-dependent. |
| T3.2 | **Agentic loops** | Plan → call tool → observe → call tool → answer. Needs T1.1 first. |
| T3.3 | **Fine-tuning on logs** | Only worthwhile after ~1k quality-labeled conversations. |
| T3.4 | **Order / booking integration** | Direct POS / calendar connection. Big scope, client-specific. |
| T3.5 | **Semantic caching** | Cache answers for near-identical questions. Big token savings at scale. Needs an embedding match layer in front of the engine. |
| T3.6 | **Evaluation in CI** | T1.3 → hooked into CI with quality thresholds that block bad prompt changes. |
| T3.7 | **Encrypted session storage at rest** | File sessions are plaintext today; encrypt or use PostgreSQL column encryption. |
| T3.8 | **CSP header for widget** | Widget is injected into 3rd-party pages; nonce-based CSP tightens XSS protection. |
| T3.9 | **IP allowlists for webhooks** | Twilio/Telegram/LINE publish egress IPs — restrict at firewall level. |

---

## How to use this file

- **Starting a new task?** Check the Built section to confirm it isn't already there.
- **Finished a roadmap item?** Move it from the roadmap section up into Built with a one-liner and file reference.
- **Designing a new feature?** Add it here first as a one-line Tier entry with "why it matters". Forces clarity before code.
- **Do not let this file grow past two screens per section.** If a feature needs more, it gets its own doc under `docs/`.
