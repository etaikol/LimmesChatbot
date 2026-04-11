# Deployment Guide

This guide walks you through every step of getting the chatbot live —
from your first local test to a public deployment that real customers use.
No guessing, no "figure it out." Just follow the steps.

---

## Table of Contents

1. [Before You Start (Prerequisites)](#1-before-you-start)
2. [Your First Local Test](#2-your-first-local-test)
3. [Deploy the Web Chat Widget](#3-deploy-the-web-chat-widget)
   - [On your own website (plain HTML)](#on-your-own-website-plain-html)
   - [On WordPress](#on-wordpress)
   - [On Wix, Squarespace, or other builders](#on-wix-squarespace-or-other-builders)
4. [Deploy LINE](#4-deploy-line)
5. [Deploy Telegram](#5-deploy-telegram)
6. [Deploy WhatsApp](#6-deploy-whatsapp)
7. [Put It on a Real Server (Production)](#7-put-it-on-a-real-server)
   - [Option A — Docker (recommended)](#option-a--docker-recommended)
   - [Option B — Manual setup on a VPS](#option-b--manual-setup-on-a-vps)
8. [Make It Secure Before Going Live](#8-make-it-secure-before-going-live)
9. [The Admin Dashboard](#9-the-admin-dashboard)
10. [Updating Your Knowledge Base](#10-updating-your-knowledge-base)
11. [Troubleshooting](#11-troubleshooting)

---

## 1. Before You Start

You need three things on your computer:

1. **Python 3.10 or newer** — Download from [python.org](https://www.python.org/downloads/).
   During installation on Windows, check **"Add Python to PATH"**.
2. **An OpenAI API key** — Go to [platform.openai.com/api-keys](https://platform.openai.com/api-keys),
   create a key, and make sure you have billing enabled (even $5 of credit is enough to start).
3. **Your knowledge base files** — The `.md`, `.txt`, or `.pdf` files that describe your
   business, products, policies, etc. They go in the `data/<your-client>/` folder.

### Create your `.env` file

In the project root (the folder with `run.bat`), create a file called `.env`.
This is where all your secrets and settings live. Start with just this:

```env
OPENAI_API_KEY=sk-your-key-here
ACTIVE_CLIENT=limmes
```

> **What is `ACTIVE_CLIENT`?** It tells the chatbot which business configuration
> to load. It matches a file in `config/clients/` — for example, `limmes` loads
> `config/clients/limmes.yaml`. If you're building for a different business,
> create a new YAML file there and point to it.

---

## 2. Your First Local Test

Let's make sure everything works on your own machine before deploying anywhere.

### Windows

Double-click `run.bat` or open a terminal in the project folder and type:

```
run.bat
```

The first time takes a minute — it creates a virtual environment, installs
all the Python packages, builds the knowledge base index, and launches a
chat in the terminal. You'll see something like:

```
[setup] Creating virtual environment .venv ...
[setup] Installing base requirements (first run only) ...
[setup] Building vector store for client 'limmes' ...
[run] Starting CLI chat — type 'quit' to exit

You: hello
Bot: Welcome to Limmes Studio! How can I help you today?
```

Type `quit` to exit. If you see the bot reply, everything is working.

### Mac / Linux

Same idea, just use `./run.sh` instead:

```bash
chmod +x run.sh    # only the first time
./run.sh
```

### Start the web server (HTTP mode)

This is what you'll use when real people need to access the chatbot:

```
run.bat serve
```

Now open your browser and go to **http://localhost:8000** — you'll see a
demo page with the chat widget in the bottom-right corner. Click the bubble,
send a message, and confirm the bot replies.

**That's it.** Your chatbot is running locally. Everything below is about
making it available to the world.

---

## 3. Deploy the Web Chat Widget

The web widget is a small chat bubble that floats in the bottom-right corner
of any website. It works by loading one JavaScript file from your chatbot
server. No npm, no build step, no React — just one line of HTML.

### Requirement

Your chatbot server needs to be running and reachable from the internet.
If you haven't done that yet, jump to [Section 7](#7-put-it-on-a-real-server)
first, then come back here.

Let's say your server is running at `https://chat.yourdomain.com`.

---

### On your own website (plain HTML)

Add this line inside the `<body>` tag of every page where you want the chat
widget to appear — usually right before `</body>`:

```html
<script src="https://chat.yourdomain.com/widget.js" async></script>
```

That's literally it. One line. The script creates the floating bubble, the
chat window, the language picker — everything. Here's what a minimal page
looks like:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <title>My Store</title>
</head>
<body>
    <h1>Welcome to my store!</h1>

    <!-- Chat widget — just this one line -->
    <script src="https://chat.yourdomain.com/widget.js" async></script>
</body>
</html>
```

---

### On WordPress

There are two ways to do this. Pick whichever feels easier:

#### Method 1: Using a plugin (easiest)

1. In your WordPress admin, go to **Plugins → Add New**.
2. Search for **"Insert Headers and Footers"** (by WPCode) and install it.
3. Go to **Code Snippets → Header & Footer** (or **WPCode → Header & Footer**).
4. In the **Footer** section, paste:
   ```html
   <script src="https://chat.yourdomain.com/widget.js" async></script>
   ```
5. Click **Save Changes**.

The chat bubble will now appear on every page of your WordPress site.

#### Method 2: Edit your theme directly

1. In your WordPress admin, go to **Appearance → Theme File Editor**.
2. On the right side, find and click **footer.php** (or **Theme Footer**).
3. Find the line that says `</body>` and paste this **right above it**:
   ```html
   <script src="https://chat.yourdomain.com/widget.js" async></script>
   ```
4. Click **Update File**.

> **Heads up:** If you update your WordPress theme, changes to `footer.php`
> may be erased. That's why the plugin method is usually better.

#### WordPress CORS setting

Your chatbot server needs to know that your WordPress site is allowed to
talk to it. In your chatbot's `.env` file, add:

```env
API_CORS_ORIGINS=https://yourwordpresssite.com
API_STRICT_CORS=true
```

If you have multiple sites (e.g., the main site + a staging site), separate
them with commas:

```env
API_CORS_ORIGINS=https://yourwordpresssite.com,https://staging.yourwordpresssite.com
```

Then restart the chatbot server so the change takes effect.

---

### On Wix, Squarespace, or other builders

Most website builders have a way to inject custom code:

- **Wix**: Settings → Custom Code → Add at the end of `<body>`.
- **Squarespace**: Settings → Advanced → Code Injection → Footer.
- **Shopify**: Online Store → Themes → Edit Code → `theme.liquid` before `</body>`.
- **Webflow**: Project Settings → Custom Code → Footer Code.

In every case, paste the same one-liner:

```html
<script src="https://chat.yourdomain.com/widget.js" async></script>
```

---

## 4. Deploy LINE

This is a complete walkthrough — from zero to a working LINE chatbot that
your customers can message.

### Step 1: Create a LINE channel

1. Go to [LINE Developers Console](https://developers.line.biz/console/).
2. Log in with your LINE account (or create one).
3. Click **Create a new provider** (or use an existing one) — the provider
   is just a label for your company/project.
4. Click **Create a Messaging API channel**.
5. Fill in:
   - **Channel name**: Your business name (e.g., "Limmes Studio").
   - **Channel description**: Short description of what the bot does.
   - **Category** and **Subcategory**: Pick whatever fits your business.
   - **Email**: Your contact email.
6. Click **Create**.

### Step 2: Get your secrets

You need two values from the LINE console. Both are on your channel's page:

1. **Channel Secret**: Go to the **Basic settings** tab → copy the
   **Channel secret**. This is used to verify that incoming messages
   really come from LINE (not from an attacker).

2. **Channel Access Token**: Go to the **Messaging API** tab → scroll
   down to **Channel access token** → click **Issue**. Copy the long
   token that appears. This is what allows your server to *send*
   messages back to users through LINE.

### Step 3: Add the secrets to your `.env`

Open your `.env` file and add:

```env
LINE_CHANNEL_SECRET=your-channel-secret-here
LINE_CHANNEL_ACCESS_TOKEN=your-channel-access-token-here
```

Restart the chatbot server after saving.

### Step 4: Set the webhook URL

This tells LINE where to send messages when someone talks to your bot.

1. Make sure your server is running and accessible from the internet
   (see [Section 7](#7-put-it-on-a-real-server)). You need a public
   URL with HTTPS — for example, `https://chat.yourdomain.com`.
2. In the LINE Developers Console, go to your channel's **Messaging API** tab.
3. Under **Webhook settings**:
   - Set **Webhook URL** to: `https://chat.yourdomain.com/webhook/line`
   - Toggle **Use webhook** to **ON**.
4. Click **Verify** — it should say "Success". If it fails, check that
   your server is running and the URL is correct.

### Step 5: Turn off auto-reply

By default, LINE has its own built-in auto-reply that will interfere with
your chatbot. Turn it off:

1. In the **Messaging API** tab, find **LINE Official Account features**.
2. Click **Edit** (it opens the LINE Official Account Manager).
3. Set **Auto-reply messages** to **Disabled**.
4. Set **Greeting messages** to **Disabled** (your chatbot handles greetings).

### Step 6: Test it

1. In the **Messaging API** tab, you'll see a **QR code**.
2. Open LINE on your phone, go to **Add Friends → QR Code**, and scan it.
3. Send a message to your bot. You should get a reply within a few seconds.

### Step 7 (optional): Set up a Rich Menu

A rich menu is the big tappable menu that appears at the bottom of the
LINE chat. You can create one through the Admin Dashboard (see
[Section 9](#9-the-admin-dashboard)) or from the LINE Official Account
Manager.

**That's it — your LINE bot is live!**

---

## 5. Deploy Telegram

### Step 1: Create a bot with BotFather

1. Open Telegram and search for **@BotFather** (the official bot for
   creating bots).
2. Send `/newbot`.
3. Follow the prompts — give it a name and a username (must end in `bot`).
4. BotFather will give you a **bot token** like
   `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`. Copy it.

### Step 2: Add the token to your `.env`

```env
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
```

For extra security, also set a webhook secret (any random string you make up):

```env
TELEGRAM_WEBHOOK_SECRET=my-random-secret-string-here
```

Restart the chatbot server.

### Step 3: Register the webhook

You need to tell Telegram where your server is. Run this command once
(replace the values with your own):

**Windows (PowerShell):**
```powershell
Invoke-RestMethod -Method Post -Uri "https://api.telegram.org/bot<YOUR_TOKEN>/setWebhook" -Body @{
    url = "https://chat.yourdomain.com/webhook/telegram"
    secret_token = "my-random-secret-string-here"
}
```

**Mac / Linux / Git Bash:**
```bash
curl -F "url=https://chat.yourdomain.com/webhook/telegram" \
     -F "secret_token=my-random-secret-string-here" \
     https://api.telegram.org/bot<YOUR_TOKEN>/setWebhook
```

You should see `"ok": true` in the response.

### Step 4: Test it

Open Telegram, find your bot by its username, and send a message. Done!

---

## 6. Deploy WhatsApp

WhatsApp uses Twilio as a middleman. This is more involved than LINE or
Telegram because Twilio is a paid service, but it's very reliable.

### Step 1: Set up Twilio

1. Create a Twilio account at [twilio.com](https://www.twilio.com/).
2. In the Twilio Console, go to **Messaging → Try it out → Send a WhatsApp message**.
3. Follow the sandbox setup instructions to connect your phone.
4. Note your **Account SID** and **Auth Token** from the console dashboard.
5. Note the **WhatsApp sandbox number** (something like `+14155238886`).

### Step 2: Add to your `.env`

```env
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your-auth-token-here
TWILIO_WHATSAPP_NUMBER=+14155238886
```

Restart the chatbot server.

### Step 3: Set the webhook URL

1. In the Twilio Console, go to **Messaging → Settings → WhatsApp Sandbox Settings**.
2. Under **"When a message comes in"**, set:
   `https://chat.yourdomain.com/webhook/whatsapp`
3. Set the method to **POST**.
4. Save.

### Step 4: Test it

Send a WhatsApp message to the sandbox number from your phone. Done!

> **Going to production?** Apply for a Twilio WhatsApp Business number
> so customers can message your actual business number instead of a sandbox.

---

## 7. Put It on a Real Server

So far everything has been running on `localhost`. For people to actually
use your chatbot, it needs to be on a server that's always on and accessible
from the internet.

You have two options:

---

### Option A — Docker (recommended)

This is the easiest way. Docker packages everything into a container so you
don't have to worry about Python versions, dependencies, or system configuration.

**What you need:** A Linux server (Ubuntu, Debian, etc.) with Docker installed.
Good options: DigitalOcean ($6/mo), Hetzner ($4/mo), AWS Lightsail ($5/mo),
or any VPS provider.

#### Step 1: Install Docker on your server

SSH into your server and run:

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
# log out and back in, then verify:
docker --version
```

#### Step 2: Upload your project

Upload the entire project folder to your server. You can use `scp`, `rsync`,
or just `git clone` if you have it in a repository:

```bash
# From your local machine:
scp -r ./LimmesChatbot user@your-server-ip:/home/user/chatbot

# Or if it's in git:
ssh user@your-server-ip
git clone https://github.com/your-repo/LimmesChatbot.git chatbot
```

#### Step 3: Create the `.env` on the server

```bash
cd /home/user/chatbot
nano .env
```

Paste all your settings (see [Section 8](#8-make-it-secure-before-going-live)
for the recommended production settings). Save with `Ctrl+X → Y → Enter`.

#### Step 4: Start it

```bash
docker compose up -d --build
```

That's it. The `-d` flag runs it in the background. It will:
- Build the Docker image (first time takes a few minutes).
- Install all dependencies inside the container.
- Build the vector store from your knowledge base files.
- Start the web server on port 8000.

Check that it's running:

```bash
docker compose logs -f chatbot
```

You should see the server start up and say it's listening. Press `Ctrl+C`
to stop watching logs (the server keeps running).

Test it:

```bash
curl http://localhost:8000/health
```

You should see a JSON response with `"status": "ok"`.

#### Step 5: Set up HTTPS with a reverse proxy

Your chatbot needs HTTPS (the padlock in the browser) because:
- LINE, Telegram, and Twilio all **require** HTTPS for webhooks.
- Browsers block loading widget.js from HTTP on HTTPS sites.
- It's just good practice.

The easiest way is **Caddy** — it handles HTTPS certificates automatically:

```bash
# Install Caddy
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt update
sudo apt install caddy
```

Create `/etc/caddy/Caddyfile`:

```
chat.yourdomain.com {
    reverse_proxy localhost:8000
}
```

Point your domain's DNS to your server's IP address (an A record), then:

```bash
sudo systemctl restart caddy
```

Caddy will automatically get a free HTTPS certificate from Let's Encrypt.
Within a minute, `https://chat.yourdomain.com` will be live.

**Alternative:** If you prefer **nginx**, here's a basic config:

```nginx
server {
    listen 80;
    server_name chat.yourdomain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $remote_addr;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Then use **certbot** to add HTTPS:

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d chat.yourdomain.com
```

#### Useful Docker commands

```bash
docker compose logs -f chatbot    # watch live logs
docker compose restart chatbot    # restart after .env change
docker compose down               # stop everything
docker compose up -d --build      # rebuild after code changes
```

If you update the knowledge base files in `data/`, re-index:

```bash
docker compose exec chatbot python -m scripts.ingest
```

---

### Option B — Manual setup on a VPS

If you don't want Docker, you can run Python directly.

#### Step 1: Install Python on your server

```bash
sudo apt update
sudo apt install python3.12 python3.12-venv python3-pip -y
```

#### Step 2: Upload and set up

```bash
cd /home/user/chatbot
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements/api.txt
```

#### Step 3: Create `.env` and build the index

```bash
nano .env      # paste your settings
python -m scripts.ingest --client limmes
```

#### Step 4: Run with systemd (so it stays running)

Create `/etc/systemd/system/chatbot.service`:

```ini
[Unit]
Description=Limmes Chatbot
After=network.target

[Service]
User=user
WorkingDirectory=/home/user/chatbot
Environment="PATH=/home/user/chatbot/.venv/bin"
ExecStart=/home/user/chatbot/.venv/bin/python -m scripts.serve
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Then:

```bash
sudo systemctl daemon-reload
sudo systemctl enable chatbot
sudo systemctl start chatbot

# Check it's running:
sudo systemctl status chatbot
```

Then add Caddy or nginx for HTTPS (same as in Option A, Step 5).

---

## 8. Make It Secure Before Going Live

Before real customers start using the chatbot, add these settings to your
`.env` file. Each one is explained below.

### Recommended production `.env`

```env
# ── Your secrets ──────────────────────────────────────
OPENAI_API_KEY=sk-your-key-here
ACTIVE_CLIENT=limmes

# ── Protect your OpenAI bill ──────────────────────────
# Stop the bot after spending ~$2/day (resets at midnight UTC).
# This prevents runaway costs if someone spams the bot.
DAILY_USD_CAP=2
DAILY_TOKEN_CAP=500000

# ── Rate limiting ─────────────────────────────────────
# Max 20 messages per minute from the same IP address.
# Max 8 per minute from the same chat session.
# This stops automated abuse while letting normal users chat freely.
RATE_LIMIT_ENABLED=true
RATE_LIMIT_IP_PER_MINUTE=20
RATE_LIMIT_IP_BURST=6
RATE_LIMIT_SESSION_PER_MINUTE=8
RATE_LIMIT_SESSION_BURST=3

# ── Spam detection ────────────────────────────────────
# Blocks gibberish/key-mashing before it reaches the AI.
SPAM_DETECTION_ENABLED=true

# ── CORS — tell the server which websites can use the widget ──
# Replace with your actual website URL. This prevents other sites
# from embedding your widget and using your OpenAI credits.
API_CORS_ORIGINS=https://yourwebsite.com
API_STRICT_CORS=true

# ── HTTPS ─────────────────────────────────────────────
# Only enable this AFTER you have Caddy/nginx handling HTTPS.
API_HSTS_ENABLED=true

# ── Logging ───────────────────────────────────────────
DEBUG=false
LOG_LEVEL=INFO
LOG_FORMAT=json

# ── Admin dashboard ───────────────────────────────────
# Set a strong random key. You'll use this to log into the
# dashboard at https://chat.yourdomain.com/admin
ADMIN_API_KEY=pick-a-strong-random-key-here

# ── Channel secrets (add whichever channels you use) ──
# LINE_CHANNEL_SECRET=...
# LINE_CHANNEL_ACCESS_TOKEN=...
# TELEGRAM_BOT_TOKEN=...
# TELEGRAM_WEBHOOK_SECRET=...
# TWILIO_ACCOUNT_SID=...
# TWILIO_AUTH_TOKEN=...
# TWILIO_WHATSAPP_NUMBER=...
```

### What each security setting does

| Setting | What it does | Why you need it |
| ------- | ------------ | --------------- |
| `DAILY_USD_CAP` | Stops all chat after spending this much per day | Prevents a $200 surprise on your OpenAI bill |
| `RATE_LIMIT_*` | Limits how fast someone can send messages | Stops bots and spam scripts |
| `SPAM_DETECTION_ENABLED` | Blocks gibberish like "asdfasdf" or "aaaaaaa" | Saves tokens — meaningless messages never reach OpenAI |
| `API_CORS_ORIGINS` | Only allows your website to load the widget | Prevents strangers from embedding your widget on their site |
| `API_STRICT_CORS` | Refuses to start if CORS is set to "allow all" | Safety net — makes sure you didn't forget to set CORS |
| `API_HSTS_ENABLED` | Forces browsers to use HTTPS | Prevents downgrade attacks |
| `ADMIN_API_KEY` | Password for the admin dashboard | Without this, the dashboard is disabled |

---

## 9. The Admin Dashboard

The admin dashboard lets you monitor and configure the chatbot from your
browser — no terminal or code needed.

### How to access it

1. Make sure `ADMIN_API_KEY` is set in your `.env` (any random string).
2. Go to `https://chat.yourdomain.com/admin` (or `http://localhost:8000/admin`
   for local testing).
3. Enter your admin API key when prompted.

### What you can do

- **Overview**: See server health, active channels, request counts.
- **Sessions**: Browse all conversations, read chat history, delete sessions.
- **Budget**: See today's token/dollar usage and remaining budget.
- **Configuration**: View and edit `.env` settings and client YAML files.
- **LINE**: Create and manage Rich Menus, preview Flex Messages.
- **Data Files**: Browse, edit, create, and delete knowledge base files
  (the files in `data/`).
- **Logs**: View recent server logs.

---

## 10. Updating Your Knowledge Base

When your business information changes (new products, new hours, new policies),
update the knowledge base:

1. Edit or add files in the `data/<your-client>/` folder. These can be
   `.md` (Markdown), `.txt`, or `.pdf` files. Organize them however makes
   sense — subdirectories are fine.

2. Rebuild the index:

   **Locally:**
   ```
   run.bat ingest
   ```

   **On a Docker server:**
   ```bash
   docker compose exec chatbot python -m scripts.ingest
   ```

   **Through the admin dashboard:**
   Go to the **Data Files** page, edit files right in the browser.
   After saving, rebuild the index from the **Overview** page.

The chatbot will immediately start using the updated information.

---

## 11. Troubleshooting

### The bot doesn't reply

- Check the server is running: visit `https://chat.yourdomain.com/health`
  in your browser. You should see JSON with `"status": "ok"`.
- Check `chain_ready` in the health response — if it's `false`, the
  knowledge base index is missing. Run `ingest` (see section 10).
- Check your `OPENAI_API_KEY` is valid and has billing enabled.
- Check the logs: `docker compose logs -f chatbot` or the admin dashboard.

### The widget doesn't show up on my website

- Open your browser's Developer Tools (F12 → Console tab). Look for errors
  loading `widget.js`.
- If you see a CORS error, make sure `API_CORS_ORIGINS` in your `.env`
  includes your website's URL.
- Make sure the script tag URL is correct and uses HTTPS.

### LINE webhook says "failed" when I click Verify

- Make sure your server is running and reachable from the internet.
- The webhook URL must be HTTPS: `https://chat.yourdomain.com/webhook/line`
- Make sure `LINE_CHANNEL_SECRET` and `LINE_CHANNEL_ACCESS_TOKEN` are
  in your `.env` and the server has been restarted.
- Check the server logs for errors.

### Telegram bot doesn't reply

- Re-register the webhook (Step 3 in the Telegram section). The URL must
  be HTTPS.
- Make sure `TELEGRAM_BOT_TOKEN` is correct.
- If you set `TELEGRAM_WEBHOOK_SECRET`, make sure you used the same value
  when calling `setWebhook`.

### WhatsApp messages aren't going through

- Make sure you joined the Twilio sandbox (sent the join code from your phone).
- Check `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, and `TWILIO_WHATSAPP_NUMBER`
  are all correct.
- The webhook URL in Twilio must be HTTPS.

### I'm getting a 429 (Too Many Requests) error

This means rate limiting kicked in. If it's happening during normal use,
increase the limits in `.env`:

```env
RATE_LIMIT_IP_PER_MINUTE=30
RATE_LIMIT_SESSION_PER_MINUTE=12
```

### I'm getting a 402 (Payment Required) error

This means the daily budget was reached. The budget resets at midnight UTC.
To raise it, increase in `.env`:

```env
DAILY_USD_CAP=5
DAILY_TOKEN_CAP=1000000
```

### Hebrew/Arabic shows as `??` in the terminal

This is a Windows terminal encoding issue — it doesn't affect the web widget
or any messaging channel. Fix it with:

```
set PYTHONIOENCODING=utf-8
```

Or better, use **Windows Terminal** (from the Microsoft Store) instead of
the old `cmd.exe`.

### Something else is broken

1. Add `--debug` to any command to see detailed logs:
   ```
   run.bat serve --debug
   ```
2. Check the health endpoint: `https://chat.yourdomain.com/health` — it
   shows the status of every subsystem (channels, budget, chain).
3. Check the admin dashboard logs page.
4. Look at `docker compose logs chatbot` if using Docker.

---

## Quick Reference

For when you already know what you're doing and just need the commands.

| Task | Command |
| ---- | ------- |
| Start CLI chat | `run.bat` or `run.bat chat` |
| Start web server | `run.bat serve` |
| Rebuild knowledge base | `run.bat ingest` |
| Scrape a website | `run.bat scrape` |
| Start with Docker | `docker compose up -d --build` |
| View Docker logs | `docker compose logs -f chatbot` |
| Rebuild index in Docker | `docker compose exec chatbot python -m scripts.ingest` |
| Restart after `.env` change | `docker compose restart chatbot` |
| Check server health | `curl https://chat.yourdomain.com/health` |

### All endpoints

| Method | Path | What it does |
| ------ | ---- | ------------ |
| GET | `/` | Demo page with the chat widget |
| GET | `/health` | Server health check |
| GET | `/widget.js` | The embeddable chat widget script |
| POST | `/chat` | Send a message, get a reply |
| DELETE | `/chat/{session_id}` | Reset a conversation |
| POST | `/webhook/whatsapp` | WhatsApp incoming messages |
| POST | `/webhook/telegram` | Telegram incoming messages |
| POST | `/webhook/line` | LINE incoming messages |
| GET | `/admin` | Admin dashboard |
| GET | `/docs` | API documentation (Swagger) |
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
