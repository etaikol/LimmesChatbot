# Customization

Everything you'll do day-to-day involves three things: **client configs**,
**personality presets**, and **the data folder**. None of them require
Python edits.

## Adding a new client

Say you're onboarding a yoga studio called *Shanti*.

### 1. Create the client file

`config/clients/shanti.yaml`

```yaml
id: shanti
name: "Shanti Yoga"
language_primary: en
language_fallback: en
location: "Tel Aviv, Israel"
timezone: "Asia/Jerusalem"

personality: clinic       # calm, reassuring tone

system_prompt_extra: |
  About the studio:
    • Shanti Yoga offers Hatha, Vinyasa, and prenatal classes.
    • Drop-in price 80₪. 10-class card 700₪.
    • Mats and props are provided. Showers on site.

greeting_override: "Welcome to Shanti — how can I help you today?"

data_paths:
  - data/shanti

scrape_urls:
  - https://shantiyoga.example.com/schedule

channels:
  web:        { enabled: true }
  whatsapp:   { enabled: true }
  telegram:   { enabled: false }
  line:       { enabled: false }
```

### 2. Drop the knowledge base

```
data/shanti/
├── schedule/
│   └── weekly_class_schedule.pdf
├── pricing/
│   └── packages.md
└── about/
    └── teachers.md
```

### 3. Activate it

Edit `.env`:

```
ACTIVE_CLIENT=shanti
```

Or pass it explicitly:

```bash
python -m scripts.chat   --client shanti
python -m scripts.ingest --client shanti --rebuild
python -m scripts.serve  # picks up ACTIVE_CLIENT
```

That's it. The bot now answers as *Shanti Yoga* with the *clinic*
personality, citing its own documents.

## Adding a new personality

Personalities live under `config/personalities/`. Each is a small YAML.

```yaml
# config/personalities/realtor.yaml
name: realtor
description: |
  Energetic, knowledgeable assistant for real-estate offices. Helps
  visitors filter listings and book viewings.

system_prompt: |
  You are a friendly real-estate assistant. Help visitors discover
  listings that fit their needs (location, budget, bedrooms, garden).
  Always offer to schedule a viewing once you've matched a property.
  Never invent listings, prices, or square meters — answer from context.

temperature: 0.7
greeting: "Hi! Looking for a new home? Tell me what you have in mind."
fallback_message: "Let me check that with our agents and get back to you."

style_keywords:
  - friendly
  - market-savvy
  - solution-oriented
```

Then point a client at it:

```yaml
# config/clients/acme_realty.yaml
personality: realtor
...
```

No code changes — just YAML.

### Personality fields

| Field                | Required | What it does                                      |
| -------------------- | -------- | ------------------------------------------------- |
| `name`               | yes      | Identifier (must match the filename)              |
| `description`        | no       | Free-form, for humans                             |
| `system_prompt`      | yes      | The voice, rules, and goals of the bot            |
| `temperature`        | no       | Default LLM temperature for this personality      |
| `greeting`           | no       | Opening line shown by the channel                 |
| `fallback_message`   | no       | Sent when something goes wrong or info is missing |
| `style_keywords`     | no       | Tone hints appended to the system prompt          |
| `refuse_topics`      | no       | Topics the bot must politely decline              |

## Adding a new file type

Suppose you want the bot to read `.epub` books.

1. **Pick a loader.** LangChain Community ships
   `UnstructuredEPubLoader`. Install its system deps separately.
2. **Register it** in `chatbot/rag/loaders.py`:

```python
def _load_epub(path: Path) -> list[Document]:
    from langchain_community.document_loaders import UnstructuredEPubLoader
    docs = UnstructuredEPubLoader(str(path)).load()
    for d in docs:
        d.metadata["source"] = path.name
        d.metadata["file_type"] = "epub"
    return docs

LOADER_REGISTRY[".epub"] = _load_epub
```

3. Re-ingest: `python -m scripts.ingest --rebuild`.

That's the entire integration.

## Hebrew (and other languages)

OpenAI's `gpt-4o-mini` already handles Hebrew, Arabic, Russian, and most
RTL/LTR languages natively. The template helps in three places:

1. **Client config** — `language_primary: he` adds a language hint to
   the system prompt and flips the web widget to RTL.
2. **Greeting override** — write your greeting directly in the target
   language for a more native feel.
3. **`Translator` tool** — when you need to force-translate something
   (e.g. a knowledge-base file written in English to display in Hebrew):

```python
from chatbot.tools.translator import Translator
t = Translator()
print(t.translate("Welcome!", target="he"))
```

## Modes vs personalities — what's the difference?

There are no separate "modes". A *mode* in the user-facing sense is just
a personality file. We ship six (default, sales, clinic, official,
friendly_official, design_studio) and you can add more without touching
code. To switch a client between modes, change one line in their YAML:

```diff
- personality: clinic
+ personality: sales
```

## Channel toggles

`channels: {...}` in the client YAML is a documentation/feature-flag
hint. The actual *enabling* of WhatsApp/Telegram/LINE happens by setting
the right env vars in `.env`. The `/health` endpoint reports the live
truth based on which tokens are present.

## Tuning retrieval

Three knobs in `.env`:

- `CHUNK_SIZE` — bigger = more context per chunk, fewer chunks. Default
  1000 chars.
- `CHUNK_OVERLAP` — keeps continuity across chunk boundaries. Default
  200.
- `RETRIEVAL_K` — how many chunks to feed the LLM per question. Default
  4. Bump to 6–8 for long technical docs.

When in doubt: **increase `RETRIEVAL_K` first**, *then* play with chunk
sizes.

## Switching LLM provider

```env
LLM_PROVIDER=anthropic
LLM_MODEL=claude-opus-4-6
ANTHROPIC_API_KEY=sk-ant-...
```

```bash
pip install langchain-anthropic
python -m scripts.serve
```

Embeddings still use OpenAI by default (`text-embedding-3-small`)
because Chroma needs an embedding function and OpenAI's is the cheapest
high-quality option. Swap it inside `chatbot/rag/vectorstore.py` if you
prefer something else.
