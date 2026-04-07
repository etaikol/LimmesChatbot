"""
Embeddable web chat widget.

Drop this one-liner into any HTML page (the API host needs CORS allowed):

    <script src="https://your-api/widget.js" async></script>

It injects a floating chat bubble that talks to `POST /chat`.

The widget supports right-to-left scripts (Hebrew/Arabic) automatically when
the client config sets `language_primary` to `he` or `ar`.
"""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, Response

from chatbot.core.engine import Chatbot

router = APIRouter(tags=["widget"])


@router.get("/widget.js")
def widget_js(request: Request) -> Response:
    bot: Chatbot = request.app.state.bot
    base_url = str(request.base_url).rstrip("/")
    js = build_widget_js(
        api_url=base_url,
        client_name=bot.profile.client.name,
        greeting=bot.greet(),
        rtl=bot.profile.client.language_primary in {"he", "ar", "fa", "ur"},
    )
    return Response(content=js, media_type="application/javascript")


def build_widget_js(
    api_url: str,
    client_name: str,
    greeting: str,
    rtl: bool = False,
) -> str:
    """Return the widget JS as a string. RTL flag flips the bubble layout."""
    direction = "rtl" if rtl else "ltr"
    text_align = "right" if rtl else "left"
    side = "left" if rtl else "right"

    return (
        "(function(){"
        "var DIR='" + direction + "';"
        "var ALIGN='" + text_align + "';"
        "var SIDE='" + side + "';"
        "var API='" + api_url + "';"
        "var CLIENT='" + _js_escape(client_name) + "';"
        "var GREETING='" + _js_escape(greeting) + "';"
        + _WIDGET_BODY +
        "})();"
    )


def _js_escape(s: str) -> str:
    return (
        s.replace("\\", "\\\\")
        .replace("'", "\\'")
        .replace("\n", "\\n")
        .replace("\r", "")
    )


# Body of the widget. Kept as a separate constant for readability.
_WIDGET_BODY = r"""
var sid='web_'+Math.random().toString(36).slice(2);
var st=document.createElement('style');
st.textContent='\
#cb-btn{position:fixed;bottom:24px;'+SIDE+':24px;z-index:99998;\
width:60px;height:60px;border-radius:50%;background:#111;color:#fff;\
border:none;cursor:pointer;box-shadow:0 6px 22px rgba(0,0,0,.25);\
display:flex;align-items:center;justify-content:center;font-size:26px;}\
#cb-btn:hover{transform:scale(1.05);}\
#cb-win{position:fixed;bottom:96px;'+SIDE+':24px;z-index:99999;\
width:360px;max-width:calc(100% - 32px);height:520px;max-height:calc(100% - 120px);\
background:#fff;border-radius:18px;box-shadow:0 12px 40px rgba(0,0,0,.18);\
display:none;flex-direction:column;overflow:hidden;\
font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;direction:'+DIR+';}\
#cb-head{padding:14px 18px;background:#111;color:#fff;font-weight:600;\
display:flex;justify-content:space-between;align-items:center;font-size:15px;}\
#cb-head .x{cursor:pointer;font-size:22px;line-height:1;opacity:.85;}\
#cb-msgs{flex:1;overflow-y:auto;padding:16px;display:flex;flex-direction:column;gap:10px;background:#fafafa;}\
.cb-m{max-width:80%;padding:10px 14px;border-radius:14px;font-size:14px;line-height:1.55;\
white-space:pre-wrap;text-align:'+ALIGN+';}\
.cb-m.u{background:#111;color:#fff;align-self:flex-end;border-bottom-'+SIDE+'-radius:4px;}\
.cb-m.b{background:#fff;color:#111;border:1px solid #eee;align-self:flex-start;\
border-bottom-'+(SIDE==="right"?"left":"right")+'-radius:4px;}\
#cb-row{display:flex;padding:12px;border-top:1px solid #eee;gap:8px;background:#fff;}\
#cb-in{flex:1;padding:11px 14px;border:1px solid #ddd;border-radius:24px;font-size:14px;outline:none;direction:'+DIR+';text-align:'+ALIGN+';}\
#cb-snd{padding:11px 18px;background:#111;color:#fff;border:none;border-radius:24px;cursor:pointer;font-size:14px;}';
document.head.appendChild(st);

var btn=document.createElement('button');
btn.id='cb-btn'; btn.innerHTML='&#x1F4AC;';
var win=document.createElement('div');
win.id='cb-win';
win.innerHTML='<div id="cb-head"><span>'+CLIENT+'</span><span class="x" id="cb-x">&times;</span></div>'
+'<div id="cb-msgs"><div class="cb-m b">'+GREETING+'</div></div>'
+'<div id="cb-row"><input id="cb-in" placeholder="..." /><button id="cb-snd">&#10148;</button></div>';
document.body.appendChild(btn);
document.body.appendChild(win);

function add(text,who){
  var m=document.getElementById('cb-msgs');
  var d=document.createElement('div');
  d.className='cb-m '+who;
  d.textContent=text;
  m.appendChild(d);
  m.scrollTop=m.scrollHeight;
  return d;
}
async function send(){
  var i=document.getElementById('cb-in');
  var t=i.value.trim();
  if(!t)return;
  add(t,'u'); i.value='';
  var th=add('...','b');
  try{
    var r=await fetch(API+'/chat',{
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({message:t,session_id:sid})
    });
    var j=await r.json();
    th.textContent=j.answer||j.detail||'(no reply)';
  }catch(e){ th.textContent='Connection error.'; }
}
btn.addEventListener('click',function(){
  win.style.display = win.style.display==='flex'?'none':'flex';
});
document.getElementById('cb-x').addEventListener('click',function(){win.style.display='none';});
document.getElementById('cb-snd').addEventListener('click',send);
document.getElementById('cb-in').addEventListener('keydown',function(e){if(e.key==='Enter')send();});
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
<title>{name} — Chatbot API</title>
<style>
  body{{font-family:system-ui,sans-serif;background:#f7f7f7;color:#111;margin:0;}}
  header{{background:#111;color:#fff;padding:24px 32px;}}
  header h1{{margin:0;font-size:22px;font-weight:700;}}
  header p{{margin:4px 0 0;color:#aaa;font-size:14px;}}
  main{{max-width:820px;margin:32px auto;padding:0 24px;}}
  .card{{background:#fff;border-radius:12px;padding:22px;margin-bottom:18px;
         box-shadow:0 1px 6px rgba(0,0,0,.05);}}
  .card h2{{margin:0 0 10px;font-size:16px;}}
  code{{background:#f0f0f0;padding:2px 6px;border-radius:4px;font-size:13px;}}
  pre{{background:#111;color:#7ee787;padding:14px;border-radius:8px;overflow-x:auto;
       font-size:13px;line-height:1.55;}}
  .pill{{display:inline-block;background:#e8f5e9;color:#2e7d32;padding:3px 10px;
         border-radius:20px;font-size:12px;font-weight:600;}}
</style></head>
<body>
<header>
  <h1>{name}</h1>
  <p>RAG chatbot template — running</p>
</header>
<main>
  <div class="card">
    <h2>Status</h2>
    <p><span class="pill">online</span>
       &nbsp;model: <code>{s.llm_model}</code>
       &nbsp;personality: <code>{bot.profile.personality.name}</code></p>
  </div>

  <div class="card">
    <h2>Embed on any website</h2>
    <pre>&lt;script src="{base_url}/widget.js" async&gt;&lt;/script&gt;</pre>
  </div>

  <div class="card">
    <h2>WhatsApp (Twilio)</h2>
    <pre>POST {base_url}/webhook/whatsapp</pre>
  </div>

  <div class="card">
    <h2>Telegram</h2>
    <pre>POST {base_url}/webhook/telegram</pre>
  </div>

  <div class="card">
    <h2>LINE</h2>
    <pre>POST {base_url}/webhook/line</pre>
  </div>

  <div class="card">
    <h2>REST</h2>
    <pre>POST {base_url}/chat
Content-Type: application/json

{{
  "message": "What are your opening hours?",
  "session_id": "user-1"
}}</pre>
  </div>

  <div class="card">
    <h2>Docs</h2>
    <p>Interactive Swagger: <a href="{base_url}/docs">{base_url}/docs</a><br>
       Health: <a href="{base_url}/health">{base_url}/health</a></p>
  </div>
</main>
<script src="{base_url}/widget.js" async></script>
</body></html>"""
