# Deployment

## TL;DR — one command

```bat
:: Windows
run.bat              :: CLI chat
run.bat serve        :: HTTP API on :8000
run.bat ingest       :: rebuild vector store
```

```bash
# macOS / Linux / Git Bash
./run.sh             # CLI chat
./run.sh serve       # HTTP API on :8000
./run.sh ingest      # rebuild vector store
```

`run.bat` / `run.sh` create the venv, install deps, build the vector store
on first launch, and start the bot. Requires `.env` to already exist with
`OPENAI_API_KEY` set.

---

## Manual install (if you don't want the wrapper)

```bash
python -m venv .venv
# Windows:  .venv\Scripts\activate
# Unix:     source .venv/bin/activate

pip install -r requirements/base.txt        # CLI only
pip install -r requirements/api.txt         # + FastAPI + channels
pip install -r requirements/extras.txt      # + scraper, docx, anthropic

python -m scripts.ingest --client limmes
python -m scripts.chat   --client limmes
```

> **Got `ModuleNotFoundError: No module named 'loguru'`?** Your venv is
> active but `pip install -r requirements/base.txt` was never run. Use
> `run.bat` / `run.sh` and it's handled for you.

---

## Endpoints (HTTP mode)

| Method | Path                  | Purpose                                    |
| ------ | --------------------- | ------------------------------------------ |
| GET    | `/`                   | Demo landing page with embedded widget     |
| GET    | `/health`             | Liveness + per-channel readiness           |
| GET    | `/widget.js`          | Embeddable JS chat bubble                  |
| POST   | `/chat`               | `{message, session_id}` → answer + sources |
| DELETE | `/chat/{session_id}`  | Reset a conversation                       |
| POST   | `/webhook/whatsapp`   | Twilio                                     |
| POST   | `/webhook/telegram`   | Telegram                                   |
| POST   | `/webhook/line`       | LINE                                       |
| GET    | `/docs`               | Swagger UI                                 |

Smoke test:

```bash
curl http://localhost:8000/health
curl http://localhost:8000/chat -H 'Content-Type: application/json' \
     -d '{"message":"hello","session_id":"test"}'
```

---

## Docker

```bash
docker compose up -d --build
docker compose logs -f chatbot
docker compose exec chatbot python -m scripts.ingest    # re-index
```

Persistent volumes: `chatbot_vectorstore` (`/app/.vectorstore`),
`chatbot_sessions` (`/app/.sessions`). `data/` and `config/` are mounted
read-only from the host.

---

## Channels

| Channel  | Required env vars                                                | Webhook URL                           |
| -------- | ---------------------------------------------------------------- | ------------------------------------- |
| Web      | (none — always on)                                               | -                                     |
| WhatsApp | `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_WHATSAPP_NUMBER` | `https://host/webhook/whatsapp`     |
| Telegram | `TELEGRAM_BOT_TOKEN`                                             | `https://host/webhook/telegram`       |
| LINE     | `LINE_CHANNEL_SECRET`, `LINE_CHANNEL_ACCESS_TOKEN`               | `https://host/webhook/line`           |

Register the Telegram webhook once:

```bash
curl -F "url=https://host/webhook/telegram" \
     https://api.telegram.org/bot<TOKEN>/setWebhook
```

`/health` shows live channel readiness based on env vars.

---

## CLI commands inside `chat`

| Command  | Effect                            |
| -------- | --------------------------------- |
| `quit`   | Leave                             |
| `clear`  | Reset this session's history      |
| `sources`| Print citations from last answer  |

Sessions persist to `.sessions/<id>.json` (JSON file backend by default).

---

## Update knowledge base

```bash
# 1. drop or replace files under data/<client>/
# 2. re-index
python -m scripts.ingest --client <id>
# or just
run.bat ingest --client <id>
```

`scripts.ingest` always rebuilds from scratch. The engine also detects
content changes on startup (SHA256 of file paths/sizes/mtimes) and
rebuilds in-place.

---

## Optional — PostgreSQL sessions

```bash
pip install "psycopg[binary]>=3.2"
```

```env
MEMORY_BACKEND=postgres
POSTGRES_DSN=postgresql://chatbot:changeme@db:5432/chatbot
```

Schema is created on first run (`chatbot_sessions` table).

---

## Optional — scrape a website

```bash
python -m scripts.scrape --url https://example.com/about
python -m scripts.scrape --client limmes        # uses scrape_urls in YAML
python -m scripts.ingest --client limmes        # then re-ingest
```

Output goes to `data/scraped/` (or `--out <dir>`).

---

## Security & anti-abuse

The template ships with a layered defense stack, all tunable from
`.env` with zero code changes. See
[`SECURITY.md`](../SECURITY.md) for the full audit and roadmap.

### What protects your wallet

| Layer                  | Env var                                | Default      | Effect on abuse                                        |
| ---------------------- | -------------------------------------- | ------------ | ------------------------------------------------------ |
| Request body cap       | `API_MAX_BODY_BYTES`                   | `65536`      | Oversized bodies → HTTP 413 *before* JSON parsing.     |
| Per-message char cap   | `MAX_MESSAGE_CHARS`                    | `4000`       | Oversized messages → HTTP 429 with friendly detail.    |
| Rate limit per IP      | `RATE_LIMIT_IP_PER_MINUTE` (+ burst)   | `30` / `10`  | Token bucket; 429 + `Retry-After` on exhaustion.       |
| Rate limit per session | `RATE_LIMIT_SESSION_PER_MINUTE`        | `12` / `4`   | Stops one tab from hammering.                          |
| Daily token budget     | `DAILY_TOKEN_CAP`                      | `0` (off)    | Hard stop; 402 until UTC midnight.                     |
| Daily USD budget       | `DAILY_USD_CAP`                        | `0` (off)    | Hard stop; uses built-in price table.                  |
| Prompt-injection log   | (automatic)                            | on           | Suspicious messages logged at WARNING (non-blocking).  |

Recommended starting point for a small-business deployment on
`gpt-4o-mini`:

```env
DAILY_TOKEN_CAP=2000000      # ~$0.40–$1.60 / day at default prices
DAILY_USD_CAP=2
RATE_LIMIT_IP_PER_MINUTE=20
RATE_LIMIT_SESSION_PER_MINUTE=10
```

Tail the budget with `GET /health` — it reports the live daily counter
under `security.budget`.

### What protects your data

| Concern                    | How it's handled                                                |
| -------------------------- | --------------------------------------------------------------- |
| Prompt injection           | System prompt + retrieval-only rule + logged heuristic flag.    |
| Path traversal via session | `sanitize_session_id` — only `[A-Za-z0-9_\-:.@]` allowed.       |
| XSS in widget              | `textContent` only — never `innerHTML` for untrusted strings.   |
| Unsigned webhooks          | Twilio HMAC, LINE HMAC, Telegram secret-token all enforced in prod. |
| Error leaks                | Global `ChatbotError` handler returns `user_message`, hides stack. |
| CORS                       | `API_STRICT_CORS=true` refuses startup when `API_CORS_ORIGINS=*`. |
| Transport                  | `API_HSTS_ENABLED=true` + HSTS header once you serve HTTPS.     |
| Secret headers             | `X-Content-Type-Options`, `Referrer-Policy`, `Permissions-Policy`, `X-Frame-Options` on every response. |

### Webhook signatures

Production behaviour (`DEBUG=false`):

| Channel  | Required secret                                                       |
| -------- | --------------------------------------------------------------------- |
| Twilio   | `TWILIO_AUTH_TOKEN` — unset → webhook rejected with 403.              |
| LINE     | `LINE_CHANNEL_SECRET` — unset → webhook rejected with 403.            |
| Telegram | `TELEGRAM_WEBHOOK_SECRET` — unset → webhook rejected with 403.        |

When registering the Telegram webhook, pass the same value:

```bash
curl -F "url=https://host/webhook/telegram" \
     -F "secret_token=<TELEGRAM_WEBHOOK_SECRET>" \
     https://api.telegram.org/bot<TOKEN>/setWebhook
```

Telegram echoes it back in `X-Telegram-Bot-Api-Secret-Token` on every
update; the route uses a constant-time compare.

### Running behind a proxy

Terminate TLS at nginx / Caddy / Traefik. The app reads the leftmost
entry from `X-Forwarded-For` as the client IP for rate limiting. If you
expose the app *directly* to the internet, this header can be spoofed
— always put a proxy in front.

---

## Production checklist

- [ ] `OPENAI_API_KEY` set, billing enabled
- [ ] `ACTIVE_CLIENT` matches `config/clients/<id>.yaml`
- [ ] `data/<client>/` populated
- [ ] `python -m scripts.ingest --client <id>` runs cleanly
- [ ] `DEBUG=false`, `LOG_FORMAT=json`, `LOG_LEVEL=INFO`
- [ ] `API_STRICT_CORS=true` **and** `API_CORS_ORIGINS=https://your-domain.com`
- [ ] `API_HSTS_ENABLED=true` (only behind real HTTPS)
- [ ] `RATE_LIMIT_ENABLED=true` with per-IP + per-session limits tuned
- [ ] `DAILY_TOKEN_CAP` and/or `DAILY_USD_CAP` set to a safe ceiling
- [ ] `.budget/state.json` lives on a persistent volume
- [ ] `TWILIO_AUTH_TOKEN` / `LINE_CHANNEL_SECRET` / `TELEGRAM_WEBHOOK_SECRET` set
- [ ] TLS at reverse proxy, `Host` header preserved
- [ ] Channel env vars set, webhooks registered (with secret tokens)
- [ ] `/health` → 200 + `chain_ready: true` + `security.budget.enabled: true`
- [ ] Volumes for `.vectorstore`, `.sessions`, `.budget` are persistent

---

## Common errors

| Error                                  | Fix                                                          |
| -------------------------------------- | ------------------------------------------------------------ |
| `ModuleNotFoundError: No module named 'loguru'` | Run `run.bat` / `run.sh`, or `pip install -r requirements/base.txt` |
| `OPENAI_API_KEY is missing`            | Add it to `.env`                                             |
| `Personality file not found`           | `config/personalities/<name>.yaml` missing                   |
| `Client config file not found`         | `--client` doesn't match a `config/clients/<id>.yaml`        |
| `No supported files in <dir>`          | Drop a `.pdf`/`.md`/`.txt` under the client's data folder    |
| `chain_ready: false` in `/health`      | Lifespan failed — check API logs above the failed startup    |
| Twilio webhook 403                     | `TWILIO_AUTH_TOKEN` mismatch, or proxy rewrites `Host`       |
| Telegram webhook 503 / 403             | `TELEGRAM_BOT_TOKEN` or `TELEGRAM_WEBHOOK_SECRET` missing    |
| Chat returns 429 unexpectedly          | Raise `RATE_LIMIT_IP_PER_MINUTE` / `RATE_LIMIT_SESSION_PER_MINUTE` |
| Chat returns 402 ("today's limit")     | `DAILY_TOKEN_CAP` or `DAILY_USD_CAP` reached; resets UTC midnight |
| Startup fails with "strict CORS"       | Set `API_CORS_ORIGINS=https://your-domain` or `API_STRICT_CORS=false` |
| Hebrew renders as `??` in CLI          | `set PYTHONIOENCODING=utf-8` (Windows) — use Windows Terminal for RTL |

Run any script with `--debug` to see DEBUG-level Loguru output
(retrieval, prompts, model calls).
