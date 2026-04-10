"""
Embeddable web chat widget.

Drop this one-liner into any HTML page (the API host needs CORS allowed):

    <script src="https://your-api/widget.js" async></script>

What it ships
-------------
- A modern floating chat bubble (system fonts, glassmorphism header,
  rounded message bubbles, smooth open/close, mobile-first sizing).
- A **language picker** built from the client's ``languages_offered``
  list (or just ``language_primary`` when none is configured). Picking
  a language flips the UI strings *and* sends ``language`` on every
  ``/chat`` request so the LLM answers in the chosen language.
- Automatic RTL layout for Hebrew/Arabic/Farsi/Urdu.
- Per-tab session id, persisted to ``localStorage`` so refresh keeps
  the conversation.
- Accessible: button has ``aria-label``, dialog has ``role="dialog"``,
  Esc closes, focus returns to the launcher.

The CSS is intentionally inlined into the JS so visitors only need one
script tag — no extra requests, no font downloads.
"""

from __future__ import annotations

import json

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, Response

from chatbot.core.engine import Chatbot
from chatbot.i18n import SUPPORTED_LANGUAGES, get_language, get_messages

router = APIRouter(tags=["widget"])


@router.get("/widget.js")
def widget_js(request: Request) -> Response:
    bot: Chatbot = request.app.state.bot
    base_url = str(request.base_url).rstrip("/")

    primary = bot.profile.client.language_primary or "en"
    offered_codes = bot.profile.client.languages_offered or [primary]

    # Resolve to full LanguageInfo objects, dropping unknowns + dedup.
    seen: set[str] = set()
    offered = []
    for code in offered_codes:
        info = get_language(code)
        if info.code in seen:
            continue
        seen.add(info.code)
        offered.append(info)
    if not offered:
        offered = [get_language(primary)]

    # Build per-language string bundles for the JS payload.
    bundles = {info.code: get_messages(info.code) for info in offered}

    # Per-language greeting: primary lang gets the rich business greeting;
    # other langs get their own translated welcome from the i18n bundle.
    primary_code = get_language(primary).code
    business_greeting = bot.greet()
    greetings = {
        info.code: (
            business_greeting
            if info.code == primary_code
            else bundles[info.code].get("welcome", business_greeting)
        )
        for info in offered
    }

    js = build_widget_js(
        api_url=base_url,
        client_name=bot.profile.client.name,
        primary_lang=primary_code,
        languages=[
            {
                "code": l.code,
                "name": l.name,
                "native": l.native_name,
                "rtl": l.rtl,
            }
            for l in offered
        ],
        bundles=bundles,
        greetings=greetings,
    )
    return Response(content=js, media_type="application/javascript")


def build_widget_js(
    *,
    api_url: str,
    client_name: str,
    primary_lang: str,
    languages: list[dict],
    bundles: dict[str, dict[str, str]],
    greetings: dict[str, str],
) -> str:
    """Return the widget JS as a string. The data is JSON-encoded once
    so we can interpolate it into the JS body without escaping headaches."""
    config = {
        "apiUrl": api_url,
        "clientName": client_name,
        "primaryLang": primary_lang,
        "languages": languages,
        "bundles": bundles,
        "greetings": greetings,
    }
    return f"(function(){{var CONFIG={json.dumps(config, ensure_ascii=False)};\n{_WIDGET_BODY}\n}})();"


# ── Widget body ────────────────────────────────────────────────────────────
#
# Modern, framework-free, ~6 KB minified. Uses CSS variables so the host
# page can re-skin it from the outside via :root if it wants.

_WIDGET_BODY = r"""
var STORAGE_SID='cb_sid', STORAGE_LANG='cb_lang';
var sid = localStorage.getItem(STORAGE_SID);
if(!sid){ var a=new Uint8Array(16);crypto.getRandomValues(a);sid='web_'+Array.from(a,function(b){return b.toString(16).padStart(2,'0')}).join(''); localStorage.setItem(STORAGE_SID, sid); }

var savedLang = localStorage.getItem(STORAGE_LANG);
var current = CONFIG.languages.find(function(l){return l.code===savedLang;}) || CONFIG.languages.find(function(l){return l.code===CONFIG.primaryLang;}) || CONFIG.languages[0];

function bundle(){ return CONFIG.bundles[current.code] || CONFIG.bundles[CONFIG.primaryLang] || {}; }
function dir(){ return current.rtl ? 'rtl' : 'ltr'; }

var css = '\
:root{--cb-bg:#ffffff;--cb-fg:#0f172a;--cb-muted:#64748b;--cb-accent:#0ea5e9;--cb-accent-fg:#ffffff;--cb-bubble-u:#0f172a;--cb-bubble-b:#f1f5f9;--cb-border:rgba(15,23,42,.08);--cb-shadow:0 30px 60px -20px rgba(15,23,42,.25);}\
.cb-launcher{position:fixed;bottom:24px;inset-inline-end:24px;z-index:2147483646;width:60px;height:60px;border-radius:50%;background:var(--cb-accent);color:var(--cb-accent-fg);border:none;cursor:pointer;box-shadow:0 12px 30px -8px rgba(14,165,233,.55);display:flex;align-items:center;justify-content:center;transition:transform .15s ease, box-shadow .2s ease;font:600 24px system-ui;}\
.cb-launcher:hover{transform:translateY(-2px) scale(1.04);}\
.cb-launcher:focus-visible{outline:3px solid #fff;outline-offset:3px;}\
.cb-panel{position:fixed;bottom:96px;inset-inline-end:24px;z-index:2147483647;width:380px;max-width:calc(100vw - 24px);height:600px;max-height:calc(100vh - 120px);background:var(--cb-bg);color:var(--cb-fg);border-radius:20px;box-shadow:var(--cb-shadow);display:none;flex-direction:column;overflow:hidden;font-family:system-ui,-apple-system,"Segoe UI",Roboto,"Helvetica Neue",sans-serif;border:1px solid var(--cb-border);transform-origin:bottom right;animation:cb-pop .18s ease-out;}\
.cb-panel[data-open="1"]{display:flex;}\
@keyframes cb-pop{from{opacity:0;transform:translateY(8px) scale(.97);}to{opacity:1;transform:none;}}\
.cb-head{padding:14px 18px;background:linear-gradient(135deg,#0f172a,#1e293b);color:#fff;display:flex;align-items:center;gap:12px;}\
.cb-title{flex:1;min-width:0;display:flex;flex-direction:column;line-height:1.2;}\
.cb-title b{font-size:15px;font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}\
.cb-title small{font-size:11px;opacity:.7;letter-spacing:.02em;}\
.cb-status{display:inline-flex;align-items:center;gap:6px;font-size:11px;opacity:.85;}\
.cb-dot{width:7px;height:7px;border-radius:50%;background:#22c55e;box-shadow:0 0 0 0 rgba(34,197,94,.7);animation:cb-pulse 2s infinite;}\
@keyframes cb-pulse{0%{box-shadow:0 0 0 0 rgba(34,197,94,.6);}70%{box-shadow:0 0 0 8px rgba(34,197,94,0);}100%{box-shadow:0 0 0 0 rgba(34,197,94,0);}}\
.cb-icon-btn{background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.12);color:#fff;border-radius:10px;padding:6px 10px;cursor:pointer;font:500 12px system-ui;display:inline-flex;align-items:center;gap:6px;transition:background .15s;}\
.cb-icon-btn:hover{background:rgba(255,255,255,.16);}\
.cb-close{background:transparent;border:none;color:#fff;font-size:22px;line-height:1;cursor:pointer;padding:4px 8px;border-radius:8px;}\
.cb-close:hover{background:rgba(255,255,255,.12);}\
.cb-msgs{flex:1;overflow-y:auto;padding:18px;display:flex;flex-direction:column;gap:10px;background:linear-gradient(180deg,#fafbfc,#f4f6f8);scroll-behavior:smooth;}\
.cb-msgs::-webkit-scrollbar{width:8px;}.cb-msgs::-webkit-scrollbar-thumb{background:#cbd5e1;border-radius:4px;}\
.cb-msg{max-width:82%;padding:10px 14px;border-radius:18px;font-size:14px;line-height:1.55;white-space:pre-wrap;word-wrap:break-word;}\
.cb-msg.u{background:var(--cb-bubble-u);color:#fff;align-self:flex-end;border-end-end-radius:6px;}\
.cb-msg.b{background:var(--cb-bubble-b);color:var(--cb-fg);align-self:flex-start;border-end-start-radius:6px;}\
.cb-msg.err{background:#fef2f2;color:#991b1b;border:1px solid #fecaca;}\
.cb-typing{display:inline-flex;gap:4px;padding:4px 0;align-self:flex-start;}\
.cb-typing span{width:6px;height:6px;border-radius:50%;background:#94a3b8;animation:cb-bounce 1s infinite ease-in-out;}\
.cb-typing span:nth-child(2){animation-delay:.15s;}.cb-typing span:nth-child(3){animation-delay:.3s;}\
@keyframes cb-bounce{0%,80%,100%{transform:scale(.6);opacity:.5;}40%{transform:scale(1);opacity:1;}}\
.cb-row{display:flex;gap:8px;padding:12px 14px;border-top:1px solid var(--cb-border);background:#fff;align-items:flex-end;}\
.cb-input{flex:1;min-height:42px;max-height:120px;padding:11px 14px;border:1px solid #e2e8f0;border-radius:14px;font:14px system-ui;outline:none;resize:none;background:#f8fafc;transition:border-color .15s, background .15s;}\
.cb-input:focus{border-color:var(--cb-accent);background:#fff;}\
.cb-send{width:42px;height:42px;flex-shrink:0;background:var(--cb-accent);color:#fff;border:none;border-radius:14px;cursor:pointer;font-size:18px;transition:transform .1s, opacity .2s;}\
.cb-send:hover{transform:scale(1.05);}.cb-send:disabled{opacity:.4;cursor:not-allowed;}\
.cb-foot{padding:8px 14px;font-size:11px;color:var(--cb-muted);text-align:center;border-top:1px solid var(--cb-border);background:#fff;}\
.cb-langs{position:absolute;inset-block-start:62px;inset-inline-end:14px;background:#fff;color:var(--cb-fg);border-radius:14px;box-shadow:0 14px 40px rgba(15,23,42,.2);border:1px solid var(--cb-border);padding:6px;display:none;flex-direction:column;min-width:170px;max-height:300px;overflow-y:auto;z-index:5;}\
.cb-langs[data-open="1"]{display:flex;}\
.cb-lang{display:flex;align-items:center;gap:10px;padding:9px 12px;border-radius:9px;cursor:pointer;font:14px system-ui;background:transparent;border:none;text-align:start;color:inherit;}\
.cb-lang:hover{background:#f1f5f9;}\
.cb-lang[data-active="1"]{background:#e0f2fe;color:#0369a1;font-weight:600;}\
.cb-lang small{color:var(--cb-muted);font-size:11px;}\
@media (max-width:520px){.cb-panel{inset-inline-end:0;inset-inline-start:0;bottom:0;width:100vw;max-width:100vw;height:88vh;max-height:88vh;border-radius:20px 20px 0 0;}.cb-launcher{bottom:18px;inset-inline-end:18px;}}\
';

var style = document.createElement('style'); style.textContent = css; document.head.appendChild(style);

// ── Markup ────────────────────────────────────────────────────────────────
var launcher = document.createElement('button');
launcher.className = 'cb-launcher';
launcher.setAttribute('aria-label','Open chat');
launcher.innerHTML = '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>';

var panel = document.createElement('div');
panel.className = 'cb-panel';
panel.setAttribute('role','dialog');
panel.setAttribute('aria-modal','false');
panel.setAttribute('aria-label', CONFIG.clientName);
panel.dir = dir();

panel.innerHTML = '\
  <div class="cb-head">\
    <div class="cb-title"><b></b><small></small></div>\
    <button type="button" class="cb-icon-btn cb-lang-btn" aria-haspopup="true" aria-expanded="false">🌐 <span class="cb-lang-label"></span></button>\
    <button type="button" class="cb-close" aria-label="Close chat">&times;</button>\
  </div>\
  <div class="cb-langs" role="menu"></div>\
  <div class="cb-msgs" aria-live="polite"></div>\
  <form class="cb-row" autocomplete="off">\
    <textarea class="cb-input" rows="1" maxlength="4000" aria-label="Message"></textarea>\
    <button type="submit" class="cb-send" aria-label="Send">\
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>\
    </button>\
  </form>\
  <div class="cb-foot"></div>\
';

document.body.appendChild(launcher);
document.body.appendChild(panel);

var $title = panel.querySelector('.cb-title b');
var $sub   = panel.querySelector('.cb-title small');
var $msgs  = panel.querySelector('.cb-msgs');
var $form  = panel.querySelector('.cb-row');
var $in    = panel.querySelector('.cb-input');
var $send  = panel.querySelector('.cb-send');
var $foot  = panel.querySelector('.cb-foot');
var $langBtn = panel.querySelector('.cb-lang-btn');
var $langLbl = panel.querySelector('.cb-lang-label');
var $langs   = panel.querySelector('.cb-langs');
var $close   = panel.querySelector('.cb-close');

// ── Render strings for the active language ───────────────────────────────
function applyLang(){
  var b = bundle();
  panel.dir = dir();
  $title.textContent = CONFIG.clientName;
  $sub.innerHTML = '<span class="cb-status"><span class="cb-dot"></span>'+(b.powered_by||'AI assistant')+'</span>';
  $in.placeholder = b.placeholder || '';
  $send.title = b.send || '';
  $send.setAttribute('aria-label', b.send || 'Send');
  $foot.textContent = b.powered_by || '';
  $langBtn.setAttribute('aria-label', b.language || 'Language');
  $langLbl.textContent = current.code.toUpperCase();
  $close.setAttribute('aria-label', b.minimize || 'Close');
  // Re-render greeting bubble
  $msgs.innerHTML = '';
  add((CONFIG.greetings && CONFIG.greetings[current.code]) || b.welcome || '', 'b');
  // Rebuild language menu
  $langs.innerHTML = '';
  CONFIG.languages.forEach(function(l){
    var btn = document.createElement('button');
    btn.type='button';
    btn.className='cb-lang';
    btn.dataset.active = (l.code===current.code)?'1':'0';
    btn.innerHTML = '<span>'+l.native+'</span><small>'+l.name+'</small>';
    btn.addEventListener('click', function(){
      current = l;
      localStorage.setItem(STORAGE_LANG, l.code);
      $langs.dataset.open='0';
      $langBtn.setAttribute('aria-expanded','false');
      applyLang();
    });
    $langs.appendChild(btn);
  });
}

function add(text, who){
  var d = document.createElement('div');
  d.className = 'cb-msg ' + who;
  d.textContent = text;
  $msgs.appendChild(d);
  $msgs.scrollTop = $msgs.scrollHeight;
  return d;
}

function typing(){
  var d = document.createElement('div');
  d.className='cb-typing';
  d.innerHTML='<span></span><span></span><span></span>';
  $msgs.appendChild(d);
  $msgs.scrollTop = $msgs.scrollHeight;
  return d;
}

async function send(text){
  add(text, 'u');
  var t = typing();
  $send.disabled = true;
  try {
    var res = await fetch(CONFIG.apiUrl + '/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text, session_id: sid, language: current.code })
    });
    var data = {};
    try { data = await res.json(); } catch(_) {}
    t.remove();
    if (res.ok) {
      add(data.answer || '(empty reply)', 'b');
    } else if (res.status === 429) {
      add(data.detail || bundle().rate_limited || 'Too many requests.', 'b');
    } else if (res.status === 402) {
      add(data.detail || bundle().budget_reached || '', 'b');
    } else {
      var d = add(data.detail || bundle().connection_error || 'Error', 'b');
      d.classList.add('err');
    }
  } catch(e) {
    t.remove();
    var d = add(bundle().connection_error || 'Connection error.', 'b');
    d.classList.add('err');
  } finally {
    $send.disabled = false;
    $in.focus();
  }
}

// ── Wiring ───────────────────────────────────────────────────────────────
launcher.addEventListener('click', function(){
  var open = panel.dataset.open === '1';
  panel.dataset.open = open ? '0' : '1';
  if (!open) { setTimeout(function(){ $in.focus(); }, 50); }
});
$close.addEventListener('click', function(){
  panel.dataset.open = '0';
  launcher.focus();
});
document.addEventListener('keydown', function(e){
  if (e.key === 'Escape' && panel.dataset.open === '1') {
    panel.dataset.open = '0';
    launcher.focus();
  }
});

$langBtn.addEventListener('click', function(){
  var open = $langs.dataset.open === '1';
  $langs.dataset.open = open ? '0' : '1';
  $langBtn.setAttribute('aria-expanded', open ? 'false' : 'true');
});
document.addEventListener('click', function(e){
  if (!panel.contains(e.target)) { $langs.dataset.open='0'; $langBtn.setAttribute('aria-expanded','false'); }
});

$in.addEventListener('input', function(){
  this.style.height='auto';
  this.style.height = Math.min(this.scrollHeight, 120)+'px';
});
$in.addEventListener('keydown', function(e){
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    $form.requestSubmit();
  }
});
$form.addEventListener('submit', function(e){
  e.preventDefault();
  var text = $in.value.trim();
  if (!text) return;
  $in.value=''; $in.style.height='auto';
  send(text);
});

applyLang();
"""


# ── Demo landing page ───────────────────────────────────────────────────────


def demo_page(base_url: str, bot: Chatbot) -> str:
    s = bot.settings
    name = bot.profile.client.name
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{name} — Chat</title>
<style>
  *{{box-sizing:border-box;}}
  body{{font-family:-apple-system,system-ui,"Segoe UI",Roboto,sans-serif;
       background:linear-gradient(180deg,#f8fafc,#eef2f7);color:#0f172a;margin:0;
       min-height:100vh;}}
  header{{background:linear-gradient(135deg,#0f172a,#1e293b);color:#fff;padding:32px 32px;}}
  header h1{{margin:0;font-size:24px;font-weight:700;letter-spacing:-.01em;}}
  header p{{margin:6px 0 0;color:#94a3b8;font-size:14px;}}
  main{{max-width:920px;margin:32px auto;padding:0 24px;}}
  .card{{background:#fff;border-radius:16px;padding:22px;border:1px solid #e2e8f0;
         box-shadow:0 1px 3px rgba(15,23,42,.04);}}
  .card h2{{margin:0 0 12px;font-size:14px;color:#475569;font-weight:600;
           text-transform:uppercase;letter-spacing:.04em;}}
  .pill{{display:inline-flex;align-items:center;gap:6px;background:#dcfce7;color:#166534;
         padding:4px 12px;border-radius:999px;font-size:12px;font-weight:600;}}
  .pill::before{{content:"";width:7px;height:7px;border-radius:50%;background:#22c55e;}}
  pre{{background:#0f172a;color:#7ee787;padding:16px;border-radius:10px;
       overflow-x:auto;font-size:13px;line-height:1.6;
       font-family:ui-monospace,Menlo,Consolas,monospace;}}
</style></head>
<body>
<header>
  <h1>{name}</h1>
  <p>AI-powered chat assistant</p>
</header>
<main>
  <div class="card" style="margin-bottom:18px;">
    <h2>Status</h2>
    <span class="pill">online</span>
  </div>

  <div class="card">
    <h2>Embed widget</h2>
    <pre>&lt;script src="{base_url}/widget.js" async&gt;&lt;/script&gt;</pre>
  </div>
</main>
<script src="{base_url}/widget.js" async></script>
</body></html>"""
