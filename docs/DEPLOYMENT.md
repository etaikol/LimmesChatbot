# Deployment Guide

This guide walks you through every step to get the chatbot running in
production — from renting a server to connecting LINE, embedding a web
widget, and integrating with WordPress. No technical background assumed.

---

## Table of contents

1. [What you need before you start](#1-what-you-need-before-you-start)
2. [Rent and prepare a server](#2-rent-and-prepare-a-server)
3. [Put the bot on the server](#3-put-the-bot-on-the-server)
4. [Create your `.env` file](#4-create-your-env-file)
5. [Build and start the bot](#5-build-and-start-the-bot)
6. [Connect a domain and HTTPS](#6-connect-a-domain-and-https)
7. [Deploy on LINE](#7-deploy-on-line)
8. [Add the chat widget to any website](#8-add-the-chat-widget-to-any-website)
9. [Integrate with WordPress](#9-integrate-with-wordpress)
10. [Keep it safe — anti-abuse settings](#10-keep-it-safe--anti-abuse-settings)
11. [Update the knowledge base](#11-update-the-knowledge-base)
12. [Useful day-to-day commands](#12-useful-day-to-day-commands)

---

## 1. What you need before you start

| What | Where to get it | Cost |
|------|----------------|------|
| OpenAI API key | platform.openai.com → API keys | Pay per use |
| A Linux VPS (server) | DigitalOcean, Hetzner, Linode, Vultr | ~$6–10/month |
| A domain name | Namecheap, GoDaddy, Google Domains | ~$10–15/year |
| Docker installed on the server | Comes free with any Ubuntu 22/24 VPS | Free |

> **Why Docker?** Docker packages the bot and every dependency into one
> sealed box. You run one command to start it, one command to restart it,
> and it works the same on every machine. You never fight with Python
> versions or missing libraries.

---

## 2. Rent and prepare a server

### 2a. Recommended spec

A $6/month DigitalOcean Droplet (1 vCPU, 1 GB RAM, Ubuntu 24.04) is
enough for a single business. Pick a datacenter close to your users.

### 2b. Connect to the server

After buying the VPS you get an IP address (e.g. `167.99.12.34`) and a
root password by email, or you can add your SSH key during creation.

Open a terminal on your computer and type:

```bash
ssh root@167.99.12.34
```

You are now inside the server.

### 2c. Install Docker (one-time, takes ~2 minutes)

Paste these three lines in order:

```bash
curl -fsSL https://get.docker.com | sh
systemctl enable docker
systemctl start docker
```

Verify it worked:

```bash
docker --version
# Docker version 26.x.x ...
```

---

## 3. Put the bot on the server

Still inside the server via SSH:

```bash
# Install git if it isn't already there
apt-get install -y git

# Download the project
git clone https://github.com/YOUR-ORG/limmes-chatbot.git /opt/chatbot
cd /opt/chatbot
```

Replace `YOUR-ORG/limmes-chatbot` with the actual repository URL. If the
repo is private you will need to create a GitHub personal access token
and use it in the URL:
`https://TOKEN@github.com/YOUR-ORG/limmes-chatbot.git`

---

## 4. Create your `.env` file

The `.env` file is where all your secrets and settings live. It never
gets committed to Git.

```bash
cd /opt/chatbot
cp .env.example .env
nano .env          # opens a simple text editor
```

**Minimum required changes** — find and fill in these lines:

```env
# Your OpenAI API key from platform.openai.com
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxx

# Which client config to use (matches config/clients/limmes.yaml)
ACTIVE_CLIENT=limmes

# Your domain, once you have one (Step 6)
API_CORS_ORIGINS=https://www.yourdomain.com
API_STRICT_CORS=true
API_HSTS_ENABLED=true

# Spending limits — START WITH THESE, tune later
DAILY_USD_CAP=3
RATE_LIMIT_IP_PER_MINUTE=20
RATE_LIMIT_SESSION_PER_MINUTE=10
```

Save and exit: press `Ctrl+X`, then `Y`, then `Enter`.

> **Your `.env` contains secrets.** Never share it, never paste it in
> chat, never commit it to Git. The `.gitignore` already excludes it.

---

## 5. Build and start the bot

```bash
cd /opt/chatbot

# Build the Docker image and start the container in the background (-d)
docker compose up -d --build
```

This takes about 2–3 minutes the first time (downloading Python, installing
packages, building the bot image). After that, restarts take a few seconds.

**Check it is running:**

```bash
docker compose ps
# NAME              STATUS    PORTS
# limmes-chatbot    running   0.0.0.0:8000->8000/tcp
```

**Check the bot is healthy:**

```bash
curl http://localhost:8000/health
# {"status":"ok", "channels": {...}}
```

**Watch live logs** (press `Ctrl+C` to stop watching):

```bash
docker compose logs -f chatbot
```

The bot will automatically restart if the server reboots.

---

## 6. Connect a domain and HTTPS

The bot listens on port 8000. You need HTTPS for LINE webhooks, the web
widget on real sites, and for security. The standard way is to put Nginx
in front as a reverse proxy and use Let's Encrypt for a free SSL certificate.

### 6a. Point your domain to the server

Log in to your domain registrar and add an **A record**:

| Type | Name | Value |
|------|------|-------|
| A | `chat` | `167.99.12.34` (your server IP) |

This makes `chat.yourdomain.com` point to your server. DNS changes take
5–30 minutes to spread globally.

### 6b. Install Nginx and Certbot

```bash
apt-get install -y nginx certbot python3-certbot-nginx
```

### 6c. Create an Nginx config for the chatbot

```bash
nano /etc/nginx/sites-available/chatbot
```

Paste this (replace `chat.yourdomain.com` with your actual subdomain):

```nginx
server {
    listen 80;
    server_name chat.yourdomain.com;

    location / {
        proxy_pass         http://127.0.0.1:8000;
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
        proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
        proxy_read_timeout 60s;
    }
}
```

Save (`Ctrl+X`, `Y`, `Enter`), then activate it:

```bash
ln -s /etc/nginx/sites-available/chatbot /etc/nginx/sites-enabled/
nginx -t          # should print "syntax is ok"
systemctl reload nginx
```

### 6d. Get a free HTTPS certificate

```bash
certbot --nginx -d chat.yourdomain.com
# Follow the prompts — enter your email when asked
# Choose option 2 (Redirect HTTP to HTTPS)
```

Certbot will edit the Nginx config automatically and set up auto-renewal.

**Test:** Open `https://chat.yourdomain.com/health` in a browser. You
should see a JSON response with `"status": "ok"`.

---

## 7. Deploy on LINE

LINE uses **webhooks** — when a user sends a message in LINE, LINE calls
your server's URL, your server replies, and LINE shows the reply to the
user. Here is how to set that up.

### 7a. Create a LINE channel

1. Go to **[developers.line.biz](https://developers.line.biz)** and log
   in with your LINE account.
2. Click **Create a new provider** → give it a name (e.g. "Limmes").
3. Click **Create a new channel** → choose **Messaging API**.
4. Fill in the form:
   - Channel name: your business name
   - Category and subcategory: pick what fits
   - Email: your email
5. Click **Create**.

You are now on the channel settings page.

### 7b. Get your credentials

Inside the channel settings:

- Go to the **Basic settings** tab → scroll down to find
  **Channel secret** → click **Issue** → copy the value.
- Go to the **Messaging API** tab → scroll to **Channel access token** →
  click **Issue** → copy the value.

### 7c. Add the credentials to `.env`

SSH back into your server:

```bash
nano /opt/chatbot/.env
```

Find these lines (they start with `#`, which means they are disabled) and
fill them in:

```env
LINE_CHANNEL_SECRET=the-channel-secret-you-copied
LINE_CHANNEL_ACCESS_TOKEN=the-long-access-token-you-copied
```

Save the file, then restart the bot so it picks up the new values:

```bash
cd /opt/chatbot
docker compose restart chatbot
```

Wait 10 seconds and check the health endpoint — `line` should now show
as ready:

```bash
curl https://chat.yourdomain.com/health
# "line": {"ready": true}
```

### 7d. Register the webhook URL with LINE

Back in the LINE Developers console:

1. Go to the **Messaging API** tab.
2. Find **Webhook URL** → click **Edit**.
3. Enter: `https://chat.yourdomain.com/webhook/line`
4. Click **Update**, then **Verify**.

You should see a green "Success" message. If you see an error, double-check
that `https://chat.yourdomain.com/health` works in a browser first.

5. Turn on the **Use webhook** toggle.
6. Under **LINE Official Account features**, turn **Auto-reply messages**
   **off** — otherwise LINE and the bot will both reply to every message.

### 7e. Test it

Scan the QR code shown at the top of the Messaging API tab with your phone.
Send a message. The bot should reply within a few seconds.

---

## 8. Add the chat widget to any website

The bot serves a floating chat bubble that works on any HTML page.
You add one line of code to your site — that's it.

### 8a. The one-line embed code

```html
<script src="https://chat.yourdomain.com/widget.js" async></script>
```

Paste this just before the closing `</body>` tag of any HTML page.
The chat bubble will appear in the bottom-right corner.

### 8b. Allow your website's domain in CORS

The bot will only respond to requests from domains you explicitly allow.
Open `.env` on the server:

```bash
nano /opt/chatbot/.env
```

Find `API_CORS_ORIGINS` and add your website's domain:

```env
API_CORS_ORIGINS=https://www.yourdomain.com
```

If you have multiple sites:

```env
API_CORS_ORIGINS=https://www.yourdomain.com,https://shop.yourdomain.com
```

Then restart:

```bash
cd /opt/chatbot && docker compose restart chatbot
```

### 8c. Test the widget

Open your website in a browser. A chat bubble should appear in the
bottom-right corner. Click it and send a test message.

---

## 9. Integrate with WordPress

The WordPress integration works differently from the widget. Instead of
loading a JavaScript file from your server, WordPress communicates with
the bot from the server-side (PHP) and you have full control over how the
chat appears in your theme.

### 9a. Create a secret API key

This key proves to the bot that requests are coming from your WordPress
site and not from random strangers.

On your local machine or inside the server, generate a random key:

```bash
openssl rand -hex 32
# prints something like: a3f9b2c1d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1
```

Copy that output. Open `.env` on the server:

```bash
nano /opt/chatbot/.env
```

Find the `CHATBOT_API_KEY` line and fill it in:

```env
CHATBOT_API_KEY=a3f9b2c1d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1
```

Also make sure your CORS origin is set to your WordPress domain:

```env
API_CORS_ORIGINS=https://www.yourdomain.com
API_STRICT_CORS=true
```

Restart the bot:

```bash
cd /opt/chatbot && docker compose restart chatbot
```

### 9b. Store the key in WordPress

Log in to your WordPress admin panel. Go to **Appearance → Theme File
Editor** (or use a plugin like **Code Snippets**). Open `wp-config.php`
and add this line near the top (before `/* That's all, stop editing! */`):

```php
define( 'LIMMES_CHATBOT_API_KEY', 'a3f9b2c1d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1' );
define( 'LIMMES_CHATBOT_URL', 'https://chat.yourdomain.com/chat' );
```

> The same key must go in both places — `.env` on the server and
> `wp-config.php` in WordPress.

### 9c. Add the PHP function to your theme

In **Appearance → Theme File Editor**, open your theme's `functions.php`
and add:

```php
/**
 * Send a message to the Limmes chatbot and return the response.
 *
 * @param  string $message    The user's message.
 * @param  string $session_id A unique ID for this visitor's conversation.
 * @return string             The bot's reply, or an error message.
 */
function limmes_chat( string $message, string $session_id ): string {
    $response = wp_remote_post( LIMMES_CHATBOT_URL, [
        'headers' => [
            'Content-Type' => 'application/json',
            'X-Api-Key'    => LIMMES_CHATBOT_API_KEY,
        ],
        'body'    => wp_json_encode( [
            'message'    => sanitize_text_field( $message ),
            'session_id' => 'wp_' . sanitize_key( $session_id ),
        ] ),
        'timeout' => 30,
    ] );

    if ( is_wp_error( $response ) ) {
        return 'Sorry, the assistant is temporarily unavailable.';
    }

    $data = json_decode( wp_remote_retrieve_body( $response ), true );
    return $data['answer'] ?? 'No response received.';
}
```

### 9d. Create a chat page

Create a new WordPress page called "Chat with us" and add this shortcode
handler to `functions.php`:

```php
add_shortcode( 'limmes_chatbox', function () {
    // Unique session per browser tab (stored in a cookie)
    $session_id = isset( $_COOKIE['limmes_sid'] )
        ? sanitize_key( $_COOKIE['limmes_sid'] )
        : wp_generate_uuid4();

    ob_start();
    ?>
    <div id="limmes-chat">
        <div id="limmes-messages" style="height:400px;overflow-y:auto;border:1px solid #ddd;padding:12px;border-radius:8px;"></div>
        <form id="limmes-form" style="display:flex;gap:8px;margin-top:8px;">
            <input id="limmes-input" type="text" placeholder="Type a message…"
                   style="flex:1;padding:8px;border:1px solid #ddd;border-radius:6px;" />
            <button type="submit" style="padding:8px 16px;">Send</button>
        </form>
    </div>
    <script>
    (function(){
        var sid = '<?php echo esc_js( $session_id ); ?>';
        document.cookie = 'limmes_sid=' + sid + ';path=/;max-age=86400;SameSite=Lax';
        var msgs = document.getElementById('limmes-messages');
        var form = document.getElementById('limmes-form');
        var input = document.getElementById('limmes-input');

        function addMsg(text, who) {
            var div = document.createElement('div');
            div.style.cssText = 'margin:6px 0;padding:8px 12px;border-radius:14px;max-width:80%;' +
                (who === 'user'
                    ? 'background:#0088cc;color:#fff;margin-left:auto;'
                    : 'background:#f0f0f0;color:#111;');
            div.textContent = text;
            msgs.appendChild(div);
            msgs.scrollTop = msgs.scrollHeight;
        }

        form.addEventListener('submit', function(e) {
            e.preventDefault();
            var msg = input.value.trim();
            if (!msg) return;
            addMsg(msg, 'user');
            input.value = '';

            fetch(<?php echo wp_json_encode( admin_url('admin-ajax.php') ); ?>, {
                method: 'POST',
                headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                body: 'action=limmes_chat&message=' + encodeURIComponent(msg) + '&sid=' + encodeURIComponent(sid)
            })
            .then(function(r){ return r.json(); })
            .then(function(d){ addMsg(d.answer || 'No response.', 'bot'); })
            .catch(function(){ addMsg('Connection error. Please try again.', 'bot'); });
        });
    })();
    </script>
    <?php
    return ob_get_clean();
} );

// AJAX handler (works for logged-in and guest users)
add_action( 'wp_ajax_limmes_chat',        'limmes_chat_ajax' );
add_action( 'wp_ajax_nopriv_limmes_chat', 'limmes_chat_ajax' );

function limmes_chat_ajax(): void {
    check_ajax_referer_not_required(); // rate-limiting is on the API side
    $message = sanitize_text_field( wp_unslash( $_POST['message'] ?? '' ) );
    $sid     = sanitize_key( $_POST['sid'] ?? wp_generate_uuid4() );
    $answer  = limmes_chat( $message, $sid );
    wp_send_json( [ 'answer' => $answer ] );
}
```

Now go to that WordPress page, add the shortcode `[limmes_chatbox]`, and
publish. The chat box will appear on the page.

> **Option B — use the floating widget instead.** If you prefer the same
> floating bubble as any other website, just add the one-line embed code
> from Step 8 to your WordPress theme's `functions.php`:
>
> ```php
> add_action( 'wp_footer', function () {
>     echo '<script src="https://chat.yourdomain.com/widget.js" async></script>';
> } );
> ```
>
> This is simpler and gives you the same experience as any non-WordPress
> site. Use the full PHP integration only if you want the chat embedded
> directly in a page layout.

---

## 10. Keep it safe — anti-abuse settings

These settings live in `.env` and protect your OpenAI bill from bots and
misbehaving users. Edit them with `nano /opt/chatbot/.env` and then
restart the bot.

### Daily spending cap (most important)

```env
# Stop spending money after $3 per day. Resets at midnight UTC.
DAILY_USD_CAP=3
```

Once the daily limit is reached, the bot politely tells users to come
back tomorrow. Your bill cannot grow beyond this amount per day.

### Rate limiting (how many messages per minute)

```env
# Max messages per IP address per minute (protects from bots)
RATE_LIMIT_IP_PER_MINUTE=20

# Max messages per chat session per minute (protects from one tab spamming)
RATE_LIMIT_SESSION_PER_MINUTE=10
```

### Recommended production settings for a small business

```env
DAILY_USD_CAP=3
DAILY_TOKEN_CAP=1500000
RATE_LIMIT_IP_PER_MINUTE=20
RATE_LIMIT_SESSION_PER_MINUTE=10
API_STRICT_CORS=true
API_HSTS_ENABLED=true
```

### Check current status and spending

Visit `https://chat.yourdomain.com/health` in a browser at any time.
It shows which channels are active, whether the bot is healthy, and the
current day's token usage.

---

## 11. Update the knowledge base

The knowledge base is the folder `data/limmes/` — markdown and text files
the bot reads to answer questions about your business.

### How to update it

1. Edit the files under `data/limmes/` on your computer (products, hours,
   policies, etc.).
2. Push the changes to Git, then on the server:

```bash
cd /opt/chatbot
git pull
docker compose exec chatbot python -m scripts.ingest --client limmes
```

The last command rebuilds the bot's search index from the updated files.
It takes about 30–60 seconds. The bot keeps answering during the rebuild.

> **Auto-detection:** On every startup the bot also checks if the files
> changed since last time and rebuilds automatically — so after `git pull`
> and `docker compose restart`, the index updates without running ingest
> manually.

---

## 12. Useful day-to-day commands

All of these are run on the server inside `/opt/chatbot`:

```bash
# See if the bot is running
docker compose ps

# Watch the live log (Ctrl+C to stop)
docker compose logs -f chatbot

# Restart the bot (e.g. after editing .env)
docker compose restart chatbot

# Stop the bot completely
docker compose down

# Start after stopped
docker compose up -d

# Rebuild from scratch after a code update
git pull
docker compose up -d --build

# Rebuild the knowledge base index
docker compose exec chatbot python -m scripts.ingest --client limmes

# Check health and spending
curl https://chat.yourdomain.com/health
```
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
