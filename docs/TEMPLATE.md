# Template Guide — Deploying for a New Business

This document explains how to take the Limmes Chatbot codebase and
adapt it for a completely different business. No code changes needed —
only configuration.

---

## 1. How Templating Works

The codebase separates **code** (engine, channels, API) from
**configuration** (client YAML, personality YAML, data files, `.env`).
To deploy for a new company, you only touch configuration.

```
Code (shared, never touched per-client)
├── chatbot/          # Engine, API, channels, security, i18n
├── scripts/          # CLI entry points
└── requirements/     # Dependencies

Configuration (per-client)
├── config/clients/<company>.yaml      # Business identity, languages, channels
├── config/personalities/<tone>.yaml   # Bot personality preset
├── data/<company>/                    # Knowledge base files
└── .env                               # API keys, runtime settings
```

---

## 2. Step-by-Step: New Company Setup

### Step 1 — Create the client config

```bash
cp config/clients/default.yaml config/clients/acme.yaml
```

Edit `config/clients/acme.yaml`:

```yaml
id: acme
name: "Acme Corp — Customer Support"
language_primary: en
languages_offered: [en, es, fr] # Languages in widget picker
personality: sales # Pick a preset or create your own
system_prompt_extra: |
  About the business:
    • Acme Corp sells widgets and gadgets online.
    • Free shipping on orders over $50.
    • Returns accepted within 30 days.
greeting_override: "Hi! 👋 How can I help you today?"
data_paths: [data/acme]
channels:
  web: { enabled: true }
  whatsapp: { enabled: false }
  telegram: { enabled: false }
  line: { enabled: false }
```

### Step 2 — Add knowledge base files

```bash
mkdir -p data/acme/catalog data/acme/policies
cp your-product-catalog.pdf data/acme/catalog/
cp your-shipping-policy.md  data/acme/policies/
```

### Step 3 — Configure `.env`

```env
OPENAI_API_KEY=sk-...
ACTIVE_CLIENT=acme
DAILY_USD_CAP=5.0
```

### Step 4 — Ingest and run

```bash
python -m scripts.ingest --client acme
python -m scripts.serve
# Open http://localhost:8000
```

That's it. The bot now answers questions about Acme Corp using the
documents you provided.

---

## 3. Channel Combinations

Different businesses need different channels. Here are common patterns:

### Web Only (simplest)

Best for: marketing sites, landing pages, small businesses.

```yaml
# config/clients/acme.yaml
channels:
  web: { enabled: true }
  whatsapp: { enabled: false }
  telegram: { enabled: false }
  line: { enabled: false }
```

No extra credentials needed. Just run the server and embed the widget.

### Web + WhatsApp

Best for: businesses with customers on WhatsApp (Israel, Brazil, India, SEA).

```yaml
channels:
  web: { enabled: true }
  whatsapp: { enabled: true }
  telegram: { enabled: false }
  line: { enabled: false }
```

Requires in `.env`:

```env
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
```

### Web + LINE

Best for: businesses in Thailand, Japan, Taiwan.

```yaml
channels:
  web: { enabled: true }
  whatsapp: { enabled: false }
  telegram: { enabled: false }
  line: { enabled: true }
```

Requires in `.env`:

```env
LINE_CHANNEL_SECRET=...
LINE_CHANNEL_ACCESS_TOKEN=...
```

### Web + Telegram

Best for: tech-savvy audiences, communities, Middle East / Central Asia.

```yaml
channels:
  web: { enabled: true }
  whatsapp: { enabled: false }
  telegram: { enabled: true }
  line: { enabled: false }
```

Requires in `.env`:

```env
TELEGRAM_BOT_TOKEN=...
TELEGRAM_WEBHOOK_SECRET=<random-string>
```

### All Channels

For businesses that need maximum reach:

```yaml
channels:
  web: { enabled: true }
  whatsapp: { enabled: true }
  telegram: { enabled: true }
  line: { enabled: true }
```

---

## 4. Language Configuration

### Monolingual (e.g. US English only)

```yaml
language_primary: en
languages_offered: [en] # Widget shows no picker (single language)
```

### Bilingual (e.g. Hebrew + English)

```yaml
language_primary: he
languages_offered: [he, en]
```

### Multi-language with Thai

```yaml
language_primary: th
languages_offered: [th, en, zh, ja]
```

### Supported languages (12 total)

`en`, `he`, `ar`, `fa`, `th`, `fr`, `es`, `de`, `ru`, `ja`, `zh`, `hi`

To add a new language: add an entry to `chatbot/i18n/messages.py` in
both `SUPPORTED_LANGUAGES` and `MESSAGES`.

---

## 5. Personality Options

| Personality         | Temperature | Use case        | Key traits                                          |
| ------------------- | ----------- | --------------- | --------------------------------------------------- |
| `default`           | 0.7         | General         | Balanced, professional, clear                       |
| `sales`             | 0.85        | E-commerce      | Enthusiastic, conversion-oriented, cross-sells      |
| `clinic`            | 0.4         | Healthcare      | Calm, safety-first, redirects to professionals      |
| `official`          | 0.2         | Government      | Formal, factual, cites sources, refuses speculation |
| `friendly_official` | 0.55        | Public service  | Warm but rule-respecting, plain language            |
| `design_studio`     | 0.6         | Interior design | Tasteful, consultative, design vocabulary           |

### Custom personality

Create `config/personalities/my_tone.yaml`:

```yaml
name: my_tone
description: "Casual, emoji-friendly, Gen-Z vibes"
system_prompt: |
  You are a super chill customer service agent. Use casual language,
  emojis where appropriate, and keep it real. Be helpful but never
  corporate or stiff.
temperature: 0.8
greeting: "Hey! 👋 What's up?"
fallback_message: "Hmm not sure about that one! Want me to connect you with the team?"
style_keywords: [casual, friendly, emoji-aware]
refuse_topics: [politics, religion]
```

---

## 6. What's Built vs What's Left

Moved to [`FEATURES.md`](FEATURES.md) — single source of truth for capabilities + roadmap.

---

## 7. Quick Reference — New Project Checklist

```
1.  cp config/clients/default.yaml config/clients/<company>.yaml
2.  Edit the YAML: id, name, languages, personality, system_prompt_extra
3.  mkdir -p data/<company>/
4.  Drop knowledge-base files into data/<company>/
5.  Edit .env: OPENAI_API_KEY, ACTIVE_CLIENT=<company>
6.  python -m scripts.ingest --client <company>
7.  python -m scripts.serve
8.  Open http://localhost:8000 — test the widget
9.  Test each offered language in the widget picker
10. Set DAILY_USD_CAP before going public
11. Add channel credentials if using WhatsApp/Telegram/LINE
12. Deploy behind a reverse proxy with TLS
```
