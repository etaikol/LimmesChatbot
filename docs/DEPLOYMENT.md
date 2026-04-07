# Deployment

This guide is the **single source of truth** for getting the chatbot
running. Every command below has been verified end-to-end against this
codebase. If something here does not match the code, the docs are wrong
and a PR is welcome.

There are three shapes you'll deploy in:

1. **Local CLI** — fastest way to test a knowledge base.
2. **HTTP API + web widget** — single server behind a reverse proxy.
3. **Docker** — what you'll actually ship to a VPS.

Then channels (WhatsApp, Telegram, LINE) plug in via webhooks once the
API is reachable.

---

## 0. Prerequisites

| Need              | Why                                                       |
| ----------------- | --------------------------------------------------------- |
| Python ≥ 3.10     | The whole project. 3.11/3.12 recommended.                 |
| `OPENAI_API_KEY`  | Used for both the chat LLM **and** embeddings.            |
| Docker (optional) | Only if you ship via the included `docker-compose.yml`.   |

Get an OpenAI key at <https://platform.openai.com/api-keys>. Even if you
plan to swap to Anthropic for the chat model, embeddings still default
to OpenAI's `text-embedding-3-small` (cheapest decent quality). To swap
embeddings, edit `chatbot/rag/vectorstore.py::_build_embeddings`.

---

## 1. Local — CLI only

This is the smallest possible install: no FastAPI, no channels, just
the chat engine in your terminal.

```bash
# 1. Clone and enter the repo
git clone <your-fork-or-this-repo>.git limmes-chatbot
cd limmes-chatbot

# 2. Create a virtualenv
python -m venv .venv
# Linux / macOS:
source .venv/bin/activate
# Windows (PowerShell):
.venv\Scripts\Activate.ps1
# Windows (Git Bash):
source .venv/Scripts/activate

# 3. Install minimal deps
pip install -r requirements/base.txt

# 4. Configure
cp .env.example .env
#   open .env and set:
#     OPENAI_API_KEY=sk-...
#     ACTIVE_CLIENT=limmes        (or whichever client id you want)

# 5. Drop your knowledge base
#   Anything you put under data/<client>/ is walked recursively.
#   Supported extensions: .pdf .txt .md .markdown .html .htm .docx .csv .json .jsonl
ls data/limmes/        # the repo ships sample data for this client

# 6. Build the vector store
python -m scripts.ingest --client limmes

# 7. Talk to it
python -m scripts.chat --client limmes
```

You'll see a banner with the client name, personality, language, and
model — then a `you >` prompt. Commands inside the REPL:

| Command             | Effect                                |
| ------------------- | ------------------------------------- |
| `quit` / `exit`     | Leave                                 |
| `clear`             | Reset this conversation's history     |
| `sources`           | Print citations from the last answer  |
| (anything else)     | Sent to the bot                       |

Sessions are persisted to `.sessions/<session-id>.json` by default.

### What if it fails?

The package raises typed exceptions with actionable messages. Common ones:

| Error                                          | What to do                                                                 |
| ---------------------------------------------- | -------------------------------------------------------------------------- |
| `OPENAI_API_KEY is missing...`                 | Add it to `.env`                                                           |
| `Personality file not found: ...`              | Make sure `config/personalities/<name>.yaml` exists and matches the client |
| `Client config file not found: ...`            | `--client` argument doesn't match a `config/clients/<id>.yaml`             |
| `No supported files in <data dir>`             | Drop at least one `.pdf`/`.md`/`.txt` file under the client's data folder  |
| `Rate limit reached`                           | Wait a few seconds and retry                                               |
| `quota` / `billing`                            | Top up your OpenAI account                                                 |

Run with `--debug` to see DEBUG-level Loguru output (model calls,
retrieval scores, prompts).

---

## 2. Local — HTTP API

Same machine, now exposing FastAPI + the embeddable web widget + all
channel webhooks.

```bash
# Add the API extras
pip install -r requirements/api.txt

# Start
python -m scripts.serve
```

Default URL: `http://0.0.0.0:8000`. Endpoints:

| Method   | Path                  | Purpose                                          |
| -------- | --------------------- | ------------------------------------------------ |
| GET      | `/`                   | Demo landing page (with embedded widget)         |
| GET      | `/health`             | Liveness + channel readiness                     |
| GET      | `/widget.js`          | One-line embeddable JS chat bubble               |
| POST     | `/chat`               | `{message, session_id}` → answer + sources       |
| DELETE   | `/chat/{session_id}`  | Reset a conversation                             |
| POST     | `/webhook/whatsapp`   | Twilio                                            |
| POST     | `/webhook/telegram`   | Telegram                                          |
| POST     | `/webhook/line`       | LINE                                              |
| GET      | `/docs`               | Swagger UI                                       |
| GET      | `/redoc`              | ReDoc                                            |

Quick `curl` smoke test:

```bash
curl -s http://localhost:8000/health | jq
# {
#   "status": "ok",
#   "client": "Limmes - Interior Design",
#   "personality": "design_studio",
#   "model": "gpt-4o-mini",
#   "chain_ready": true,
#   "active_sessions": 0,
#   "channels": { "web": true, "whatsapp": false, "telegram": false, "line": false }
# }

curl -s http://localhost:8000/chat \
     -H 'Content-Type: application/json' \
     -d '{"message":"What time do you open?","session_id":"curl-test"}' | jq
```

If `/health` returns 200 with `chain_ready: true`, the engine is
healthy. The `channels` object reports which providers have valid env
vars set — that is the live truth, not what `config/clients/*.yaml`
declares.

### Embedding the widget

The widget is one line of HTML:

```html
<script src="https://your-host.example.com/widget.js" async></script>
```

It auto-flips to RTL when the active client's `language_primary` is
`he`, `ar`, `fa`, or `ur`. If the widget is hosted on a different
origin than your site, set `API_CORS_ORIGINS` in `.env`:

```env
API_CORS_ORIGINS=https://www.your-site.com,https://your-site.com
```

### Run options

```bash
python -m scripts.serve                  # default host/port from .env
python -m scripts.serve --host 127.0.0.1 --port 9000
python -m scripts.serve --reload         # uvicorn hot reload (dev only)
python -m scripts.serve --debug          # DEBUG logs
```

---

## 3. Docker

The repo ships a multi-stage `Dockerfile` and a `docker-compose.yml`.

```bash
cp .env.example .env
# fill in OPENAI_API_KEY (and ACTIVE_CLIENT if not 'default')

docker compose up -d --build
docker compose logs -f chatbot
```

The container exposes port `8000`. Two named volumes persist state
across restarts:

| Volume                 | Mounted at         | Purpose                              |
| ---------------------- | ------------------ | ------------------------------------ |
| `chatbot_vectorstore`  | `/app/.vectorstore`| Chroma embeddings                    |
| `chatbot_sessions`     | `/app/.sessions`   | Per-user JSON conversation history   |

Your `data/` and `config/` folders are mounted **read-only** from the
host, so you can edit on the host and re-ingest in-place:

```bash
# Force a clean re-index after editing data/
docker compose exec chatbot python -m scripts.ingest

# Tail the logs
docker compose logs -f chatbot

# Restart
docker compose restart chatbot
```

The first request after a restart will rebuild the vector store
automatically if the `data/` SHA changed since the last ingest — see
`load_or_create_vectorstore` in `chatbot/rag/vectorstore.py`.

### Behind a reverse proxy

Terminate TLS at nginx / Caddy / Traefik and forward to `127.0.0.1:8000`.
Minimal nginx server block:

```nginx
server {
    server_name bot.example.com;
    listen 443 ssl http2;
    ssl_certificate     /etc/letsencrypt/live/bot.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/bot.example.com/privkey.pem;

    location / {
        proxy_pass         http://127.0.0.1:8000;
        proxy_set_header   Host              $host;
        proxy_set_header   X-Real-IP         $remote_addr;
        proxy_set_header   X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
        proxy_read_timeout 60s;
    }
}
```

**Important for Twilio**: keep the `Host` header intact. The Twilio
signature validator hashes the full URL including host; if your proxy
rewrites it, signature validation will reject every request.

---

## 4. Channels

Once the API is reachable from the public internet, plug in any subset
of these. The `channels:` block in `config/clients/<id>.yaml` is just a
documentation hint — the *actual* on/off switch is whether the right
env vars are present. `/health` reflects the live truth.

### 4a. Web widget

Nothing to configure beyond CORS. See [Embedding the widget](#embedding-the-widget).

### 4b. WhatsApp (Twilio)

1. Create a Twilio account → enable the **WhatsApp Sandbox** (or get an
   approved sender for production).
2. In your `.env`:
   ```env
   TWILIO_ACCOUNT_SID=AC...
   TWILIO_AUTH_TOKEN=...
   TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
   ```
3. In Twilio Console → WhatsApp Sandbox → "When a message comes in",
   set: `https://bot.example.com/webhook/whatsapp` (HTTP POST).
4. Restart the API. `curl https://bot.example.com/health` should now
   show `"whatsapp": true`.

The adapter validates Twilio's `X-Twilio-Signature` header against
`TWILIO_AUTH_TOKEN`. If you leave `TWILIO_AUTH_TOKEN` empty, signature
validation is skipped (dev mode only — never do that in production).

### 4c. Telegram

1. Talk to [@BotFather](https://t.me/BotFather) → `/newbot` → copy the
   token.
2. In `.env`:
   ```env
   TELEGRAM_BOT_TOKEN=123456:ABC-DEF...
   ```
3. Register the webhook (one-time):
   ```bash
   curl -F "url=https://bot.example.com/webhook/telegram" \
        https://api.telegram.org/bot<TOKEN>/setWebhook
   ```
4. Restart the API. Send `/start` to your bot in Telegram.

Built-in commands handled by the adapter:

| Command   | Effect                                  |
| --------- | --------------------------------------- |
| `/start`  | Greeting                                |
| `/help`   | Brief help message                      |
| `/clear`  | Reset *this* user's conversation memory |

### 4d. LINE

1. Create a Messaging API channel at
   <https://developers.line.biz/console/>.
2. In `.env`:
   ```env
   LINE_CHANNEL_SECRET=...
   LINE_CHANNEL_ACCESS_TOKEN=...
   ```
3. In the channel settings → "Webhook URL", set
   `https://bot.example.com/webhook/line` and enable "Use webhook".
4. Disable "Auto-reply messages" in LINE settings — otherwise LINE
   answers before your bot does.

The adapter verifies `X-Line-Signature` (HMAC-SHA256 over the raw
body) before processing. If `LINE_CHANNEL_SECRET` is empty, validation
is skipped (dev only).

---

## 5. Sessions in PostgreSQL (optional)

By default, conversations are stored as one JSON file per session under
`.sessions/`. That works fine for a single instance. For multi-instance
deployments (load balancer + several API pods), switch to PostgreSQL:

```bash
pip install "psycopg[binary]>=3.2"
```

```env
MEMORY_BACKEND=postgres
POSTGRES_DSN=postgresql://chatbot:changeme@db.example.com:5432/chatbot
```

The `chatbot_sessions` table is created on first run (see
`chatbot/persistence/database.py`). The schema is intentionally tiny:

```sql
CREATE TABLE chatbot_sessions (
    session_id TEXT PRIMARY KEY,
    messages   JSONB NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

To use the bundled PostgreSQL container, uncomment the `postgres:`
service block in `docker-compose.yml`.

---

## 6. Logging & observability

All logs flow through Loguru. FastAPI / uvicorn / LangChain stdlib logs
are intercepted into the same pipeline (see
`chatbot/logging_setup.py::_InterceptHandler`).

| Setting       | Values             | What it does                                       |
| ------------- | ------------------ | -------------------------------------------------- |
| `LOG_LEVEL`   | DEBUG/INFO/...     | Minimum level (use DEBUG to inspect retrieval)     |
| `LOG_FORMAT`  | `pretty` / `json`  | `json` = one JSON object per line (for prod)       |
| `LOG_FILE`    | path or empty      | Optional file sink, daily rotation, 14-day retain  |

Liveness probe (`/health`) confirms:

- The chain is built (`chain_ready: true`)
- The model name and personality
- Which channels have valid credentials

```bash
docker compose exec chatbot \
    python -c "import httpx; print(httpx.get('http://localhost:8000/health').json())"
```

---

## 7. Updating the knowledge base

Drop or replace files under `data/<client>/`, then run one of:

```bash
# Local
python -m scripts.ingest --client <id>

# Docker
docker compose exec chatbot python -m scripts.ingest --client <id>
```

`scripts.ingest` always rebuilds from scratch — it deletes
`.vectorstore/` and re-embeds everything. The engine *also* detects
content changes automatically on startup (SHA256 of file
paths/sizes/mtimes) and rebuilds in-place if needed.

---

## 8. Scraping a client's website

If a client has no documents, scrape their site once and treat the
output as data:

```bash
# Pass URLs explicitly
python -m scripts.scrape \
    --url https://shantiyoga.example.com/about \
    --url https://shantiyoga.example.com/schedule

# Or use the urls listed in the client's YAML (scrape_urls: [...])
python -m scripts.scrape --client limmes
```

Each URL becomes one `.txt` file under `data/scraped/` (or
`--out <dir>` if you want it elsewhere). Re-run `ingest` afterwards to
embed the new files.

---

## 9. Programmatic use (Python)

You don't need the API to use the bot. Import it directly:

```python
from chatbot import Chatbot

bot = Chatbot.from_client("limmes")          # picks up .env
response = bot.ask("מתי אתם פתוחים בשישי?", session_id="user-1")

print(response.answer)
for src in response.sources:
    print(" -", src.source, "p.", src.page)
```

`Chatbot` constructors:

| Constructor                          | When to use                                          |
| ------------------------------------ | ---------------------------------------------------- |
| `Chatbot.from_env()`                 | Read `ACTIVE_CLIENT` from `.env`                     |
| `Chatbot.from_client("<id>")`        | Force a specific client config                       |
| `Chatbot(profile, settings, ...)`    | Inject your own retriever/llm/memory (advanced/test) |

---

## 10. Going to production — checklist

- [ ] `OPENAI_API_KEY` set, billing enabled
- [ ] `ACTIVE_CLIENT` matches a `config/clients/<id>.yaml`
- [ ] `data/<client>/` populated with real documents
- [ ] `python -m scripts.ingest --client <id>` runs cleanly at least once
- [ ] `LOG_FORMAT=json`, `LOG_LEVEL=INFO`
- [ ] `API_CORS_ORIGINS` restricted to the real client domain(s) — not `*`
- [ ] TLS terminated by your reverse proxy
- [ ] Channel credentials in `.env`, webhook URLs registered
- [ ] `/health` returns 200 with `chain_ready: true` and the channels
      you expect set to `true`
- [ ] Volumes for `.vectorstore` and `.sessions` are persistent
- [ ] Session backup configured (file copies of `.sessions/`, or
      PostgreSQL backups)
- [ ] You've sent at least one real message through every channel you
      enabled and verified the reply is grounded in your `data/`

---

## Troubleshooting

| Symptom                                              | Likely cause / fix                                                                  |
| ---------------------------------------------------- | ----------------------------------------------------------------------------------- |
| `OPENAI_API_KEY is missing`                          | `.env` not loaded — check working directory, or set the env var explicitly         |
| `chain_ready: false` in `/health`                    | Lifespan failed — check the API logs above the failed startup                       |
| Bot answers in English when client is `he`           | Add `language_primary: he` and a Hebrew `greeting_override` in the client YAML      |
| Bot ignores your documents                           | `python -m scripts.ingest --client <id>` (force a clean rebuild) and check the logs |
| Twilio webhook returns 403                           | `TWILIO_AUTH_TOKEN` mismatch, or proxy rewrites `Host` header                        |
| Telegram webhook returns 503                         | `TELEGRAM_BOT_TOKEN` not set in the running process's env                            |
| LINE webhook returns 403                             | `LINE_CHANNEL_SECRET` mismatch, or your proxy mutates the request body              |
| Widget bubble doesn't appear                         | CORS — check `API_CORS_ORIGINS` and the browser devtools network tab                |
| Hebrew renders as `??` in the CLI                    | Windows console codepage — set `PYTHONIOENCODING=utf-8` before running              |
