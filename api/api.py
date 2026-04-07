"""
Limmes Chatbot - FastAPI Backend
Multi-channel: Web Widget, WhatsApp (Twilio), Telegram
"""

import os
import json
import hashlib
import logging
from datetime import datetime
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv

# Optional dependency: Twilio (for WhatsApp)
try:
    from twilio.request_validator import RequestValidator
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False
    RequestValidator = None

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("limmes")

# ── Config ───────────────────────────────────────────────────────────────────
load_dotenv()

MODEL_NAME        = os.getenv("MODEL_NAME",        "gpt-4o-mini")
EMBEDDING_MODEL   = os.getenv("EMBEDDING_MODEL",   "text-embedding-3-small")
MODEL_TEMPERATURE = float(os.getenv("MODEL_TEMPERATURE", "0.7"))
CHUNK_SIZE        = int(os.getenv("CHUNK_SIZE",    "500"))
CHUNK_OVERLAP     = int(os.getenv("CHUNK_OVERLAP", "50"))
RETRIEVAL_K       = int(os.getenv("RETRIEVAL_K",   "4"))
VECTORSTORE_DIR   = os.getenv("VECTORSTORE_DIR",   ".chroma")
PDF_DIRECTORY     = os.getenv("PDF_DIRECTORY",     "pdfs")
CLIENT_NAME       = os.getenv("CLIENT_NAME",       "Limmes Assistant")
SYSTEM_PROMPT     = os.getenv("SYSTEM_PROMPT", """You are a helpful AI assistant.
Answer questions based on the provided documents.
If you don't have the answer in the documents, say so clearly.
Be concise, friendly, and professional.""")

# Optional integrations
TELEGRAM_TOKEN    = os.getenv("TELEGRAM_TOKEN", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")

# ── In-memory session store  (swap for Redis in production) ──────────────────
# sessions[session_id] = [{"role": "user"|"assistant", "content": str}, ...]
sessions: dict[str, list[dict]] = {}

# ── Global chain / retriever (loaded once at startup) ────────────────────────
qa_chain   = None
retriever  = None


# ═════════════════════════════════════════════════════════════════════════════
# RAG ENGINE
# ═════════════════════════════════════════════════════════════════════════════

def get_file_hash(file_paths: list[Path]) -> str:
    total = sum(p.stat().st_size + int(p.stat().st_mtime) for p in file_paths if p.exists())
    return hashlib.md5(str(total).encode()).hexdigest()


def load_pdfs(directory: str) -> list:
    pdf_dir = Path(directory)
    if not pdf_dir.exists():
        pdf_dir.mkdir(parents=True)
        logger.warning(f"Created empty PDF directory: {directory}")
        return []

    pdf_files = sorted(pdf_dir.glob("*.pdf"))
    if not pdf_files:
        logger.warning(f"No PDFs found in {directory}")
        return []

    all_chunks = []
    splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)

    for pdf_path in pdf_files:
        try:
            loader = PyPDFLoader(str(pdf_path))
            pages  = loader.load()
            for page in pages:
                page.metadata["pdf_filename"] = pdf_path.name
            chunks = splitter.split_documents(pages)
            all_chunks.extend(chunks)
            logger.info(f"Loaded {pdf_path.name}: {len(pages)} pages → {len(chunks)} chunks")
        except Exception as e:
            logger.error(f"Could not load {pdf_path.name}: {e}")

    return all_chunks


def should_rebuild(pdf_paths: list[Path]) -> bool:
    meta_file = Path(VECTORSTORE_DIR) / "metadata.json"
    if not meta_file.exists():
        return True
    try:
        with open(meta_file) as f:
            meta = json.load(f)
        return meta.get("hash") != get_file_hash(pdf_paths)
    except Exception:
        return True


def save_metadata(pdf_paths: list[Path]):
    Path(VECTORSTORE_DIR).mkdir(parents=True, exist_ok=True)
    with open(Path(VECTORSTORE_DIR) / "metadata.json", "w") as f:
        json.dump({
            "hash": get_file_hash(pdf_paths),
            "files": [p.name for p in pdf_paths],
            "created_at": datetime.now().isoformat()
        }, f, indent=2)


def build_vectorstore(chunks, pdf_paths: list[Path]):
    embeddings  = OpenAIEmbeddings(model=EMBEDDING_MODEL)
    vectorstore = Chroma.from_documents(
        chunks,
        embeddings,
        persist_directory=VECTORSTORE_DIR,
        collection_name="documents"
    )
    save_metadata(pdf_paths)
    logger.info(f"Vectorstore built with {len(chunks)} chunks → saved to {VECTORSTORE_DIR}")
    return vectorstore


def load_vectorstore():
    embeddings  = OpenAIEmbeddings(model=EMBEDDING_MODEL)
    vectorstore = Chroma(
        persist_directory=VECTORSTORE_DIR,
        embedding_function=embeddings,
        collection_name="documents"
    )
    count = vectorstore._collection.count()
    if count == 0:
        return None
    logger.info(f"Loaded cached vectorstore ({count} embeddings)")
    return vectorstore


def build_chain(vectorstore):
    llm = ChatOpenAI(model=MODEL_NAME, temperature=MODEL_TEMPERATURE)
    ret = vectorstore.as_retriever(search_kwargs={"k": RETRIEVAL_K})

    prompt = ChatPromptTemplate.from_template(
        "{system_prompt}\n\n"
        "Conversation so far:\n{history}\n\n"
        "Relevant document context:\n{context}\n\n"
        "User question: {question}"
    )

    # Format retrieved docs into plain text
    def format_docs(docs):
        return "\n\n".join(
            f"[{d.metadata.get('pdf_filename','?')} p.{d.metadata.get('page','?')}]\n{d.page_content}"
            for d in docs
        )

    chain = (
        {
            "system_prompt": lambda _: SYSTEM_PROMPT,
            "history":       lambda x: x.get("history", ""),
            "context":       lambda x: format_docs(ret.invoke(x["question"])),
            "question":      lambda x: x["question"],
        }
        | prompt
        | llm
        | StrOutputParser()
    )
    return chain, ret


# ═════════════════════════════════════════════════════════════════════════════
# STARTUP
# ═════════════════════════════════════════════════════════════════════════════

@asynccontextmanager
async def lifespan(app: FastAPI):
    global qa_chain, retriever
    logger.info("🚀 Starting Limmes API …")

    pdf_paths = sorted(Path(PDF_DIRECTORY).glob("*.pdf")) if Path(PDF_DIRECTORY).exists() else []

    vectorstore = None

    # Try loading cached vectorstore first
    if Path(VECTORSTORE_DIR).exists() and not should_rebuild(pdf_paths):
        try:
            vectorstore = load_vectorstore()
        except Exception as e:
            logger.warning(f"Cache load failed: {e}")

    # Build fresh if needed
    if vectorstore is None:
        if not pdf_paths:
            logger.warning("⚠️  No PDFs found — bot will have no document knowledge")
        else:
            chunks = load_pdfs(PDF_DIRECTORY)
            if chunks:
                vectorstore = build_vectorstore(chunks, pdf_paths)

    if vectorstore:
        qa_chain, retriever = build_chain(vectorstore)
        logger.info(f"✅ Chain ready — {CLIENT_NAME}")
    else:
        logger.warning("⚠️  Running without vectorstore — add PDFs to /pdfs and restart")

    # Log available integrations
    integrations = []
    integrations.append("Web Widget ✅")
    integrations.append(f"WhatsApp {'✅' if TWILIO_AVAILABLE else '❌ (install: pip install twilio)'}")
    integrations.append("Telegram ✅")
    logger.info(f"📡 Integrations: {' | '.join(integrations)}")

    yield  # App runs here

    logger.info("👋 Shutting down")


# ═════════════════════════════════════════════════════════════════════════════
# APP
# ═════════════════════════════════════════════════════════════════════════════

app = FastAPI(
    title=f"Limmes Chatbot API — {CLIENT_NAME}",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # Lock down in production
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Helpers ──────────────────────────────────────────────────────────────────

def get_history_str(session_id: str, max_turns: int = 5) -> str:
    msgs = sessions.get(session_id, [])[-max_turns * 2:]
    return "\n".join(
        f"{'User' if m['role']=='user' else 'Assistant'}: {m['content']}"
        for m in msgs
    )


def add_to_session(session_id: str, role: str, content: str):
    if session_id not in sessions:
        sessions[session_id] = []
    sessions[session_id].append({"role": role, "content": content})
    # Cap history at 50 messages per session
    if len(sessions[session_id]) > 50:
        sessions[session_id] = sessions[session_id][-50:]


def ask(question: str, session_id: str) -> str:
    if qa_chain is None:
        return "I'm not ready yet — no documents have been loaded. Please contact support."
    history = get_history_str(session_id)
    try:
        return qa_chain.invoke({"question": question, "history": history})
    except Exception as e:
        logger.error(f"Chain error: {e}")
        raise


# ═════════════════════════════════════════════════════════════════════════════
# ROUTES
# ═════════════════════════════════════════════════════════════════════════════

# ── Health ───────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {
        "status": "ok",
        "client": CLIENT_NAME,
        "model": MODEL_NAME,
        "chain_ready": qa_chain is not None,
        "active_sessions": len(sessions),
    }


# ── Web Widget Chat ───────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"

class ChatResponse(BaseModel):
    reply: str
    session_id: str


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    if not req.message.strip():
        raise HTTPException(400, "Message cannot be empty")

    add_to_session(req.session_id, "user", req.message)

    try:
        reply = ask(req.message, req.session_id)
    except Exception as e:
        raise HTTPException(500, f"Error generating response: {str(e)}")

    add_to_session(req.session_id, "assistant", reply)
    return ChatResponse(reply=reply, session_id=req.session_id)


@app.delete("/chat/{session_id}")
def clear_session(session_id: str):
    sessions.pop(session_id, None)
    return {"cleared": session_id}


# ── WhatsApp (Twilio) ─────────────────────────────────────────────────────────
# Twilio sends POST with form fields: Body, From, To
# Returns TwiML XML
# Security: Validates Twilio signature (set TWILIO_AUTH_TOKEN in .env)

@app.post("/webhook/whatsapp")
async def whatsapp_webhook(request: Request):
    # Check if Twilio is installed
    if not TWILIO_AVAILABLE:
        logger.error("WhatsApp webhook called but twilio is not installed")
        return HTMLResponse(
            content=_twiml("WhatsApp integration not available. Install twilio: pip install twilio"),
            media_type="application/xml"
        )
    
    # Validate Twilio signature for production security
    if TWILIO_AUTH_TOKEN:
        signature = request.headers.get("X-Twilio-Signature", "")
        validator = RequestValidator(TWILIO_AUTH_TOKEN)
        
        # Get raw URL and body for validation
        url = str(request.url)
        form_data = await request.form()
        
        # Construct POST parameters dict for validation
        post_params = {key: form_data.get(key, "") for key in form_data.keys()}
        
        if not validator.validate(url, post_params, signature):
            logger.warning(f"Invalid Twilio signature from {request.client.host if request.client else 'unknown'}")
            raise HTTPException(403, "Unauthorized: Invalid Twilio signature")
    else:
        # Dev mode - no validation (log warning)
        form_data = await request.form()
        logger.debug("WhatsApp webhook: TWILIO_AUTH_TOKEN not set, skipping signature validation")
    
    message    = form_data.get("Body", "").strip()
    from_number = form_data.get("From", "unknown")

    if not message:
        return HTMLResponse(content=_twiml("I didn't receive a message. Please try again."), media_type="application/xml")

    session_id = f"wa_{from_number}"
    add_to_session(session_id, "user", message)

    try:
        reply = ask(message, session_id)
    except Exception as e:
        logger.error(f"WhatsApp error: {e}")
        reply = "Sorry, I ran into an issue. Please try again in a moment."

    add_to_session(session_id, "assistant", reply)
    return HTMLResponse(content=_twiml(reply), media_type="application/xml")


def _twiml(message: str) -> str:
    # Escape XML special characters
    message = message.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>{message}</Message>
</Response>"""


# ── Telegram ──────────────────────────────────────────────────────────────────
# Set webhook via:
# https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://yourdomain.com/webhook/telegram

@app.post("/webhook/telegram")
async def telegram_webhook(request: Request):
    if not TELEGRAM_TOKEN:
        raise HTTPException(503, "Telegram not configured — set TELEGRAM_TOKEN in .env")

    import httpx
    body = await request.json()

    # Extract message
    msg = body.get("message") or body.get("edited_message")
    if not msg:
        return {"ok": True}

    chat_id = msg["chat"]["id"]
    text    = msg.get("text", "").strip()

    if not text or text.startswith("/"):
        if text == "/start":
            reply = f"👋 Hi! I'm {CLIENT_NAME}. Ask me anything!"
        elif text == "/clear":
            sessions.pop(f"tg_{chat_id}", None)
            reply = "✅ Conversation cleared."
        else:
            return {"ok": True}
    else:
        session_id = f"tg_{chat_id}"
        add_to_session(session_id, "user", text)
        try:
            reply = ask(text, session_id)
        except Exception as e:
            logger.error(f"Telegram error: {e}")
            reply = "Sorry, I ran into an issue. Please try again."
        add_to_session(session_id, "assistant", reply)

    # Send reply back to Telegram
    async with httpx.AsyncClient() as client:
        await client.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={"chat_id": chat_id, "text": reply}
        )

    return {"ok": True}


# ── Widget embed script ───────────────────────────────────────────────────────

@app.get("/widget.js", response_class=HTMLResponse)
def widget_js(request: Request):
    base_url = str(request.base_url).rstrip("/")
    js = _widget_script(base_url, CLIENT_NAME)
    return HTMLResponse(content=js, media_type="application/javascript")


def _widget_script(api_url: str, client_name: str) -> str:
    return f"""
(function() {{
  // Inject styles
  const style = document.createElement('style');
  style.textContent = `
    #limmes-btn {{
      position:fixed; bottom:24px; right:24px; z-index:9999;
      width:56px; height:56px; border-radius:50%;
      background:#111; border:none; cursor:pointer;
      box-shadow:0 4px 20px rgba(0,0,0,0.3);
      display:flex; align-items:center; justify-content:center;
      transition:transform .2s;
    }}
    #limmes-btn:hover {{ transform:scale(1.1); }}
    #limmes-btn svg {{ width:26px; height:26px; fill:white; }}
    #limmes-window {{
      position:fixed; bottom:92px; right:24px; z-index:9999;
      width:360px; height:520px; border-radius:16px;
      background:#fff; box-shadow:0 8px 40px rgba(0,0,0,0.18);
      display:none; flex-direction:column; overflow:hidden;
      font-family: system-ui, sans-serif;
    }}
    #limmes-header {{
      padding:14px 18px; background:#111; color:#fff;
      font-weight:600; font-size:15px;
      display:flex; justify-content:space-between; align-items:center;
    }}
    #limmes-messages {{
      flex:1; overflow-y:auto; padding:16px;
      display:flex; flex-direction:column; gap:10px;
    }}
    .limmes-msg {{ max-width:80%; padding:10px 14px; border-radius:12px; font-size:14px; line-height:1.5; }}
    .limmes-msg.user {{ background:#111; color:#fff; align-self:flex-end; border-bottom-right-radius:4px; }}
    .limmes-msg.bot  {{ background:#f0f0f0; color:#111; align-self:flex-start; border-bottom-left-radius:4px; }}
    #limmes-input-row {{
      display:flex; padding:12px; border-top:1px solid #eee; gap:8px;
    }}
    #limmes-input {{
      flex:1; padding:10px 14px; border:1px solid #ddd; border-radius:24px;
      font-size:14px; outline:none;
    }}
    #limmes-send {{
      padding:10px 18px; background:#111; color:#fff;
      border:none; border-radius:24px; cursor:pointer; font-size:14px;
    }}
  `;
  document.head.appendChild(style);

  // Build widget HTML
  const sessionId = 'web_' + Math.random().toString(36).slice(2);

  const btn = document.createElement('button');
  btn.id = 'limmes-btn';
  btn.innerHTML = `<svg viewBox="0 0 24 24"><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z"/></svg>`;

  const win = document.createElement('div');
  win.id = 'limmes-window';
  win.innerHTML = `
    <div id="limmes-header">
      <span>{client_name}</span>
      <span id="limmes-close" style="cursor:pointer;font-size:20px;">×</span>
    </div>
    <div id="limmes-messages">
      <div class="limmes-msg bot">👋 Hi! How can I help you today?</div>
    </div>
    <div id="limmes-input-row">
      <input id="limmes-input" placeholder="Type a message…" />
      <button id="limmes-send">Send</button>
    </div>
  `;

  document.body.appendChild(btn);
  document.body.appendChild(win);

  // Toggle
  btn.addEventListener('click', () => {{
    win.style.display = win.style.display === 'flex' ? 'none' : 'flex';
  }});
  document.getElementById('limmes-close').addEventListener('click', () => {{
    win.style.display = 'none';
  }});

  // Send message
  async function sendMessage() {{
    const input = document.getElementById('limmes-input');
    const text  = input.value.trim();
    if (!text) return;

    appendMsg(text, 'user');
    input.value = '';

    const thinking = appendMsg('…', 'bot');

    try {{
      const res  = await fetch('{api_url}/chat', {{
        method: 'POST',
        headers: {{'Content-Type': 'application/json'}},
        body: JSON.stringify({{ message: text, session_id: sessionId }})
      }});
      const data = await res.json();
      thinking.textContent = data.reply || 'Sorry, no response.';
    }} catch(e) {{
      thinking.textContent = 'Error connecting to assistant. Please try again.';
    }}

    const msgs = document.getElementById('limmes-messages');
    msgs.scrollTop = msgs.scrollHeight;
  }}

  function appendMsg(text, who) {{
    const msgs = document.getElementById('limmes-messages');
    const el   = document.createElement('div');
    el.className = 'limmes-msg ' + who;
    el.textContent = text;
    msgs.appendChild(el);
    msgs.scrollTop = msgs.scrollHeight;
    return el;
  }}

  document.getElementById('limmes-send').addEventListener('click', sendMessage);
  document.getElementById('limmes-input').addEventListener('keydown', e => {{
    if (e.key === 'Enter') sendMessage();
  }});
}})();
""".strip()


# ── Demo page ─────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    base_url = str(request.base_url).rstrip("/")
    return HTMLResponse(_demo_page(base_url, CLIENT_NAME))


def _demo_page(base_url: str, client_name: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{client_name} — Limmes API</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: system-ui, sans-serif; background: #f8f8f8; color: #111; min-height: 100vh; }}
  header {{ background: #111; color: #fff; padding: 24px 32px; }}
  header h1 {{ font-size: 22px; font-weight: 700; }}
  header p {{ font-size: 14px; color: #aaa; margin-top: 4px; }}
  main {{ max-width: 800px; margin: 40px auto; padding: 0 24px; }}
  .card {{ background: #fff; border-radius: 12px; padding: 24px; margin-bottom: 20px; box-shadow: 0 2px 12px rgba(0,0,0,.06); }}
  .card h2 {{ font-size: 16px; font-weight: 700; margin-bottom: 12px; }}
  code {{ background: #f0f0f0; padding: 2px 6px; border-radius: 4px; font-size: 13px; }}
  pre {{ background: #111; color: #7ee787; padding: 16px; border-radius: 8px; overflow-x: auto; font-size: 13px; line-height: 1.6; }}
  .badge {{ display:inline-block; background:#e8f5e9; color:#2e7d32; padding:3px 10px; border-radius:20px; font-size:12px; font-weight:600; }}
  .badge.warn {{ background:#fff3e0; color:#e65100; }}
</style>
</head>
<body>
<header>
  <h1>🤖 {client_name}</h1>
  <p>Limmes RAG Chatbot API — Running</p>
</header>
<main>
  <div class="card">
    <h2>Status</h2>
    <p><span class="badge">✓ API Online</span> &nbsp; Model: <code>{MODEL_NAME}</code></p>
  </div>

  <div class="card">
    <h2>📦 Embed on any website</h2>
    <p style="margin-bottom:12px;font-size:14px;">Paste this single line before <code>&lt;/body&gt;</code>:</p>
    <pre>&lt;script src="{base_url}/widget.js"&gt;&lt;/script&gt;</pre>
  </div>

  <div class="card">
    <h2>🔗 WhatsApp (Twilio) Webhook</h2>
    <pre>POST {base_url}/webhook/whatsapp</pre>
    <p style="margin-top:10px;font-size:13px;color:#666;">Set this URL in your Twilio WhatsApp sandbox settings.</p>
  </div>

  <div class="card">
    <h2>💬 Telegram Webhook</h2>
    <pre>POST {base_url}/webhook/telegram</pre>
    <p style="margin-top:10px;font-size:13px;color:#666;">Register via: <code>https://api.telegram.org/bot&lt;TOKEN&gt;/setWebhook?url={base_url}/webhook/telegram</code></p>
  </div>

  <div class="card">
    <h2>🧪 REST API</h2>
    <pre>POST {base_url}/chat
Content-Type: application/json

{{
  "message": "What are your opening hours?",
  "session_id": "user-abc123"
}}</pre>
  </div>

  <div class="card">
    <h2>📖 Docs</h2>
    <p style="font-size:14px;">
      Interactive API docs: <a href="{base_url}/docs">{base_url}/docs</a><br>
      Health check: <a href="{base_url}/health">{base_url}/health</a>
    </p>
  </div>
</main>
<script src="{base_url}/widget.js"></script>
</body>
</html>"""
