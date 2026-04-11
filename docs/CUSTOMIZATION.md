# Customization

Three things, never any Python edits: **client YAML**, **personality YAML**,
**the data folder**.

## TL;DR — onboard a new client

```bash
# 1. config/clients/<id>.yaml          (client YAML, see template below)
# 2. data/<id>/...                     (PDFs, .md, .txt, .docx, .csv, .json, .html)
# 3. .env  →  ACTIVE_CLIENT=<id>
# 4. rebuild + run
run.bat ingest --client <id>
run.bat chat   --client <id>
```

---

## Client YAML template

`config/clients/<id>.yaml`

```yaml
id: <id>
name: "Display Name"
language_primary: en       # default reply language; he|ar|fa|ur → auto-RTL
language_fallback: en
# Codes in the widget language picker (first = default). Empty list =
# only language_primary. See chatbot/i18n/messages.py for the full list.
languages_offered:
  - en
  - es
  - fr
  - th
  - he
  - ar
location: "City, Country"
timezone: "UTC"

personality: default       # one of: default | sales | clinic |
                           #         official | friendly_official | design_studio

system_prompt_extra: |
  About the business:
    • Hours, phone, address.
    • Anything you want appended to the system prompt.

greeting_override: "Welcome! How can I help?"   # optional

data_paths:
  - data/<id>

scrape_urls:               # optional, used by `scripts.scrape --client <id>`
  - https://example.com

channels:
  web:        { enabled: true }
  whatsapp:   { enabled: false }
  telegram:   { enabled: false }
  line:       { enabled: false }
```

> `channels:` is a doc hint only. Channels are *actually* enabled by
> setting the matching env vars in `.env`. `/health` shows the live
> truth.

---

## Personality YAML template

`config/personalities/<name>.yaml`

```yaml
name: <name>
description: "Free-form, for humans."
system_prompt: |
  You are a ... assistant. Voice, rules, goals.
temperature: 0.7
greeting: "Opening line."
fallback_message: "Sent when info is missing."
style_keywords:  [friendly, concise]
refuse_topics:   [legal advice, medical diagnosis]
```

| Field              | Required | What it does                                  |
| ------------------ | -------- | --------------------------------------------- |
| `name`             | yes      | Must match the filename                       |
| `system_prompt`    | yes      | Voice, rules, goals                           |
| `temperature`      | no       | Default LLM temperature                       |
| `greeting`         | no       | Channel opening line                          |
| `fallback_message` | no       | Shown on error / missing info                 |
| `style_keywords`   | no       | Tone hints appended to system prompt          |
| `refuse_topics`    | no       | Topics the bot must politely decline          |

Built-in presets: `default`, `sales`, `clinic`, `official`,
`friendly_official`, `design_studio`.

---

## Data folder rules

Drop files anywhere under `data/<client>/`. Walked recursively.
Supported extensions:

```
.pdf  .txt  .md  .markdown  .html  .htm  .docx  .csv  .json  .jsonl
```

After adding/changing files:

```bash
run.bat ingest --client <id>
```

Add a new format → register a loader in `chatbot/rag/loaders.py`:

```python
def _load_epub(path):
    from langchain_community.document_loaders import UnstructuredEPubLoader
    docs = UnstructuredEPubLoader(str(path)).load()
    for d in docs:
        d.metadata["source"] = path.name
        d.metadata["file_type"] = "epub"
    return docs

LOADER_REGISTRY[".epub"] = _load_epub
```

---

## Retrieval knobs (`.env`)

| Var              | Default | Effect                                    |
| ---------------- | ------- | ----------------------------------------- |
| `CHUNK_SIZE`     | 1000    | Chars per chunk (rebuild after change)    |
| `CHUNK_OVERLAP`  | 200     | Continuity across chunks (rebuild)        |
| `RETRIEVAL_K`    | 4       | Chunks per question (no rebuild needed)   |

When in doubt, raise `RETRIEVAL_K` first (6–8 for long technical docs).

---

## Switch LLM provider

```env
LLM_PROVIDER=anthropic
LLM_MODEL=claude-opus-4-6
ANTHROPIC_API_KEY=sk-ant-...
```

```bash
pip install -r requirements/extras.txt   # ships langchain-anthropic
```

Embeddings stay on OpenAI by default (`text-embedding-3-small`). Swap in
`chatbot/rag/vectorstore.py::_build_embeddings` if needed.

---

## Memory / sessions

```env
MEMORY_BACKEND=file        # memory | file | postgres
MAX_HISTORY_TURNS=10
```

For multi-instance deploys see
[`DEPLOYMENT.md` → PostgreSQL sessions](DEPLOYMENT.md#optional--postgresql-sessions).

---

## Languages (and how the picker works)

The template ships UI translations for **12 languages** — English,
Hebrew, Arabic, Farsi, Thai, French, Spanish, German, Russian, Japanese,
Chinese, Hindi. The bot *itself* understands many more; this list is
only for the widget's UI strings (placeholder, send button,
"thinking…", error toasts, language picker labels).

```yaml
language_primary: he
languages_offered:
  - he
  - en
  - ar
  - th
  - ru
greeting_override: "שלום! איך אפשר לעזור?"
```

What happens:

1. The widget renders a 🌐 language picker with one entry per code in
   `languages_offered`. The first entry is the default.
2. When the visitor picks a language, the widget stores it in
   `localStorage` and sends `language: "<code>"` on every subsequent
   `/chat` request.
3. The engine passes the code into the system prompt at request time:
   *"Reply in `'th'` unless the user clearly writes in another
   language."* No chain rebuild needed — the template is rebuilt per
   turn from a prompt input.
4. RTL layout flips automatically when the chosen language is `he`,
   `ar`, `fa`, or `ur`.

### Adding a new language

Append a row to `chatbot/i18n/messages.py`:

```python
SUPPORTED_LANGUAGES.append(LanguageInfo("ko", "Korean", "한국어"))

MESSAGES["ko"] = {
    "placeholder":      "메시지를 입력하세요…",
    "send":             "보내기",
    "thinking":         "생각 중…",
    "connection_error": "연결 오류입니다. 다시 시도하세요.",
    "rate_limited":     "메시지를 너무 빨리 보내고 있습니다.",
    "too_long":         "메시지가 너무 깁니다.",
    "language":         "언어",
    "clear":            "대화 지우기",
    "minimize":         "최소화",
    "powered_by":       "AI 어시스턴트",
    "welcome":          "안녕하세요! 무엇을 도와드릴까요?",
    "budget_reached":   "오늘 사용량 한도에 도달했습니다. 내일 다시 시도하세요.",
}
```

Missing keys fall back to English, so partial translations are fine.

### CLI / Python use

```python
bot.ask("สวัสดี ร้านเปิดกี่โมง?", session_id="u1", language="th")
```

---

## Security & anti-abuse

See [`docs/DEPLOYMENT.md`](DEPLOYMENT.md#security--anti-abuse) and
[`SECURITY.md`](../SECURITY.md) for the full rundown. The short version:

- **Rate limits** — per IP + per session, token-bucket, configurable.
- **Body size cap** — requests over `API_MAX_BODY_BYTES` get 413.
- **Daily token/spend cap** — budgets reset at 00:00 UTC; exceeding
  returns 402 with a friendly message.
- **Prompt-injection heuristics** — logged, non-blocking.
- **Webhook signatures** — Twilio / LINE / Telegram secrets are enforced
  in production (`DEBUG=false`).
- **Strict CORS** — set `API_STRICT_CORS=true` to fail startup when
  `API_CORS_ORIGINS` is `*` or empty.

All knobs live in `.env`; see `.env.example` for the commented list.
