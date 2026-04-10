# Usage Guide

Everything you need to get the most out of the Limmes Chatbot template,
from dropping data files to configuring multi-channel integrations.

---

## 1. The `data/` Folder — How RAG Works

The chatbot answers questions **only** from documents you place under
`data/`. No internet search, no hallucinated facts.

### How it works

1. You place files in `data/<client_id>/` (e.g. `data/limmes/`).
2. Run `python -m scripts.ingest --client limmes` (or `run.bat ingest`).
3. The ingestion pipeline:
   - Recursively finds every supported file (PDF, MD, TXT, HTML, DOCX, CSV, JSON).
   - Splits each file into overlapping chunks (`CHUNK_SIZE=1000`, `CHUNK_OVERLAP=200`).
   - Embeds chunks with OpenAI `text-embedding-3-small`.
   - Stores them in a local ChromaDB vector store (`.vectorstore/`).
4. At query time, the 4 most relevant chunks are retrieved and injected
   into the LLM's system prompt as `=== Context ===`.

### Recommended folder structure

```
data/limmes/
├── catalog/            # Product PDFs, spec sheets
├── policies/           # Shipping, returns, warranty
├── about/              # Hours, location, team bios
└── faqs/               # Common Q&A documents
```

### Supported file types

| Extension         | Loader             | Notes                                     |
| ----------------- | ------------------ | ----------------------------------------- |
| `.pdf`            | PyPDF              | Most reliable; works out of the box       |
| `.md`, `.txt`     | Plain text (UTF-8) | Great for structured info like hours      |
| `.html`, `.htm`   | BeautifulSoup      | Requires `beautifulsoup4` (in extras.txt) |
| `.docx`           | docx2txt           | Requires `docx2txt` (in extras.txt)       |
| `.csv`            | Row-by-row         | Each row becomes a chunk                  |
| `.json`, `.jsonl` | JSON               | Flattens objects into text                |

### Tips for best RAG quality

- **Short, focused files** beat one giant PDF. Split your catalog by
  category.
- **Use Markdown** with clear headings for structured info (hours,
  policies). The chunker respects heading boundaries.
- **Name files descriptively** — the filename is stored as metadata and
  shown in source citations.
- **Re-ingest after changes** — the system detects file-content changes
  via SHA256 hashing and auto-rebuilds on server start. You can also
  force rebuild with `--rebuild`.
- **Temp files**: Word creates `~$` lock files — the ingestion pipeline
  warns and skips them automatically.

---

## 2. Personalities — Controlling the Bot's Tone

Personalities live under `config/personalities/`. Each is a YAML file.

### Available presets

| Preset              | Temperature | Best for                                     |
| ------------------- | ----------- | -------------------------------------------- |
| `default`           | 0.7         | General-purpose, balanced                    |
| `sales`             | 0.85        | E-commerce, conversion-oriented              |
| `clinic`            | 0.4         | Healthcare, wellness (safety-first)          |
| `official`          | 0.2         | Legal, government (formal, factual)          |
| `friendly_official` | 0.55        | Public service (warm + rule-respecting)      |
| `design_studio`     | 0.6         | Interior design, furniture, lifestyle brands |

### Personality fields

```yaml
name: sales
description: "Energetic, conversion-oriented"
system_prompt: |
  You are a friendly sales assistant...
temperature: 0.85
greeting: "Hi! Looking for something special today?"
fallback_message: "I don't have that info, but let me connect you with our team."
style_keywords: [enthusiastic, helpful, concise]
refuse_topics: [competitor pricing, politics]
```

- **`system_prompt`**: The core personality instruction injected into every LLM call.
- **`temperature`**: Controls randomness (0 = deterministic, 1 = creative).
- **`refuse_topics`**: The bot will politely redirect when asked about these.
- **`style_keywords`**: Appended as a `Tone: ...` instruction.

### Creating a custom personality

1. Copy an existing preset: `cp config/personalities/default.yaml config/personalities/my_brand.yaml`
2. Edit the YAML fields.
3. Reference it in your client config: `personality: my_brand`

---

## 3. Client Configuration

Clients live under `config/clients/`. Each YAML file configures one
business deployment.

### Key fields

```yaml
id: limmes # Must match the filename
name: "Limmes — Interior Design"
language_primary: he # Default reply language
languages_offered: [he, en, ar, ru, th, fr] # Widget language picker
personality: design_studio # Links to personalities/<name>.yaml

system_prompt_extra: | # Business-specific facts appended to the prompt
  About the business:
    • We sell furniture and lighting...
    • Opening hours: Sun–Thu 09:00–19:00...

greeting_override: "שלום! 👋 ..." # Overrides personality.greeting for primary language

data_paths: [data/limmes] # Where the RAG pipeline looks for documents
scrape_urls: # URLs to scrape for data (optional)
  - https://www.example.com/

channels:
  web: { enabled: true }
  whatsapp: { enabled: true }
  telegram: { enabled: false }
  line: { enabled: false }
```

### Language behaviour

- `language_primary` — the default reply language when no preference is given.
- `languages_offered` — shown in the widget's language picker. The user picks one, and it's sent with every `/chat` request so the LLM replies in that language.
- The `greeting_override` applies to the **primary language only**. Other languages use their i18n `welcome` string from `chatbot/i18n/messages.py`.

---

## 4. Prompts — How the System Prompt is Built

At request time, the engine assembles the system prompt from four layers:

```
1. Personality system_prompt      (sales.yaml → "You are a friendly sales assistant...")
2. Client system_prompt_extra     (limmes.yaml → "About the business: ...")
3. Refuse topics                  ("Politely refuse to discuss: ...")
4. Style keywords                 ("Tone: enthusiastic, helpful, concise.")
5. Language instruction           ("IMPORTANT — REPLY LANGUAGE: You MUST reply in 'th'.")
```

The language instruction is placed **last** so it always takes precedence.
This ensures a Thai user who selects Thai in the widget gets Thai
responses, even if the client config mentions Hebrew as the business's
primary language.

The full RAG prompt template (in `chatbot/core/prompts.py`) then wraps
this with:

```
[system] <assembled system prompt>
[system] Use the following knowledge-base context... === Context === ...
[system] Recent conversation: <history>
[human]  <user's question>
```

---

## 5. Channel Integrations

### Web Widget (Done — fully functional)

Drop one script tag into any HTML page:

```html
<script src="https://your-api/widget.js" async></script>
```

Features:

- Language picker with 12 languages, auto-RTL for Hebrew/Arabic/Farsi
- Per-tab session persistence (localStorage)
- Glassmorphism UI, mobile responsive
- Typing indicator, error handling, rate-limit messages

### WhatsApp via Twilio (Done — ready to configure)

**Status**: Adapter fully implemented. Signature validation works.
Needs Twilio account + credentials.

Setup:

1. Create a Twilio account, enable WhatsApp sandbox.
2. Set in `.env`:
   ```
   TWILIO_ACCOUNT_SID=AC...
   TWILIO_AUTH_TOKEN=...
   TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
   ```
3. Point the sandbox webhook to `POST https://<your-domain>/webhook/whatsapp`
4. Enable in client config: `channels: { whatsapp: { enabled: true } }`

What works:

- Inbound message handling, session per phone number
- HMAC signature validation (Twilio RequestValidator)
- TwiML XML response format
- Fallback messages on errors

What's left for production:

- Migrate from sandbox to Twilio WhatsApp Business profile
- Media message handling (images, documents from user)
- Outbound/proactive messaging

### LINE Messaging API (Done — ready to configure)

**Status**: Adapter fully implemented with raw HTTP (no line-bot-sdk
dependency). HMAC-SHA256 signature validation. Needs LINE developer
credentials.

Setup:

1. Create a Messaging API channel at https://developers.line.biz/console/
2. Set in `.env`:
   ```
   LINE_CHANNEL_SECRET=...
   LINE_CHANNEL_ACCESS_TOKEN=...
   ```
3. Register webhook: `POST https://<your-domain>/webhook/line`
4. Enable in client config: `channels: { line: { enabled: true } }`

What works:

- Text message events, grouped by user ID
- HMAC-SHA256 signature validation
- Async reply via LINE Reply API
- Error handling and logging

What's left for production:

- Rich messages (Flex Messages, Quick Replies)
- Image/video/file handling
- Rich menu setup
- Group chat support

### Telegram (Done — ready to configure)

**Status**: Adapter works via raw HTTP (httpx), no SDK.

Setup:

1. Create a bot via @BotFather on Telegram.
2. Set in `.env`:
   ```
   TELEGRAM_BOT_TOKEN=...
   TELEGRAM_WEBHOOK_SECRET=<random-string>
   ```
3. Register webhook:
   ```
   curl "https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://<host>/webhook/telegram&secret_token=<SECRET>"
   ```

What works:

- Text message handling, `/start`, `/help`, `/clear` commands
- Secret token validation
- Async reply via Bot API

---

## 6. Running the Project

### Quick start (Windows)

```bat
run.bat chat                   # CLI chatbot
run.bat serve                  # FastAPI server on :8000
run.bat ingest                 # Rebuild vector store
run.bat scrape                 # Scrape URLs from client config
```

### Quick start (macOS / Linux)

```bash
./run.sh chat
./run.sh serve
./run.sh ingest
./run.sh scrape
```

### Direct scripts

```bash
python -m scripts.chat --client limmes
python -m scripts.serve --port 8000 --reload
python -m scripts.ingest --client limmes --rebuild
python -m scripts.scrape --url https://example.com
```

### Docker

```bash
docker compose up              # Starts API on :8000
docker compose up --build      # Rebuild after code changes
```

---

## 7. Environment Variables — Quick Reference

| Variable             | Required | Default        | Description                              |
| -------------------- | -------- | -------------- | ---------------------------------------- |
| `OPENAI_API_KEY`     | Yes      | —              | OpenAI API key                           |
| `ACTIVE_CLIENT`      | No       | `default`      | Which `config/clients/<id>.yaml` to load |
| `LLM_MODEL`          | No       | `gpt-4o-mini`  | Model name                               |
| `LLM_PROVIDER`       | No       | `openai`       | `openai` or `anthropic`                  |
| `DEBUG`              | No       | `false`        | Enables dev-mode webhook bypass          |
| `RATE_LIMIT_ENABLED` | No       | `true`         | Toggle rate limiting                     |
| `DAILY_USD_CAP`      | No       | `5.0`          | Max daily LLM spend                      |
| `DAILY_TOKEN_CAP`    | No       | `500_000`      | Max daily LLM token usage                |
| `API_CORS_ORIGINS`   | No       | `*`            | Comma-separated allowed origins          |
| `API_STRICT_CORS`    | No       | `false`        | Refuse to start if CORS is `*`           |
| `MEMORY_BACKEND`     | No       | `file`         | `memory`, `file`, or `postgres`          |

This table is a quick reference for the most commonly changed settings. See
`.env.example` for the full current list with comments, including additional
spam/admin-related controls.

---

## 8. Best Practices

1. **Start with the CLI** (`run.bat chat`) to test your data and personality
   before launching the API.
2. **Keep data files small and focused** — one file per topic gives better
   retrieval than one giant document.
3. **Set a daily budget** (`DAILY_USD_CAP=5.0`) before exposing to the public.
4. **Test every language** you offer — open the widget, switch language, and
   verify the greeting, placeholder, and LLM response are all in the correct
   language.
5. **Use `LOG_FORMAT=json`** in production for structured logging.
6. **Put a reverse proxy** (nginx, Caddy) in front for TLS.
7. **Back up `.sessions/`** if conversation history matters to you.
