# Limmes Chatbot Template

A clean, opinionated template for shipping production-grade AI chatbots
to small and mid-sized businesses. Drop in your client's documents,
pick a personality, and you have a multi-channel assistant ready to go.

```
You: "What time do you open on Friday?"
Bot: "We're open from 9:00 to 14:00 on Fridays. Anything else I can help with?"
```

## What you get

- **RAG over any file**: PDF, TXT, Markdown, HTML, DOCX, CSV, JSON.
  Drop files in `data/`, run one command, done.
- **Personality presets**: `default`, `sales`, `clinic`, `official`,
  `friendly_official`, `design_studio`. Switch the tone with one line.
- **Multi-channel**: Web widget, WhatsApp (Twilio), Telegram, LINE.
  All ride on the same chat engine.
- **Sessions & memory**: per-user conversations persisted to disk
  (or PostgreSQL — opt-in).
- **Clean structure**: Pydantic settings, Loguru logging, LangChain
  pipelines, no spaghetti.
- **Hebrew + RTL ready**: tested with `he`, plus auto-RTL web widget.
- **Docker-first**: `docker compose up` and you're live.

## 60-second start

```bash
# 1. Install (CLI only)
python -m venv .venv && source .venv/bin/activate    # or .venv\Scripts\activate on Windows
pip install -r requirements/base.txt

# 2. Configure
cp .env.example .env
# edit .env -> set OPENAI_API_KEY and ACTIVE_CLIENT

# 3. Drop your knowledge base
cp some-product-catalog.pdf data/limmes/catalog/

# 4. Try it
python -m scripts.chat --client limmes
```

To run the multi-channel HTTP server instead:

```bash
pip install -r requirements/api.txt
python -m scripts.serve
# open http://localhost:8000
```

## Project layout

```
.
├── chatbot/                 # The package — import this in your code
│   ├── core/                #   engine, memory, profiles, prompts
│   ├── rag/                 #   loaders, ingestion, vector store
│   ├── llm/                 #   providers (OpenAI, Anthropic), chains
│   ├── channels/            #   CLI, WhatsApp, Telegram, LINE adapters
│   ├── api/                 #   FastAPI app, routes, web widget
│   ├── tools/               #   web scraper, translator
│   ├── persistence/         #   optional PostgreSQL backend
│   ├── settings.py          #   Pydantic settings (env vars)
│   ├── logging_setup.py     #   Loguru setup + stdlib intercept
│   └── exceptions.py
│
├── config/
│   ├── personalities/       # bot tone presets (YAML)
│   └── clients/             # per-client configs (YAML)
│
├── data/                    # ← Drop files here. Walked recursively.
│   └── limmes/
│       ├── about/
│       ├── catalog/
│       └── policies/
│
├── scripts/                 # CLI entry-points
│   ├── chat.py              #   python -m scripts.chat
│   ├── serve.py             #   python -m scripts.serve
│   ├── ingest.py            #   python -m scripts.ingest
│   └── scrape.py            #   python -m scripts.scrape
│
├── requirements/            # split installs (base / api / extras / all)
├── docs/                    # ARCHITECTURE.md, CUSTOMIZATION.md, DEPLOYMENT.md
├── pyproject.toml
├── Dockerfile
├── docker-compose.yml
└── .env.example
```

## How a single chat turn works

```
User message
   │
   ▼
Channel adapter (CLI / Web / WhatsApp / Telegram / LINE)
   │  builds session_id from sender
   ▼
Chatbot.ask(question, session_id)
   │
   ├─► SessionStore.get(session_id)        ← conversation history
   │
   ├─► RAGRetriever.retrieve(question)     ← top-K relevant chunks
   │       └── Chroma vector store
   │
   ├─► LangChain RAG chain
   │       ├── system_prompt (personality + client extras)
   │       ├── retrieved context
   │       ├── conversation history
   │       └── user question
   │       │
   │       ▼
   │   ChatOpenAI / ChatAnthropic
   │
   ├─► SessionStore.add_message(...)       ← persist memory
   │
   ▼
ChatResponse(answer, session_id, sources[])
```

## Customizing for a new client

Three files. That's it.

1. **`config/clients/<id>.yaml`** — pick a personality, set language,
   add business facts, list data folders, toggle channels.
2. **`data/<id>/...`** — drop the knowledge base.
3. **`.env`** — set `ACTIVE_CLIENT=<id>` plus channel tokens.

Walk-through in [`docs/CUSTOMIZATION.md`](docs/CUSTOMIZATION.md).

## Choosing a personality

| Preset                | Best for                                              |
| --------------------- | ----------------------------------------------------- |
| `default`             | Generic helpful assistant (safe baseline)             |
| `sales`               | Retail, e-commerce, lead-gen                          |
| `clinic`              | Health, wellness, calm anxious users                  |
| `official`            | Legal, finance, formal compliance-heavy contexts      |
| `friendly_official`   | Government / municipal — warm but rule-respecting     |
| `design_studio`       | Interior design, furniture, architecture (Limmes)     |

Add your own under `config/personalities/<name>.yaml` — see existing files
as templates.

## Channels at a glance

| Channel    | How clients reach the bot                | Setup                                |
| ---------- | ---------------------------------------- | ------------------------------------ |
| Web widget | `<script src="/widget.js" async>` on any page | none (auto)                     |
| WhatsApp   | Twilio sandbox / approved sender         | `TWILIO_AUTH_TOKEN` + webhook URL    |
| Telegram   | @BotFather, set webhook                  | `TELEGRAM_BOT_TOKEN`                 |
| LINE       | Messaging API channel                    | `LINE_CHANNEL_*` env vars            |

Full deployment notes in [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md).

## Programmatic use

```python
from chatbot import Chatbot

bot = Chatbot.from_client("limmes")
response = bot.ask("מתי אתם פתוחים בשישי?", session_id="user-1")

print(response.answer)
for s in response.sources:
    print(" -", s.source, "p.", s.page)
```

## Docs

- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — every module explained
- [`docs/CUSTOMIZATION.md`](docs/CUSTOMIZATION.md) — adding clients, personalities, file types
- [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) — Docker, channels, ops

## License

MIT.
