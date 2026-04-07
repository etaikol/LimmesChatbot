# Architecture

This template is built around four ideas:

1. **One engine, many channels.** The `Chatbot` class is the only place
   where retrieval, memory, and LLM calls happen. Channels (CLI, Web,
   WhatsApp, Telegram, LINE) are *thin adapters* that translate from a
   provider's payload format and back.
2. **Configuration is data, not code.** A new client = a new YAML file.
   A new bot tone = a new YAML file. No Python edits required for
   day-to-day work.
3. **The data folder is the contract.** Anything you put under `data/`
   becomes part of the bot's knowledge. The pipeline picks the right
   loader by file extension.
4. **Defaults that get you to "Hello"** — and escape hatches when you
   outgrow them (Anthropic, PostgreSQL, custom loaders, scraping).

```
┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐
│  CLI / scripts   │   │  Web widget JS   │   │  Twilio webhook  │   │ Telegram / LINE  │
└────────┬─────────┘   └────────┬─────────┘   └────────┬─────────┘   └────────┬─────────┘
         │                      │                      │                      │
         └──────────────────────┴──────────┬───────────┴──────────────────────┘
                                           │
                                           ▼
                                   ┌──────────────┐
                                   │  Chatbot()   │   <- core/engine.py
                                   └──────┬───────┘
                ┌──────────────────────┬──┴──┬──────────────────────┐
                ▼                      ▼     ▼                      ▼
        ┌───────────────┐   ┌──────────────────┐          ┌──────────────────┐
        │ SessionStore  │   │   RAGRetriever   │          │   LLMProvider    │
        │ (memory|file| │   │   ┌────────────┐ │          │  (OpenAI |       │
        │  postgres)    │   │   │  Chroma    │ │          │   Anthropic)     │
        └───────────────┘   │   └────────────┘ │          └──────────────────┘
                            │   ┌────────────┐ │
                            │   │ ingestion  │ │
                            │   └─────┬──────┘ │
                            │         ▼        │
                            │   ┌────────────┐ │
                            │   │   data/    │ │
                            │   │ pdf md txt │ │
                            │   │ html docx  │ │
                            │   └────────────┘ │
                            └──────────────────┘
```

## Modules

### `chatbot/settings.py`
A single `Settings` class powered by `pydantic-settings`. Reads
environment variables and `.env`. Provides typed access for everything
else in the package via `get_settings()` (LRU-cached singleton).

### `chatbot/logging_setup.py`
Loguru-based, with a stdlib `logging` interceptor so FastAPI/uvicorn/
LangChain logs flow through the same pipeline. Pretty for development,
JSON for production. File rotation with 14-day retention.

### `chatbot/exceptions.py`
A small hierarchy: `ChatbotError → ConfigError | IngestionError |
LLMError | RetrievalError | ChannelError`. Every public exception has a
`user_message` that channels show to end users instead of stack traces.

### `chatbot/core/profile.py`
Two Pydantic models loaded from YAML:

- `PersonalityConfig` — system prompt, temperature, tone, refuse-topics.
- `ClientConfig` — id, name, language, data paths, channels, plus an
  `system_prompt_extra` for business facts.

`ChatbotProfile` is the merged view used by the engine; its
`effective_system_prompt` glues personality + client extras + a small
language hint.

### `chatbot/core/memory.py`
Two layers:

- `Message` / `ConversationMemory` — value objects (one chat history).
- `SessionStore` — pluggable backend keyed on `session_id`. Backends:
  - `memory`: process-local dict (tests).
  - `file`: one JSON file per session under `.sessions/`.
  - `postgres`: optional, see `chatbot/persistence/database.py`.

### `chatbot/core/engine.py`
The `Chatbot` class. Constructed once per process.

```python
class Chatbot:
    def ask(self, question: str, session_id: str) -> ChatResponse: ...
    def greet(self) -> str: ...
    def reset(self, session_id: str) -> None: ...

    @classmethod
    def from_client(cls, client_id: str) -> "Chatbot": ...
    @classmethod
    def from_env(cls)              -> "Chatbot": ...
```

`ask()` runs four steps:

1. Load history from the session store.
2. Invoke the prebuilt LangChain RAG chain.
3. Persist user + assistant messages.
4. Collect retrieved chunks as `SourceDocument`s for citation.

### `chatbot/core/prompts.py`
All prompt templates live here. The chain template uses placeholders
`{system_prompt}`, `{context}`, `{history}`, `{question}`. Tweak wording
without touching glue code.

### `chatbot/llm/providers.py`
`LLMProvider.from_settings()` returns a thin wrapper around a
`langchain_core.language_models.BaseChatModel`. Currently supports OpenAI
and Anthropic. Add a provider by writing `_build_xxx()` and a branch in
`from_settings`.

### `chatbot/llm/chains.py`
`build_rag_chain(llm, retriever, system_prompt)` returns a LangChain
runnable that takes `{"question", "history"}` and returns a string.

### `chatbot/rag/loaders.py`
`LOADER_REGISTRY: dict[str, Callable]` maps file extensions to loader
functions. Each returns a list of `langchain_core.documents.Document`.
Add a new format with one entry.

### `chatbot/rag/ingestion.py`
- `ingest_paths(paths)` — load + chunk a list of files.
- `ingest_data_directory(dir)` — recursively walk, ignore unsupported
  extensions, return chunked Documents.

### `chatbot/rag/vectorstore.py`
- `load_or_create_vectorstore()` — open existing Chroma store, or build
  one from `data/`. Detects content changes via a SHA256 of file
  paths/sizes/mtimes.
- `build_vectorstore(documents)` — embed and persist a fresh batch.

### `chatbot/rag/retriever.py`
`RAGRetriever` wraps the vector store and exposes both a plain
`retrieve(query)` and a LangChain `BaseRetriever` for use inside chains.

### `chatbot/channels/`
Each adapter takes a `Chatbot` instance and a provider payload:

- `cli.py`        — REPL with commands (`quit`, `clear`, `sources`).
- `whatsapp.py`   — Twilio: form payload in, TwiML XML out, signature check.
- `telegram.py`   — Bot API: JSON in, async reply via `sendMessage`.
- `line.py`       — LINE Messaging API: HMAC signature, async reply.

The web channel ships with the API as a JS widget rather than a class.

### `chatbot/api/`
- `app.py` — FastAPI app factory + lifespan that builds the global
  `Chatbot` once at startup.
- `routes/health.py` — `/health` returns model + channel readiness.
- `routes/chat.py` — `POST /chat` for any custom client and the widget.
- `routes/webhooks.py` — `/webhook/whatsapp`, `/webhook/telegram`,
  `/webhook/line`.
- `routes/widget.py` — `/widget.js` and the demo landing page.

### `chatbot/tools/`
- `scraper.py` — Tiny BeautifulSoup-based scraper. Strips scripts/styles
  and writes one `.txt` per URL into `data/scraped/`.
- `translator.py` — LLM-backed translator (no extra service required).

### `chatbot/persistence/database.py`
Optional PostgreSQL backend for sessions. Imported lazily so the rest of
the project does not require psycopg.

## Decision points (and why)

| Decision                            | Choice                              | Reason                              |
| ----------------------------------- | ----------------------------------- | ----------------------------------- |
| LLM framework                       | LangChain LCEL                      | Mature, swappable providers         |
| Vector store                        | Chroma (file-persistent)            | Zero infra, embedded                |
| Settings                            | pydantic-settings                   | Typed, env-aware, validated         |
| Logging                             | Loguru + stdlib intercept           | Single configuration, structured    |
| Channels                            | Adapter pattern                     | Add a channel without touching core |
| Personalities                       | YAML files                          | Editable by non-engineers           |
| Session storage                     | File backend by default             | No external service needed          |
| Async                               | Sync engine, async API routes       | Simpler engine, FastAPI handles I/O |

## Where to extend

| You want to…                              | Do this                                              |
| ----------------------------------------- | ---------------------------------------------------- |
| Add a new client                          | Create `config/clients/<id>.yaml` + drop files in `data/<id>/` |
| Add a new personality                     | Create `config/personalities/<name>.yaml`            |
| Add a new file format to RAG              | Register a loader in `chatbot/rag/loaders.py`        |
| Add a new LLM provider                    | Add `_build_xxx` in `chatbot/llm/providers.py`       |
| Add a new channel (Discord, Slack, ...)   | New file in `chatbot/channels/` + a route under `chatbot/api/routes/webhooks.py` |
| Move from file sessions to a real DB      | Set `MEMORY_BACKEND=postgres`, install `psycopg[binary]`, set `POSTGRES_DSN` |
| Replace Chroma with pgvector              | Edit `chatbot/rag/vectorstore.py::_make_chroma`      |
