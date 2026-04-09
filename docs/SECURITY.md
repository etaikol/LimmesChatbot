# Security Architecture

This document covers every security control in the Limmes Chatbot
template, the threat model they defend against, and what remains to
harden before a full public launch.

---

## 1. Defence-in-Depth Overview

Every request goes through multiple layers before it costs a cent:

```
Client request
  │
  ├─ 1  Body-size middleware      (reject > 64 KB before parsing)
  ├─ 2  Hardened response headers (X-Content-Type-Options, X-Frame-Options, …)
  ├─ 3  CORS policy               (restrict origins in production)
  ├─ 4  Per-IP rate limiter        (token bucket, 30 req/min default)
  ├─ 5  Per-session rate limiter   (12 req/min per chat tab)
  ├─ 6  Input sanitization         (Unicode NFC, control chars, length cap)
  ├─ 7  Prompt-injection heuristic (non-blocking, logged for monitoring)
  ├─ 8  Daily token/spend budget   (hard cap before the LLM call)
  └─ 9  LLM call (paid)
```

Cheapest checks run first so abusive traffic is rejected before it
reaches the paid LLM call.

---

## 2. Module Reference

### `chatbot/security/headers.py` — SecurityHeadersMiddleware

An ASGI middleware that runs on **every** request and response:

| Control          | Header / behaviour                                                                        | Default                                                                   |
| ---------------- | ----------------------------------------------------------------------------------------- | ------------------------------------------------------------------------- |
| Body-size guard  | Rejects any request with `Content-Length` above the cap _before_ the JSON parser sees it. | 64 KiB (`API_MAX_BODY_BYTES`)                                             |
| Content sniffing | `X-Content-Type-Options: nosniff`                                                         | Always                                                                    |
| Clickjacking     | `X-Frame-Options: DENY`                                                                   | Always                                                                    |
| Referrer leak    | `Referrer-Policy: strict-origin-when-cross-origin`                                        | Always                                                                    |
| Feature policy   | `Permissions-Policy: camera=(), microphone=(), geolocation=()`                            | Always                                                                    |
| Transport        | `Strict-Transport-Security`                                                               | Off by default; enable via `API_HSTS_ENABLED=true` when behind real HTTPS |

### `chatbot/security/rate_limit.py` — RateLimiter

Token-bucket rate limiter keyed by IP or session ID:

| Setting               | Env var                         | Default |
| --------------------- | ------------------------------- | ------- |
| Per-IP burst          | `RATE_LIMIT_IP_BURST`           | 10      |
| Per-IP sustained      | `RATE_LIMIT_IP_PER_MINUTE`      | 30      |
| Per-session burst     | `RATE_LIMIT_SESSION_BURST`      | 4       |
| Per-session sustained | `RATE_LIMIT_SESSION_PER_MINUTE` | 12      |
| Enable/disable        | `RATE_LIMIT_ENABLED`            | `true`  |

Implementation: in-memory per process. For multi-instance deployments,
swap the internal dict for Redis or a shared store.

When a limit is hit the API returns **HTTP 429** with a `Retry-After`
header.

### `chatbot/security/budget.py` — BudgetGuard

Daily spend cap (tokens and/or USD) persisted to a JSON state file:

| Setting                 | Env var                | Default              |
| ----------------------- | ---------------------- | -------------------- |
| Daily token cap         | `DAILY_TOKEN_CAP`      | 0 (disabled)         |
| Daily USD cap           | `DAILY_USD_CAP`        | 0.0 (disabled)       |
| State file              | `BUDGET_STATE_FILE`    | `.budget/state.json` |
| Price override (input)  | `PRICE_IN_USD_PER_1K`  | auto from model      |
| Price override (output) | `PRICE_OUT_USD_PER_1K` | auto from model      |

The guard runs a **pessimistic pre-check** before the LLM call (counts
the system prompt + history + question) and a **post-record** after the
answer is produced. If the daily cap is exceeded, the API returns
**HTTP 402** and the widget shows a "today's limit reached" message.

### `chatbot/security/sanitize.py` — Input Sanitization

| Function                        | What it does                                                                                                                                                                      |
| ------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `sanitize_user_input()`         | Unicode NFC normalisation, strips control characters, collapses whitespace, enforces `MAX_MESSAGE_CHARS` (default 4000)                                                           |
| `sanitize_session_id()`         | Restricts to alphanumeric, `-`, `_`, `:`, `@` — safe for filenames and database keys                                                                                              |
| `looks_like_prompt_injection()` | Non-blocking heuristic that flags messages containing patterns like "ignore previous instructions", "you are now", "jailbreak", etc. Logged and recorded, never blocks on its own |

### Webhook Authentication

| Channel           | Mechanism                                                         | Production behaviour                             |
| ----------------- | ----------------------------------------------------------------- | ------------------------------------------------ |
| WhatsApp (Twilio) | `X-Twilio-Signature` HMAC validated via `twilio.RequestValidator` | Rejected when `TWILIO_AUTH_TOKEN` is unset       |
| Telegram          | `X-Telegram-Bot-Api-Secret-Token` (constant-time compare)         | Rejected when `TELEGRAM_WEBHOOK_SECRET` is unset |
| LINE              | `X-Line-Signature` HMAC-SHA256 (base64)                           | Rejected when `LINE_CHANNEL_SECRET` is unset     |

In `DEBUG=true` mode, missing secrets log a warning and let webhooks
through — **never run DEBUG=true in production**.

---

## 3. CORS Policy

| Env var            | Default         | Recommendation                                                               |
| ------------------ | --------------- | ---------------------------------------------------------------------------- |
| `API_CORS_ORIGINS` | `*` (allow all) | Set to your real domains: `https://example.com,https://www.example.com`      |
| `API_STRICT_CORS`  | `false`         | Set `true` in production — the app **refuses to start** if CORS is still `*` |

---

## 4. Threat Model

| Threat                                                                | Mitigation                                                                                    | Status                              |
| --------------------------------------------------------------------- | --------------------------------------------------------------------------------------------- | ----------------------------------- |
| **Denial-of-wallet** — attacker floods chat to burn LLM credits       | Rate limits (IP + session) + daily budget cap                                                 | Done                                |
| **Prompt injection** — user tricks bot into ignoring its instructions | Heuristic detection + structured prompt (system→context→history→user)                         | Partial (heuristic is non-blocking) |
| **XSS via widget** — attacker injects script through chat messages    | Widget uses `textContent` (never `innerHTML`) for message bubbles                             | Done                                |
| **SSRF via scraper** — attacker feeds internal URLs                   | Scraper is a CLI script, not exposed to end users                                             | Done                                |
| **Webhook forgery** — attacker fakes Twilio/Telegram/LINE callbacks   | Signature validation per provider                                                             | Done                                |
| **Session enumeration** — attacker guesses session IDs                | Session IDs sanitised to safe characters; file-based storage doesn't expose directory listing | Done                                |
| **Oversized payloads** — large body causes memory pressure            | Body-size middleware rejects before parsing                                                   | Done                                |
| **Transport sniffing** — eavesdropping                                | HSTS header available, rely on reverse proxy TLS                                              | Done (opt-in)                       |
| **Data exfiltration from RAG** — bot leaks private docs               | Bot can only surface docs it was given; no internet search tool                               | By design                           |

---

## 5. Production Hardening Checklist

Before going live:

- [ ] Set `API_STRICT_CORS=true` and `API_CORS_ORIGINS` to your real domains.
- [ ] Set `API_HSTS_ENABLED=true` (requires HTTPS via reverse proxy).
- [ ] Set `DAILY_USD_CAP` to a sensible daily limit (e.g. `5.0`).
- [ ] Set `DAILY_TOKEN_CAP` as a secondary guard (e.g. `500000`).
- [ ] Set `DEBUG=false`.
- [ ] Set `TWILIO_AUTH_TOKEN`, `TELEGRAM_WEBHOOK_SECRET`, `LINE_CHANNEL_SECRET` for any enabled channel.
- [ ] Put the app behind a reverse proxy (nginx / Caddy / Traefik) for TLS termination.
- [ ] Use `LOG_FORMAT=json` and ship logs to a central aggregator.
- [ ] Monitor the prompt-injection log entries and tune `looks_like_prompt_injection()` patterns.
- [ ] Consider adding a WAF (Cloudflare, AWS WAF) in front of the reverse proxy.

---

## 6. Future Roadmap

| Item                            | Priority | Notes                                                                                       |
| ------------------------------- | -------- | ------------------------------------------------------------------------------------------- |
| Redis-backed rate limiter       | High     | Required for multi-instance / horizontal scaling                                            |
| Per-user authentication         | Medium   | Currently all web users are anonymous; add optional JWT or API-key auth                     |
| Content filtering on LLM output | Medium   | Catch the model generating unsafe content before it reaches the user                        |
| Audit trail / structured log    | Medium   | Structured JSON log entries for every chat turn for compliance                              |
| Encrypted session storage       | Low      | File-based sessions are plaintext; encrypt at rest or use PostgreSQL with column encryption |
| CSP header for widget           | Low      | Widget is injected into third-party pages; a nonce-based CSP would tighten XSS protection   |
| IP allowlists for webhooks      | Low      | Twilio/Telegram/LINE publish their egress IPs; allow only those                             |
