# Architecture

Four ideas:

1. **One engine, many channels.** `Chatbot` is the only place where
   retrieval, memory, and LLM calls happen. Channels are thin adapters.
2. **Configuration is data.** New client = new YAML. New tone = new YAML.
3. **The data folder is the contract.** Drop files in `data/`, the
   loader registry picks the right reader by extension.
4. **Defaults that get you to "Hello"** — escape hatches when you grow.

```
CLI · Web widget · Twilio · Telegram · LINE
                    │
                    ▼
              ┌──────────┐
              │ Chatbot  │  core/engine.py
              └────┬─────┘
        ┌─────────┼─────────┐
        ▼         ▼         ▼
  SessionStore  RAGRetriever  LLMProvider
   memory|file   (Chroma)     OpenAI|Anthropic
   |postgres        ▲
                    │
                  data/  (.pdf .md .txt .html .docx .csv .json ...)
```

---

## Module map

| Module                          | Responsibility                                                |
| ------------------------------- | ------------------------------------------------------------- |
| `chatbot/settings.py`           | `Settings` (pydantic-settings, env + `.env`)                  |
| `chatbot/logging_setup.py`      | Loguru + stdlib intercept, optional file sink                 |
| `chatbot/exceptions.py`         | `ChatbotError` hierarchy with `user_message`                  |
| `chatbot/core/profile.py`       | `PersonalityConfig`, `ClientConfig`, merged `ChatbotProfile`  |
| `chatbot/core/memory.py`        | `Message`, `ConversationMemory`, `SessionStore`               |
| `chatbot/core/engine.py`        | `Chatbot.ask / greet / reset` + `from_client / from_env`      |
| `chatbot/core/prompts.py`       | `RAG_CHAT_TEMPLATE` (system / context / history / question)   |
| `chatbot/llm/providers.py`      | `LLMProvider.from_settings()` → OpenAI or Anthropic           |
| `chatbot/llm/chains.py`         | `build_rag_chain(llm, retriever, system_prompt)` (LCEL)       |
| `chatbot/rag/loaders.py`        | `LOADER_REGISTRY` mapping extension → loader fn               |
| `chatbot/rag/ingestion.py`      | `ingest_paths`, `ingest_data_directory` (recursive walk)      |
| `chatbot/rag/vectorstore.py`    | Chroma store + SHA256 change detection (`ingestion_meta.json`) |
| `chatbot/rag/retriever.py`      | `RAGRetriever` (plain + LangChain `BaseRetriever`)            |
| `chatbot/channels/cli.py`       | REPL: `quit`, `clear`, `sources`                              |
| `chatbot/channels/whatsapp.py`  | Twilio: form → TwiML, signature check                         |
| `chatbot/channels/telegram.py`  | Bot API: JSON → `sendMessage`                                 |
| `chatbot/channels/line.py`      | LINE Messaging API: HMAC + reply                              |
| `chatbot/api/app.py`            | FastAPI factory + lifespan (builds global `Chatbot`)          |
| `chatbot/api/routes/health.py`  | `GET /health`                                                 |
| `chatbot/api/routes/chat.py`    | `POST /chat`, `DELETE /chat/{id}`                             |
| `chatbot/api/routes/webhooks.py`| `POST /webhook/{whatsapp,telegram,line}`                      |
| `chatbot/api/routes/widget.py`  | `GET /widget.js` + demo page builder                          |
| `chatbot/api/routes/admin.py`   | Admin API: overview, sessions, budget, config, LINE, data     |
| `chatbot/api/routes/admin_ui.py`| Admin dashboard SPA (inline HTML/JS)                          |
| `chatbot/channels/line_flex.py` | LINE Flex Message builders (product, contact, carousel)       |
| `chatbot/channels/line_rich_menu.py`| LINE Rich Menu CRUD + CLI                                 |
| `chatbot/tools/scraper.py`      | BeautifulSoup → one `.txt` per URL under `data/scraped/`      |
| `chatbot/tools/translator.py`   | LLM-backed translator                                         |
| `chatbot/persistence/database.py` | Optional PostgreSQL session backend (lazy import)           |

---

## `Chatbot.ask` — what runs each turn

```
1. history     = SessionStore.history_text(session_id)
2. answer      = chain.invoke({question, history})
                   ├─ retriever fetches top-K chunks
                   ├─ formats them as [src p.N] blocks
                   ├─ fills RAG_CHAT_TEMPLATE
                   └─ ChatOpenAI / ChatAnthropic
3. SessionStore.add_message(user)
   SessionStore.add_message(assistant)
4. sources     = retriever.retrieve(question)        # for citation
→ ChatResponse(answer, session_id, sources, metadata)
```

---

## Decisions

| Area              | Choice                              | Why                              |
| ----------------- | ----------------------------------- | -------------------------------- |
| LLM framework     | LangChain LCEL                      | Mature, swappable providers      |
| Vector store      | Chroma (file-persistent)            | Zero infra, embedded             |
| Settings          | pydantic-settings                   | Typed, env-aware, validated      |
| Logging           | Loguru + stdlib intercept           | One config, structured           |
| Channels          | Adapter pattern                     | Add a channel without core edits |
| Personalities     | YAML files                          | Editable by non-engineers        |
| Sessions          | File backend by default             | No external service              |
| Async             | Sync engine, async API routes       | Simpler engine, FastAPI for I/O  |

---

## Where to extend

| You want to…                            | Do this                                                          |
| --------------------------------------- | ---------------------------------------------------------------- |
| Add a client                            | `config/clients/<id>.yaml` + `data/<id>/`                        |
| Add a personality                       | `config/personalities/<name>.yaml`                               |
| Add a file format                       | Register a fn in `chatbot/rag/loaders.py::LOADER_REGISTRY`       |
| Add an LLM provider                     | New `_build_xxx` + branch in `chatbot/llm/providers.py`          |
| Add a channel (Discord, Slack, ...)     | New `chatbot/channels/<name>.py` + route in `routes/webhooks.py` |
| Move to PostgreSQL sessions             | `MEMORY_BACKEND=postgres`, install `psycopg[binary]`             |
| Replace Chroma with pgvector            | Edit `chatbot/rag/vectorstore.py::_make_chroma`                  |
| Replace OpenAI embeddings               | Edit `chatbot/rag/vectorstore.py::_build_embeddings`             |
