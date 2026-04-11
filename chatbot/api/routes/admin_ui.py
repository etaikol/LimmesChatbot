"""
Admin dashboard HTML/JS.

Single-page application served inline — no build step, no CDN.
Styled with system fonts and a dark sidebar layout.
Communicates with the /admin/api/* endpoints.

Layout: _CSS, _HTML_BODY, _JS are separate constants for navigability.
Translations live in _TRANSLATIONS (Python dict) injected as JSON.
"""

from __future__ import annotations

import json


def dashboard_html() -> str:
    langs_json = json.dumps(_TRANSLATIONS, ensure_ascii=False, separators=(",", ":"))
    return (
        '<!DOCTYPE html>\n<html lang="en">\n<head>\n'
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>Chatbot Admin</title>\n"
        "<style>\n" + _CSS + "\n</style>\n</head>\n<body>\n"
        + _HTML_BODY
        + "\n<script>\n"
        + _JS.replace("__LANGS_JSON__", langs_json)
        + "\n</script>\n</body>\n</html>"
    )


# ══════════════════════════════════════════════════════════════════════
# CSS
# ══════════════════════════════════════════════════════════════════════
_CSS = r"""
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{--bg:#0f172a;--bg2:#1e293b;--bg3:#334155;--fg:#f1f5f9;--muted:#94a3b8;--accent:#0ea5e9;--accent2:#38bdf8;--success:#22c55e;--warn:#f59e0b;--danger:#ef4444;--card:#1e293b;--border:#334155;--radius:12px;--shadow:0 4px 24px rgba(0,0,0,.3)}
body{font-family:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;background:var(--bg);color:var(--fg);min-height:100vh;display:flex}
a{color:var(--accent2);text-decoration:none}
button{cursor:pointer;font:inherit}

/* Sidebar */
.sidebar{width:240px;background:var(--bg2);border-right:1px solid var(--border);display:flex;flex-direction:column;position:fixed;top:0;left:0;bottom:0;z-index:10}
.sidebar-brand{padding:20px;font-size:18px;font-weight:700;color:var(--accent);border-bottom:1px solid var(--border);display:flex;align-items:center;gap:10px}
.sidebar-nav{flex:1;padding:12px 8px;display:flex;flex-direction:column;gap:2px;overflow-y:auto}
.nav-item{display:flex;align-items:center;gap:10px;padding:10px 14px;border-radius:8px;color:var(--muted);font-size:14px;font-weight:500;border:none;background:none;text-align:left;width:100%;transition:all .15s}
.nav-item:hover{background:var(--bg3);color:var(--fg)}
.nav-item.active{background:rgba(14,165,233,.15);color:var(--accent)}
.nav-item svg{width:18px;height:18px;flex-shrink:0}
.nav-section{padding:8px 14px 4px;font-size:10px;color:var(--bg3);text-transform:uppercase;letter-spacing:.08em;margin-top:8px}

/* Main */
.main{margin-left:240px;flex:1;padding:24px;min-height:100vh}
.page{display:none}.page.active{display:block}
.page-title{font-size:22px;font-weight:700;margin-bottom:20px;display:flex;align-items:center;gap:10px}

/* Cards */
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:16px;margin-bottom:24px}
.card{background:var(--card);border:1px solid var(--border);border-radius:var(--radius);padding:18px;transition:border-color .15s}
.card:hover{border-color:var(--accent)}
.card-label{font-size:12px;color:var(--muted);text-transform:uppercase;letter-spacing:.05em;margin-bottom:6px}
.card-value{font-size:28px;font-weight:700}
.card-sub{font-size:12px;color:var(--muted);margin-top:4px}

/* Tables */
.tbl-wrap{background:var(--card);border:1px solid var(--border);border-radius:var(--radius);overflow:hidden;margin-bottom:20px}
table{width:100%;border-collapse:collapse;font-size:13px}
th{text-align:left;padding:10px 14px;background:var(--bg3);color:var(--muted);font-weight:600;text-transform:uppercase;font-size:11px;letter-spacing:.04em}
td{padding:10px 14px;border-top:1px solid var(--border)}
tr:hover td{background:rgba(255,255,255,.02)}

/* Tags */
.tag{display:inline-block;padding:3px 10px;border-radius:20px;font-size:11px;font-weight:600}
.tag-on{background:rgba(34,197,94,.15);color:var(--success)}
.tag-off{background:rgba(239,68,68,.15);color:var(--danger)}

/* Buttons */
.btn{display:inline-flex;align-items:center;gap:6px;padding:8px 16px;border-radius:8px;font-size:13px;font-weight:600;border:none;transition:all .15s}
.btn-primary{background:var(--accent);color:#fff}.btn-primary:hover{background:var(--accent2)}
.btn-danger{background:var(--danger);color:#fff}.btn-danger:hover{opacity:.85}
.btn-ghost{background:transparent;color:var(--muted);border:1px solid var(--border)}.btn-ghost:hover{color:var(--fg);border-color:var(--muted)}
.btn-ghost.active{background:var(--accent);color:#fff;border-color:var(--accent)}
.btn-sm{padding:5px 12px;font-size:12px}

/* Forms */
.form-group{margin-bottom:14px}
.form-label{display:block;font-size:12px;color:var(--muted);margin-bottom:4px;font-weight:600}
.form-input,.form-select,.form-textarea{width:100%;padding:9px 12px;border:1px solid var(--border);border-radius:8px;background:var(--bg);color:var(--fg);font:13px system-ui;outline:none;transition:border-color .15s}
.form-input:focus,.form-textarea:focus{border-color:var(--accent)}
.form-textarea{resize:vertical;min-height:120px;font-family:monospace}

/* Tabs */
.tab-bar{display:flex;gap:4px;margin-bottom:20px;border-bottom:1px solid var(--border);padding-bottom:0}
.tab-btn{padding:8px 16px;border:none;background:none;color:var(--muted);font-size:13px;font-weight:600;cursor:pointer;border-bottom:2px solid transparent;margin-bottom:-1px;transition:all .15s}
.tab-btn:hover{color:var(--fg)}
.tab-btn.active{color:var(--accent);border-bottom-color:var(--accent)}
.view-toggle{display:inline-flex;gap:2px;background:var(--bg3);border-radius:8px;padding:2px}
.view-toggle .tab-btn{border-bottom:none;border-radius:6px;padding:5px 12px;font-size:12px;margin:0}
.view-toggle .tab-btn.active{background:var(--accent);color:#fff}

/* Toast */
.toast{position:fixed;bottom:24px;right:24px;padding:12px 20px;border-radius:10px;font-size:13px;font-weight:600;color:#fff;z-index:9999;opacity:0;transform:translateY(10px);transition:all .25s}
.toast.show{opacity:1;transform:none}
.toast-ok{background:var(--success)}.toast-err{background:var(--danger)}.toast-warn{background:var(--warn)}

/* Progress bar */
.progress{height:8px;background:var(--bg3);border-radius:4px;overflow:hidden;margin-top:8px}
.progress-fill{height:100%;border-radius:4px;transition:width .3s}

/* Log viewer */
.log-viewer{background:#0d1117;border:1px solid var(--border);border-radius:var(--radius);padding:14px;font:12px/1.6 "Cascadia Code","Fira Code",monospace;color:#c9d1d9;max-height:500px;overflow-y:auto;white-space:pre-wrap;word-break:break-all}

/* Auth overlay */
.auth-overlay{position:fixed;inset:0;background:var(--bg);display:flex;align-items:center;justify-content:center;z-index:9999}
.auth-box{background:var(--card);border:1px solid var(--border);border-radius:16px;padding:32px;width:360px;text-align:center;box-shadow:var(--shadow)}
.auth-box h2{margin-bottom:8px;font-size:20px}
.auth-box p{color:var(--muted);font-size:13px;margin-bottom:20px}
.auth-box .form-input{text-align:center;font-size:15px;margin-bottom:16px}

/* Mobile */
@media(max-width:768px){.sidebar{width:60px}.sidebar-brand span,.nav-item span{display:none}.main{margin-left:60px;padding:16px}.cards{grid-template-columns:1fr}}

/* Modal */
.modal-bg{position:fixed;inset:0;background:rgba(0,0,0,.6);z-index:100;display:flex;align-items:center;justify-content:center}
.modal{background:var(--card);border:1px solid var(--border);border-radius:16px;width:700px;max-width:90vw;max-height:85vh;display:flex;flex-direction:column;box-shadow:var(--shadow)}
.modal-head{padding:16px 20px;border-bottom:1px solid var(--border);display:flex;align-items:center;justify-content:space-between}
.modal-head h3{font-size:16px}
.modal-body{flex:1;overflow-y:auto;padding:20px}
.msg-row{margin-bottom:12px;display:flex;flex-direction:column;gap:4px}
.msg-role{font-size:11px;font-weight:700;text-transform:uppercase;color:var(--muted)}
.msg-text{padding:10px 14px;border-radius:12px;font-size:13px;line-height:1.55;white-space:pre-wrap}
.msg-row.human .msg-text{background:var(--bg3);align-self:flex-end;max-width:85%}
.msg-row.ai .msg-text{background:rgba(14,165,233,.1);align-self:flex-start;max-width:85%}

/* Rich text editor */
.editor-toolbar{display:flex;gap:4px;padding:6px 8px;background:var(--bg3);border:1px solid var(--border);border-bottom:none;border-radius:var(--radius) var(--radius) 0 0;flex-wrap:wrap;align-items:center}
.editor-toolbar button{padding:4px 10px;border:1px solid var(--border);border-radius:6px;background:var(--bg2);color:var(--fg);font-size:13px;cursor:pointer;transition:all .15s;min-width:32px}
.editor-toolbar button:hover{background:var(--accent);color:#fff;border-color:var(--accent)}
.editor-toolbar .sep{width:1px;height:22px;background:var(--border);margin:0 4px}
.rich-editor{border:1px solid var(--border);border-radius:0 0 var(--radius) var(--radius);min-height:300px;padding:14px;background:var(--bg);color:var(--fg);font-size:14px;line-height:1.65;outline:none;overflow-y:auto;max-height:600px}
.rich-editor:focus{border-color:var(--accent)}
.rich-editor h1,.rich-editor h2,.rich-editor h3{margin-top:12px;margin-bottom:6px}
.rich-editor h1{font-size:22px}.rich-editor h2{font-size:18px}.rich-editor h3{font-size:15px}
.rich-editor ul,.rich-editor ol{padding-left:20px;margin:8px 0}
.rich-editor blockquote{border-left:3px solid var(--accent);padding-left:12px;margin:8px 0;color:var(--muted)}
.rich-editor hr{border:none;border-top:1px solid var(--border);margin:12px 0}

/* Upload zone */
.upload-zone{border:2px dashed var(--border);border-radius:var(--radius);padding:24px;text-align:center;color:var(--muted);cursor:pointer;transition:all .2s}
.upload-zone:hover,.upload-zone.dragover{border-color:var(--accent);color:var(--accent);background:rgba(14,165,233,.05)}
.upload-zone input{display:none}

/* Config form sections */
.cfg-card{background:var(--card);border:1px solid var(--border);border-radius:var(--radius);padding:16px;margin-bottom:12px}
.cfg-card h4{font-size:13px;color:var(--accent);margin-bottom:12px;text-transform:uppercase;letter-spacing:.04em}
.cfg-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px}
@media(max-width:768px){.cfg-grid{grid-template-columns:1fr}}

/* Multiline form field */
.field-multiline{width:100%;padding:9px 12px;border:1px solid var(--border);border-radius:8px;background:var(--bg);color:var(--fg);font:13px system-ui;outline:none;min-height:80px;resize:vertical;white-space:pre-wrap;transition:border-color .15s}
.field-multiline:focus{border-color:var(--accent)}

/* Emoji picker */
.emoji-picker{position:fixed;z-index:9999;background:var(--card);border:1px solid var(--border);border-radius:12px;padding:10px;box-shadow:var(--shadow);width:340px;max-height:420px;overflow-y:auto}
.emoji-cat-label{font-size:10px;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:.07em;padding:6px 2px 2px;display:block}
.emoji-grid{display:grid;grid-template-columns:repeat(8,1fr);gap:2px;margin-bottom:4px}
.emoji-grid button{font-size:19px;padding:5px;border:none;background:none;cursor:pointer;border-radius:6px;transition:background .1s;line-height:1}
.emoji-grid button:hover{background:var(--bg3)}

/* Language switcher */
.lang-switcher{padding:10px 8px;border-top:1px solid var(--border);display:flex;gap:4px;justify-content:center;flex-wrap:wrap}
.lang-btn{padding:4px 11px;border:1px solid var(--border);border-radius:6px;background:none;color:var(--muted);font-size:11px;font-weight:700;cursor:pointer;transition:all .15s;letter-spacing:.03em}
.lang-btn:hover{color:var(--fg);border-color:var(--muted)}
.lang-btn.active{background:var(--accent);color:#fff;border-color:var(--accent)}
[dir=rtl] .sidebar{left:auto;right:0;border-right:none;border-left:1px solid var(--border)}
[dir=rtl] .main{margin-left:0;margin-right:240px}
@media(max-width:768px){[dir=rtl] .main{margin-right:60px}}

/* Onboarding */
.onb-overlay{position:fixed;inset:0;background:rgba(0,0,0,.35);z-index:9998;pointer-events:none;transition:opacity .3s}
.onb-card{position:fixed;top:24px;left:50%;transform:translateX(-50%);z-index:9999;background:var(--card);border:1px solid var(--accent);border-radius:16px;width:460px;max-width:92vw;min-height:280px;padding:22px 24px 18px;box-shadow:0 8px 40px rgba(14,165,233,.25);pointer-events:all;text-align:center;display:flex;flex-direction:column;direction:ltr}
.onb-card .onb-icon{font-size:32px;margin-bottom:6px}
.onb-card .onb-title{font-size:17px;font-weight:700;margin-bottom:3px}
.onb-card .onb-body{font-size:13px;line-height:1.55;color:var(--muted);margin-bottom:14px;min-height:56px}
.onb-dots{display:flex;justify-content:center;gap:8px;margin-bottom:12px}
.onb-dot{width:8px;height:8px;border-radius:50%;background:var(--bg3);transition:background .2s}
.onb-dot.active{background:var(--accent)}
.onb-btns{display:flex;justify-content:space-between;align-items:center;margin-top:auto;min-height:36px}
.onb-lang{display:flex;gap:4px;justify-content:center;margin-bottom:10px}
.onb-lang button{padding:3px 9px;border:1px solid var(--border);border-radius:5px;background:none;color:var(--muted);font-size:10px;font-weight:700;cursor:pointer}
.onb-lang button.active{background:var(--accent);color:#fff;border-color:var(--accent)}
.onb-highlight{position:relative;z-index:9999;box-shadow:0 0 0 4px var(--accent),0 0 20px rgba(14,165,233,.3);border-radius:var(--radius);transition:box-shadow .3s}"""

# ══════════════════════════════════════════════════════════════════════
# HTML body (between <body> and <script>)
# ══════════════════════════════════════════════════════════════════════
_HTML_BODY = r"""
<!-- Auth -->
<div class="auth-overlay" id="auth">
  <div class="auth-box">
    <div style="font-size:36px;margin-bottom:12px">🔒</div>
    <h2>Admin Dashboard</h2>
    <p>Sign in with your admin credentials</p>
    <input type="text" class="form-input" id="loginUser" placeholder="Username" style="margin-bottom:10px" autofocus>
    <input type="password" class="form-input" id="loginPass" placeholder="Password" style="margin-bottom:16px">
    <button class="btn btn-primary" style="width:100%" onclick="tryLogin()">Sign In</button>
    <p id="authErr" style="color:var(--danger);margin-top:12px;font-size:12px;display:none"></p>
  </div>
</div>

<!-- Sidebar -->
<nav class="sidebar" id="sidebar" style="display:none">
  <div class="sidebar-brand">
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/></svg>
    <span>Admin</span>
  </div>
  <div class="sidebar-nav">
    <button class="nav-item active" data-page="overview" onclick="showPage('overview',this)">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>
      <span data-i18n="nav.overview">Overview</span>
    </button>
    <button class="nav-item" data-page="sessions" onclick="showPage('sessions',this)">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
      <span data-i18n="nav.sessions">Sessions</span>
    </button>
    <button class="nav-item" data-page="budget" onclick="showPage('budget',this)">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>
      <span data-i18n="nav.budget">Budget</span>
    </button>
    <button class="nav-item" data-page="config" onclick="showPage('config',this)">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>
      <span data-i18n="nav.config">Configuration</span>
    </button>
    <div class="nav-section" data-i18n="nav.section.channels">Channels</div>
    <button class="nav-item" data-page="line" onclick="showPage('line',this)">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"/></svg>
      <span data-i18n="nav.line">LINE</span>
    </button>
    <div class="nav-section" data-i18n="nav.section.business">Business</div>
    <button class="nav-item" data-page="products" onclick="showPage('products',this)">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 2L3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z"/><line x1="3" y1="6" x2="21" y2="6"/><path d="M16 10a4 4 0 0 1-8 0"/></svg>
      <span data-i18n="nav.products">Products</span>
    </button>
    <button class="nav-item" data-page="contacts" onclick="showPage('contacts',this)">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>
      <span data-i18n="nav.contacts">Messages</span>
    </button>
    <button class="nav-item" data-page="handoff" onclick="showPage('handoff',this)">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
      <span data-i18n="nav.handoff">Handoff</span>
    </button>
    <button class="nav-item" data-page="fallback" onclick="showPage('fallback',this)">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
      <span data-i18n="nav.fallback">Unanswered</span>
    </button>
    <div class="nav-section" data-i18n="nav.section.content">Content</div>
    <button class="nav-item" data-page="data" onclick="showPage('data',this)">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>
      <span data-i18n="nav.data">Data Files</span>
    </button>
    <button class="nav-item" data-page="logs" onclick="showPage('logs',this)">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="4 17 10 11 4 5"/><line x1="12" y1="19" x2="20" y2="19"/></svg>
      <span data-i18n="nav.logs">Logs</span>
    </button>
    <div class="nav-section" id="navSectionAdmin" style="display:none" data-i18n="nav.section.admin">Admin</div>
    <button class="nav-item" id="navUsers" data-page="users" onclick="showPage('users',this)" style="display:none">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
      <span data-i18n="nav.users">Users</span>
    </button>
  </div>
  <div id="sidebarUser" style="padding:10px 12px;border-top:1px solid var(--border);font-size:12px;display:none">
    <div style="display:flex;align-items:center;justify-content:space-between">
      <span><span id="sidebarUsername" style="font-weight:600"></span> <span class="tag tag-on" id="sidebarRole" style="font-size:10px"></span></span>
      <button class="btn btn-ghost btn-sm" onclick="doLogout()" style="padding:3px 8px;font-size:11px">Logout</button>
    </div>
  </div>
  <div class="lang-switcher">
    <button class="lang-btn active" data-lang="en" onclick="setLang('en')" title="English">EN</button>
    <button class="lang-btn" data-lang="th" onclick="setLang('th')" title="ภาษาไทย">TH</button>
    <button class="lang-btn" data-lang="he" onclick="setLang('he')" title="עברית">HE</button>
  </div>
</nav>

<!-- Content -->
<div class="main" id="mainContent" style="display:none">

  <!-- ═══════ Overview ═══════ -->
  <div class="page active" id="page-overview">
    <div class="page-title" data-i18n="page.overview">📊 Overview</div>
    <div class="cards" id="overviewCards"></div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px">
      <div>
        <h3 style="font-size:14px;color:var(--muted);margin-bottom:10px" data-i18n="ov.channels">Channels</h3>
        <div class="tbl-wrap"><table><thead><tr><th data-i18n="th.channel">Channel</th><th data-i18n="th.status">Status</th></tr></thead><tbody id="channelRows"></tbody></table></div>
      </div>
      <div>
        <h3 style="font-size:14px;color:var(--muted);margin-bottom:10px" data-i18n="ov.security">Security</h3>
        <div class="tbl-wrap"><table><thead><tr><th data-i18n="th.feature">Feature</th><th data-i18n="th.status">Status</th></tr></thead><tbody id="securityRows"></tbody></table></div>
      </div>
    </div>
  </div>

  <!-- ═══════ Sessions ═══════ -->
  <div class="page" id="page-sessions">
    <div class="page-title" style="justify-content:space-between">
      <span data-i18n="page.sessions">💬 Sessions</span>
      <div><button class="btn btn-ghost btn-sm" onclick="loadSessions()" data-i18n="btn.refresh">↻ Refresh</button> <button class="btn btn-danger btn-sm" data-admin-only onclick="clearAllSessions()" data-i18n="btn.clearAll">Clear All</button></div>
    </div>
    <div class="tbl-wrap"><table><thead><tr><th data-i18n="th.session_id">Session ID</th><th data-i18n="th.messages">Messages</th><th data-i18n="th.last_active">Last Activity</th><th data-i18n="th.actions">Actions</th></tr></thead><tbody id="sessionRows"></tbody></table></div>
  </div>

  <!-- ═══════ Budget ═══════ -->
  <div class="page" id="page-budget">
    <div class="page-title" style="justify-content:space-between">
      <span data-i18n="page.budget">💰 Budget</span>
      <button class="btn btn-danger btn-sm" data-admin-only onclick="resetBudget()" data-i18n="btn.resetToday">Reset Today</button>
    </div>
    <!-- Summary cards: today / 7d / 30d -->
    <div class="cards" id="budgetCards"></div>
    <!-- Today progress bars -->
    <div id="budgetBars"></div>
    <!-- Spend bar chart (last 30 days) -->
    <div class="card" style="margin-top:20px;padding:20px;display:none" id="budgetChartWrap">
      <div class="card-label" style="margin-bottom:12px" data-i18n="budget.chart.dailySpend30dUsd">Daily spend — last 30 days (USD)</div>
      <div id="budgetChart" style="display:flex;align-items:flex-end;gap:4px;height:80px;overflow-x:auto"></div>
      <div id="budgetChartLegend" style="display:flex;gap:16px;margin-top:8px;font-size:11px;color:var(--muted)"></div>
    </div>
    <!-- Full history table -->
    <div style="margin-top:20px;display:none" id="budgetHistoryWrap">
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px">
        <span style="font-size:14px;font-weight:600" data-i18n="budget.history.title">Spend History</span>
        <div style="display:flex;gap:6px">
          <button class="btn btn-ghost btn-sm" id="bh7" onclick="filterBudgetHistory(7,this)" data-i18n="budget.history.filter.7days">7 days</button>
          <button class="btn btn-ghost btn-sm active" id="bh30" onclick="filterBudgetHistory(30,this)" data-i18n="budget.history.filter.30days">30 days</button>
          <button class="btn btn-ghost btn-sm" id="bhAll" onclick="filterBudgetHistory(0,this)" data-i18n="budget.history.filter.all">All</button>
        </div>
      </div>
      <div class="tbl-wrap"><table><thead><tr><th data-i18n="budget.history.header.date">Date</th><th data-i18n="budget.history.header.tokensUsed">Tokens Used</th><th data-i18n="budget.history.header.usdSpent">USD Spent</th><th data-i18n="budget.history.header.dailyCapPct">% of Daily Cap</th></tr></thead><tbody id="budgetHistoryRows"></tbody></table></div>
      <div style="text-align:right;font-size:12px;color:var(--muted);margin-top:6px" id="budgetHistoryTotal"></div>
    </div>
  </div>

  <!-- ═══════ Configuration ═══════ -->
  <div class="page" id="page-config">
    <div class="page-title" data-i18n="page.config">⚙️ Configuration</div>

    <div class="tab-bar">
      <button class="tab-btn active" onclick="showConfigTab('env',this)" data-i18n="cfg.tab.env">Environment</button>
      <button class="tab-btn" onclick="showConfigTab('client',this)" data-i18n="cfg.tab.client">Client</button>
      <button class="tab-btn" onclick="showConfigTab('personality',this)" data-i18n="cfg.tab.personality">Personality</button>
    </div>

    <!-- Env -->
    <div class="config-panel" id="cfg-env">
      <div id="envForm"></div>
      <div style="margin-top:16px;display:flex;align-items:center;gap:12px">
        <button class="btn btn-primary" data-admin-only onclick="saveEnv()" data-i18n="btn.saveEnv">Save Environment Settings</button>
        <span style="font-size:11px;color:var(--muted)" data-i18n="restart.note">Restart required for changes to take effect</span>
      </div>
    </div>

    <!-- Client -->
    <div class="config-panel" id="cfg-client" style="display:none">
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:16px">
        <span style="font-size:13px;color:var(--muted)"><span data-i18n="cf.editing">Editing</span>: <strong id="clientFile"></strong></span>
        <div class="view-toggle">
          <button class="tab-btn active" onclick="setClientView('form',this)" data-i18n="view.form">Form</button>
          <button class="tab-btn" onclick="setClientView('yaml',this)" data-i18n="view.yaml">YAML</button>
        </div>
      </div>
      <div id="clientFormView"><div id="clientFormFields"></div>
        <button class="btn btn-primary" onclick="saveClientForm()" style="margin-top:16px" data-i18n="btn.saveClient">Save Client Config</button>
        <span style="font-size:11px;color:var(--muted);margin-left:12px" data-i18n="restart.note">Restart required</span>
      </div>
      <div id="clientYamlView" style="display:none">
        <textarea class="form-textarea" id="clientYaml" rows="20" style="min-height:300px"></textarea>
        <button class="btn btn-primary" onclick="saveYaml('client')" style="margin-top:12px">Save Client YAML</button>
      </div>
    </div>

    <!-- Personality -->
    <div class="config-panel" id="cfg-personality" style="display:none">
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:16px">
        <span style="font-size:13px;color:var(--muted)"><span data-i18n="cf.editing">Editing</span>: <strong id="personalityFile"></strong></span>
        <div class="view-toggle">
          <button class="tab-btn active" onclick="setPersonalityView('form',this)" data-i18n="view.form">Form</button>
          <button class="tab-btn" onclick="setPersonalityView('yaml',this)" data-i18n="view.yaml">YAML</button>
        </div>
      </div>
      <div id="personalityFormView"><div id="personalityFormFields"></div>
        <button class="btn btn-primary" onclick="savePersonalityForm()" style="margin-top:16px" data-i18n="btn.savePersonality">Save Personality Config</button>
        <span style="font-size:11px;color:var(--muted);margin-left:12px" data-i18n="restart.note">Restart required</span>
      </div>
      <div id="personalityYamlView" style="display:none">
        <textarea class="form-textarea" id="personalityYaml" rows="20" style="min-height:300px"></textarea>
        <button class="btn btn-primary" onclick="saveYaml('personality')" style="margin-top:12px">Save Personality YAML</button>
      </div>
    </div>
  </div>

  <!-- ═══════ LINE ═══════ -->
  <div class="page" id="page-line">
    <div class="page-title" data-i18n="page.line">💬 LINE Channel</div>
    <!-- Channel status (rendered by renderChannelStatus) -->
    <div id="line-channel-root"></div>
    <!-- LINE-specific tools (only visible when configured) -->
    <div id="lineTools" style="display:none">
      <div style="display:flex;align-items:center;justify-content:space-between;margin:24px 0 12px">
        <h3 style="font-size:16px;font-weight:600">Rich Menus</h3>
        <div><button class="btn btn-ghost btn-sm" onclick="loadLineMenus()">↻ Refresh</button> <button class="btn btn-primary btn-sm" onclick="showRichMenuCreator()">+ Create Menu</button></div>
      </div>
      <div id="richMenuList"></div>
      <div id="richMenuCreator" style="display:none;margin-top:16px">
        <div class="card" style="padding:20px">
          <h4 style="margin-bottom:12px;font-size:14px">Create Rich Menu</h4>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
            <div class="form-group"><label class="form-label">Name</label><input class="form-input" id="rmName" value="Main Menu"></div>
            <div class="form-group"><label class="form-label">Chat Bar Text</label><input class="form-input" id="rmChatBar" value="Tap to open" maxlength="14"></div>
            <div class="form-group"><label class="form-label">Layout</label>
              <select class="form-input" id="rmLayout" onchange="updateRMFields()"><option value="2col">2 Columns</option><option value="3col">3 Columns</option><option value="2x3" selected>2x3 Grid (6 areas)</option></select>
            </div>
          </div>
          <div id="rmAreasForm"></div>
          <div style="margin-top:12px;display:flex;gap:8px">
            <button class="btn btn-primary" onclick="createRichMenu()">Create on LINE</button>
            <button class="btn btn-ghost" onclick="document.getElementById('richMenuCreator').style.display='none'">Cancel</button>
          </div>
        </div>
      </div>
      <div style="display:flex;align-items:center;justify-content:space-between;margin:32px 0 12px"><h3 style="font-size:16px;font-weight:600">Flex Message Preview</h3></div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px">
        <div>
          <div class="form-group"><label class="form-label">Type</label><select class="form-input" id="flexType" onchange="updateFlexForm()"><option value="product">Product Card</option><option value="contact">Contact Card</option></select></div>
          <div id="flexForm"></div>
          <button class="btn btn-primary" onclick="previewFlex()" style="margin-top:8px">Generate Preview</button>
        </div>
        <div><div class="form-label">JSON Preview</div><pre class="log-viewer" id="flexPreview" style="min-height:200px;max-height:600px;font-size:11px">{}</pre></div>
      </div>
    </div>
  </div>

  <!-- ═══════ Data Files ═══════ -->
  <div class="page" id="page-data">
    <div class="page-title" style="justify-content:space-between">
      <span data-i18n="page.data">📁 Data Files</span>
      <div>
        <button class="btn btn-ghost btn-sm" onclick="loadDataFiles()" data-i18n="btn.refresh">↻ Refresh</button>
        <button class="btn btn-primary btn-sm" data-admin-only onclick="showNewFileForm()" data-i18n="btn.newFile">+ New File</button>
      </div>
    </div>
    <p style="font-size:12px;color:var(--muted);margin-bottom:16px" data-i18n="data.hint">Knowledge base files for the chatbot. Edit content, then re-ingest to update the vector store.</p>

    <!-- Upload -->
    <div class="upload-zone" id="uploadZone" data-admin-only onclick="document.getElementById('fileUploadInput').click()" style="margin-bottom:16px">
      <input type="file" id="fileUploadInput" accept=".md,.txt,.csv" multiple onchange="handleFileUpload(this.files)">
      <div style="font-size:20px;margin-bottom:6px">📤</div>
      <div data-i18n="data.upload.cta"><strong>Click to upload</strong> or drag files here</div>
      <div style="font-size:11px;margin-top:4px" data-i18n="data.upload.hint">.md, .txt files — UTF-8 only</div>
    </div>

    <!-- New file -->
    <div id="newFileForm" style="display:none;margin-bottom:16px">
      <div class="card" style="padding:16px">
        <h4 style="margin-bottom:10px;font-size:14px" data-i18n="data.newfile">Create New Data File</h4>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px">
          <div class="form-group"><label class="form-label">Folder (optional)</label><input class="form-input" id="newFileFolder" placeholder="e.g. products"></div>
          <div class="form-group"><label class="form-label">Filename</label><input class="form-input" id="newFileName" placeholder="e.g. new_product.md"></div>
        </div>
        <div class="form-group"><label class="form-label">Content</label><div id="newFileEditorWrap"></div></div>
        <div style="display:flex;gap:8px"><button class="btn btn-primary btn-sm" onclick="createDataFile()" data-i18n="btn.create">Create</button><button class="btn btn-ghost btn-sm" onclick="document.getElementById('newFileForm').style.display='none'" data-i18n="btn.cancel">Cancel</button></div>
      </div>
    </div>

    <!-- File list -->
    <div class="tbl-wrap"><table><thead><tr><th data-i18n="th.file">File</th><th data-i18n="th.folder">Folder</th><th data-i18n="th.size">Size</th><th data-i18n="th.actions">Actions</th></tr></thead><tbody id="dataFileRows"></tbody></table></div>

    <!-- Editor -->
    <div id="fileEditor" style="display:none">
      <div class="card" style="padding:20px">
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px">
          <h4 style="font-size:14px" id="editingFileName">Editing: ...</h4>
          <div style="display:flex;gap:8px;align-items:center">
            <div class="view-toggle">
              <button class="tab-btn active" onclick="setEditorMode('rich',this)" data-i18n="view.visual">Visual</button>
              <button class="tab-btn" onclick="setEditorMode('raw',this)" data-i18n="view.markdown">Markdown</button>
            </div>
            <button class="btn btn-ghost btn-sm" onclick="closeEditor()" data-i18n="btn.closeEditor">✕ Close</button>
          </div>
        </div>
        <div id="richEditorWrap"></div>
        <textarea class="form-textarea" id="rawEditorArea" rows="20" style="min-height:400px;font-size:13px;display:none"></textarea>
        <div style="margin-top:12px;display:flex;gap:8px;align-items:center">
          <button class="btn btn-primary" onclick="saveDataFile()">💾 Save</button>
          <span style="font-size:11px;color:var(--muted)">After saving, restart server or run <code style="background:var(--bg3);padding:2px 6px;border-radius:4px">run.bat ingest</code></span>
        </div>
      </div>
    </div>
  </div>

  <!-- ═══════ Logs ═══════ -->
  <div class="page" id="page-logs">
    <div class="page-title" style="justify-content:space-between">
      <span data-i18n="page.logs">📋 Logs</span>
      <div>
        <select class="form-input" id="logLines" style="width:auto;display:inline-block" onchange="loadLogs()">
          <option value="50">Last 50</option><option value="100" selected>Last 100</option><option value="200">Last 200</option><option value="500">Last 500</option>
        </select>
        <button class="btn btn-ghost btn-sm" onclick="loadLogs()">↻ Refresh</button>
      </div>
    </div>
    <div id="logNotConfigured" style="display:none">
      <div class="card" style="padding:24px;text-align:center">
        <div style="font-size:36px;margin-bottom:12px">📝</div>
        <h3 style="margin-bottom:8px" data-i18n="logs.nocfg.title">Log File Not Configured</h3>
        <p style="color:var(--muted);font-size:13px" data-i18n="logs.nocfg.body">Set <code style="background:var(--bg3);padding:2px 6px;border-radius:4px">LOG_FILE=chatbot.log</code> in your .env to enable log viewing.</p>
        <p style="color:var(--muted);font-size:12px;margin-top:8px"><span data-i18n="logs.nocfg.go">Go to</span> <a href="#" onclick="showPage('config',document.querySelector('[data-page=config]'));return false" data-i18n="logs.nocfg.link">Configuration → Environment</a> <span data-i18n="logs.nocfg.set">to set this.</span></p>
      </div>
    </div>
    <div class="log-viewer" id="logViewer" style="display:none">No logs loaded</div>
  </div>

  <!-- ═══════ Users ═══════ -->
  <div class="page" id="page-users">
    <div class="page-title" style="justify-content:space-between">
      <span data-i18n="page.users">👥 Users</span>
      <button class="btn btn-primary btn-sm" onclick="showNewUserForm()" data-i18n="btn.addUser">+ Add User</button>
    </div>

    <!-- New user form -->
    <div id="newUserForm" style="display:none;margin-bottom:16px">
      <div class="card" style="padding:16px">
        <h4 style="margin-bottom:10px;font-size:14px" data-i18n="users.newuser">Create New User</h4>
        <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px">
          <div class="form-group"><label class="form-label" data-i18n="users.username">Username</label><input class="form-input" id="newUserName" placeholder="username" pattern="[a-zA-Z0-9_-]+"></div>
          <div class="form-group"><label class="form-label" data-i18n="users.password">Password</label><input class="form-input" id="newUserPass" type="password" placeholder="min 4 chars"></div>
          <div class="form-group"><label class="form-label" data-i18n="users.role">Role</label><select class="form-input" id="newUserRole"><option value="admin">Admin</option><option value="viewer" selected>Viewer</option></select></div>
        </div>
        <div style="font-size:11px;color:var(--muted);margin-bottom:12px" data-i18n="users.role_hint">Admin: full access, can manage users. Viewer: read-only access to dashboard.</div>
        <div style="display:flex;gap:8px">
          <button class="btn btn-primary btn-sm" onclick="createNewUser()" data-i18n="btn.create">Create</button>
          <button class="btn btn-ghost btn-sm" onclick="document.getElementById('newUserForm').style.display='none'" data-i18n="btn.cancel">Cancel</button>
        </div>
      </div>
    </div>

    <div class="tbl-wrap"><table><thead><tr><th data-i18n="users.username">Username</th><th data-i18n="users.role">Role</th><th data-i18n="users.created_by">Created By</th><th data-i18n="th.actions">Actions</th></tr></thead><tbody id="userRows"></tbody></table></div>
  </div>

  <!-- ═══════ Products ═══════ -->
  <div class="page" id="page-products">
    <div class="page-title" style="justify-content:space-between">
      <span data-i18n="page.products">🛍️ Products</span>
      <div style="display:flex;gap:8px">
        <button class="btn btn-ghost btn-sm" onclick="loadProducts()" data-i18n="btn.refresh">↻ Refresh</button>
        <button class="btn btn-primary btn-sm" data-admin-only onclick="showProductForm(null)">+ Add Product</button>
      </div>
    </div>
    <div class="cards" id="productStats"></div>

    <!-- Add / Edit form -->
    <div id="productForm" style="display:none;margin-bottom:16px">
      <div class="card" style="padding:20px">
        <h4 style="margin-bottom:14px;font-size:14px" id="productFormTitle">Add Product</h4>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
          <div class="form-group"><label class="form-label">Product Name</label><input class="form-input" id="pf_name" placeholder="e.g. Roman Blind Blackout" oninput="autoSlugId()"></div>
          <div class="form-group"><label class="form-label">English Name (optional)</label><input class="form-input" id="pf_name_en" placeholder="e.g. Roman Blind"></div>
          <div class="form-group"><label class="form-label">Category</label><input class="form-input" id="pf_category" list="pf_catlist" placeholder="e.g. Curtains"><datalist id="pf_catlist"></datalist></div>
          <div class="form-group"><label class="form-label">Price</label><input class="form-input" id="pf_price" placeholder="e.g. $50 or $50–$100"></div>
          <div class="form-group"><label class="form-label">Image URL (optional)</label><input class="form-input" id="pf_image_url" placeholder="https://..."></div>
          <div class="form-group" style="display:flex;align-items:center;gap:10px;padding-top:20px">
            <label style="display:flex;align-items:center;gap:8px;cursor:pointer;font-size:13px">
              <input type="checkbox" id="pf_in_stock" checked style="width:18px;height:18px;accent-color:var(--accent)">
              In Stock
            </label>
          </div>
          <div class="form-group" style="grid-column:1/-1"><label class="form-label">Description (shown to bot &amp; customers)</label><textarea class="form-textarea" id="pf_description" rows="3" style="min-height:70px"></textarea></div>
          <div class="form-group" style="grid-column:1/-1"><label class="form-label">ID (auto-generated)</label><input class="form-input" id="pf_id" placeholder="auto-generated-from-name" style="opacity:0.6;font-family:monospace;font-size:12px"></div>
        </div>
        <div style="margin-top:16px;display:flex;gap:8px">
          <button class="btn btn-primary" onclick="saveProduct()">Save Product</button>
          <button class="btn btn-ghost" onclick="document.getElementById('productForm').style.display='none'">Cancel</button>
        </div>
      </div>
    </div>

    <div class="tbl-wrap"><table><thead><tr><th>ID</th><th data-i18n="th.name">Name</th><th data-i18n="th.category">Category</th><th data-i18n="th.price">Price</th><th data-i18n="th.image">Image</th><th data-i18n="th.status">Status</th><th data-i18n="th.actions">Actions</th></tr></thead><tbody id="productRows"></tbody></table></div>
  </div>

  <!-- ═══════ Contacts / Messages ═══════ -->
  <div class="page" id="page-contacts">
    <div class="page-title" style="justify-content:space-between">
      <span data-i18n="page.contacts">📧 Messages</span>
      <button class="btn btn-ghost btn-sm" onclick="loadContacts()" data-i18n="btn.refresh">↻ Refresh</button>
    </div>
    <div class="cards" id="contactStats"></div>
    <div class="tbl-wrap"><table><thead><tr><th data-i18n="th.channel">Channel</th><th data-i18n="th.name">Name</th><th>Contact</th><th data-i18n="th.message">Message</th><th data-i18n="th.time">Time</th><th data-i18n="th.status">Status</th><th data-i18n="th.actions">Actions</th></tr></thead><tbody id="contactRows"></tbody></table></div>
  </div>

  <!-- ═══════ Handoff ═══════ -->
  <div class="page" id="page-handoff">
    <div class="page-title" style="justify-content:space-between">
      <span data-i18n="page.handoff">🤝 Live Handoff</span>
      <button class="btn btn-ghost btn-sm" onclick="loadHandoffs()" data-i18n="btn.refresh">↻ Refresh</button>
    </div>
    <div class="tbl-wrap"><table><thead><tr><th data-i18n="th.session_id">Session</th><th data-i18n="th.channel">Channel</th><th>Reason</th><th data-i18n="th.messages">Messages</th><th data-i18n="th.time">Since</th><th data-i18n="th.actions">Actions</th></tr></thead><tbody id="handoffRows"></tbody></table></div>
    <div id="handoffReplyBox" style="display:none;margin-top:16px">
      <div class="card" style="padding:16px">
        <h4 style="margin-bottom:10px;font-size:14px">Reply to session: <span id="handoffReplyTarget"></span></h4>
        <div id="handoffMsgHistory" style="max-height:250px;overflow-y:auto;border:1px solid var(--border);border-radius:8px;padding:12px;margin-bottom:12px;background:var(--bg)"></div>
        <div class="form-group"><textarea class="form-textarea" id="handoffReplyText" rows="3" placeholder="Type your reply..."></textarea></div>
        <div style="display:flex;gap:8px">
          <button class="btn btn-primary btn-sm" onclick="sendHandoffReply()">Send Reply</button>
          <button class="btn btn-danger btn-sm" onclick="resolveCurrentHandoff()">Resolve &amp; Return to Bot</button>
          <button class="btn btn-ghost btn-sm" onclick="document.getElementById('handoffReplyBox').style.display='none'">Cancel</button>
        </div>
      </div>
    </div>
  </div>

  <!-- ═══════ Fallback / Unanswered ═══════ -->
  <div class="page" id="page-fallback">
    <div class="page-title" style="justify-content:space-between">
      <span data-i18n="page.fallback">❓ Unanswered Questions</span>
      <button class="btn btn-ghost btn-sm" onclick="loadFallbacks()" data-i18n="btn.refresh">↻ Refresh</button>
    </div>
    <div class="cards" id="fallbackStats"></div>
    <div class="tbl-wrap"><table><thead><tr><th data-i18n="th.question">Question</th><th>Answer Given</th><th data-i18n="th.session_id">Session</th><th data-i18n="th.time">Time</th><th data-i18n="th.status">Status</th><th data-i18n="th.actions">Actions</th></tr></thead><tbody id="fallbackRows"></tbody></table></div>
  </div>

</div>

<div class="toast" id="toast"></div>

<!-- Onboarding -->
<div class="onb-overlay" id="onbOverlay" style="display:none"></div>
<div class="onb-card" id="onbCard" style="display:none">
  <div class="onb-lang" id="onbLang"></div>
  <div class="onb-icon" id="onbIcon"></div>
  <div class="onb-title" id="onbTitle"></div>
  <div class="onb-body" id="onbBody"></div>
  <div class="onb-dots" id="onbDots"></div>
  <div class="onb-btns" id="onbBtns"></div>
</div>"""

# ══════════════════════════════════════════════════════════════════════
# JS  (the placeholder __LANGS_JSON__ is replaced at render time)
# ══════════════════════════════════════════════════════════════════════
_JS = r"""(function(){
"use strict";

// ── i18n ─────────────────────────────────────────────────────────────
var LANGS=__LANGS_JSON__;
var _lang='en';
function t(k){return(LANGS[_lang]&&LANGS[_lang][k])||LANGS.en[k]||k}
window.setLang=function(code){
  if(!LANGS[code])return;_lang=code;
  localStorage.setItem('admin_lang',code);
  document.documentElement.dir=code==='he'?'rtl':'ltr';
  document.documentElement.lang=code;
  document.querySelectorAll('.lang-btn').forEach(function(b){b.classList.toggle('active',b.dataset.lang===code)});
  document.querySelectorAll('[data-i18n]').forEach(function(el){
    var v=t(el.dataset.i18n);if(v!==undefined)el.innerHTML=v;
  });
  // Re-render cached dynamic content so translated strings apply immediately
  if(_lastOverviewData)renderOverview(_lastOverviewData);
  if(_lastBudgetData)renderBudget(_lastBudgetData);
  // Re-render config forms if data is cached
  if(cfgCache.client){buildClientForm(cfgCache.client);buildPersonalityForm(cfgCache.personality)}
  // Re-render env form
  if(cfgCache.env)buildEnvForm(cfgCache.env);
  var onbCard=document.getElementById('onbCard');
  if(onbCard&&onbCard.style.display!=='none')renderOnbStep();
};
function initLang(){setLang(localStorage.getItem('admin_lang')||'en')}

// ── Onboarding ────────────────────────────────────────────────────────
var _onbStep=0,_onbHighlight=null;
var ONB_STEPS=[
  {icon:'🚀',titleK:'onb.welcome',bodyK:'onb.welcome_sub',page:null},
  {icon:'📁',titleK:'onb.step1_title',bodyK:'onb.step1_body',page:'data'},
  {icon:'🏢',titleK:'onb.step2_title',bodyK:'onb.step2_body',page:'config',configTab:'client'},
  {icon:'🤖',titleK:'onb.step3_title',bodyK:'onb.step3_body',page:'config',configTab:'personality'},
  {icon:'📊',titleK:'onb.step4_title',bodyK:'onb.step4_body',page:'overview'},
];
function showOnboarding(){
  document.getElementById('onbOverlay').style.display='block';
  document.getElementById('onbCard').style.display='block';
  _onbStep=0;renderOnbStep();
}
function renderOnbStep(){
  var s=ONB_STEPS[_onbStep],total=ONB_STEPS.length;
  // navigate to the real page for this step
  if(s.page){var nb=document.querySelector('[data-page='+s.page+']');if(nb)showPage(s.page,nb)}
  else if(_onbStep===0){var ob=document.querySelector('[data-page=overview]');if(ob)showPage('overview',ob)}
  // switch config tab if specified
  if(s.configTab){var tabBtn=document.querySelector('[data-i18n="cfg.tab.'+s.configTab+'"]');if(tabBtn)showConfigTab(s.configTab,tabBtn)}
  // highlight the relevant nav item
  if(_onbHighlight){_onbHighlight.classList.remove('onb-highlight');_onbHighlight=null}
  if(s.page){var ni=document.querySelector('[data-page='+s.page+']');if(ni){ni.classList.add('onb-highlight');_onbHighlight=ni}}
  // content
  document.getElementById('onbIcon').textContent=s.icon;
  document.getElementById('onbTitle').textContent=s.titleK?t(s.titleK):'';
  document.getElementById('onbBody').textContent=s.bodyK?t(s.bodyK):'';
  // lang buttons
  var lh='';['en','th','he'].forEach(function(c){lh+='<button class="'+(c===_lang?'active':'')+'" onclick="onbLangSwitch(\''+c+'\')">'+c.toUpperCase()+'</button>'});
  document.getElementById('onbLang').innerHTML=lh;
  // dots
  var dh='';for(var i=0;i<total;i++)dh+='<div class="onb-dot'+(_onbStep===i?' active':'')+'" style="cursor:pointer" onclick="onbGo('+i+')"></div>';
  document.getElementById('onbDots').innerHTML=dh;
  // buttons — left (Skip/Back) always + right (Next/Done) always, positions never shift
  var bh='';
  if(_onbStep===0)bh+='<button class="btn btn-ghost btn-sm" onclick="window.closeOnboarding()">'+t('onb.skip')+'</button>';
  else bh+='<button class="btn btn-ghost btn-sm" onclick="window.onbPrev()">← '+t('onb.prev')+'</button>';
  if(_onbStep<total-1)bh+='<button class="btn btn-primary btn-sm" onclick="window.onbNext()">'+t('onb.next')+' →</button>';
  else bh+='<button class="btn btn-primary btn-sm" onclick="window.closeOnboarding()">'+t('onb.done')+' ✔</button>';
  document.getElementById('onbBtns').innerHTML=bh;
}
window.onbLangSwitch=function(code){setLang(code);renderOnbStep()};
window.onbNext=function(){if(_onbStep<ONB_STEPS.length-1){_onbStep++;renderOnbStep()}};
window.onbPrev=function(){if(_onbStep>0){_onbStep--;renderOnbStep()}};
window.onbGo=function(i){_onbStep=i;renderOnbStep()};
window.closeOnboarding=function(){
  document.getElementById('onbOverlay').style.display='none';
  document.getElementById('onbCard').style.display='none';
  if(_onbHighlight){_onbHighlight.classList.remove('onb-highlight');_onbHighlight=null}
  localStorage.setItem('admin_onboarded','1');
  showPage('overview',document.querySelector('[data-page=overview]'));
};

var KEY='',TOKEN='',ROLE='',USERNAME='',BASE=window.location.origin+'/admin/api';

// ── Auth ──────────────────────────────────────────────────────────────
window.tryLogin=async function(){
  var u=document.getElementById('loginUser').value.trim();
  var p=document.getElementById('loginPass').value;
  if(!u||!p){document.getElementById('authErr').textContent='Username and password required';document.getElementById('authErr').style.display='block';return}
  try{
    var r=await fetch(BASE+'/auth/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username:u,password:p})});
    if(!r.ok){var e=await r.json().catch(function(){return{detail:'Login failed'}});throw new Error(e.detail||'Error '+r.status)}
    var d=await r.json();
    TOKEN=d.token;ROLE=d.role;USERNAME=d.username;KEY='';
    document.getElementById('auth').style.display='none';
    document.getElementById('sidebar').style.display='flex';
    document.getElementById('mainContent').style.display='block';
    applyRole();
    initLang();
    var ov=await api('/overview');renderOverview(ov);
    loadConfig().catch(function(){});
    if(!localStorage.getItem('admin_onboarded'))showOnboarding();
  }catch(e){document.getElementById('authErr').textContent=e.message||'Authentication failed';document.getElementById('authErr').style.display='block';TOKEN='';ROLE='';USERNAME=''}
};
document.getElementById('loginUser').addEventListener('keydown',function(e){if(e.key==='Enter')document.getElementById('loginPass').focus()});
document.getElementById('loginPass').addEventListener('keydown',function(e){if(e.key==='Enter')tryLogin()});

window.doLogout=async function(){
  try{await fetch(BASE+'/auth/logout',{method:'POST',headers:{'X-Auth-Token':TOKEN}})}catch(e){}
  TOKEN='';ROLE='';USERNAME='';KEY='';
  document.getElementById('auth').style.display='flex';
  document.getElementById('sidebar').style.display='none';
  document.getElementById('mainContent').style.display='none';
  document.getElementById('loginUser').value='';document.getElementById('loginPass').value='';
  document.getElementById('authErr').style.display='none';
};

function applyRole(){
  // Show user info in sidebar
  document.getElementById('sidebarUser').style.display='block';
  document.getElementById('sidebarUsername').textContent=USERNAME;
  document.getElementById('sidebarRole').textContent=ROLE;
  // Show Users nav only for admin
  var isAdmin=ROLE==='admin';
  document.getElementById('navUsers').style.display=isAdmin?'flex':'none';
  document.getElementById('navSectionAdmin').style.display=isAdmin?'block':'none';
  // Hide write buttons for viewers
  document.querySelectorAll('[data-admin-only]').forEach(function(el){el.style.display=isAdmin?'':'none'});
}

// ── API ───────────────────────────────────────────────────────────────
async function api(path,opts){
  opts=opts||{};
  var headers={};
  if(TOKEN)headers['X-Auth-Token']=TOKEN;
  else if(KEY)headers['X-Admin-Key']=KEY;
  if(opts.body&&!opts.raw)headers['Content-Type']='application/json';
  var fo={method:opts.method||'GET',headers:headers};
  if(opts.body)fo.body=opts.raw?opts.body:JSON.stringify(opts.body);
  var r=await fetch(BASE+path,fo);
  if(!r.ok){var e=await r.json().catch(function(){return{detail:'Request failed'}});throw new Error(e.detail||'Error '+r.status)}
  return r.json();
}
async function apiUpload(path,fd){
  var headers={};
  if(TOKEN)headers['X-Auth-Token']=TOKEN;
  else if(KEY)headers['X-Admin-Key']=KEY;
  var r=await fetch(BASE+path,{method:'POST',headers:headers,body:fd});
  if(!r.ok){var e=await r.json().catch(function(){return{detail:'Upload failed'}});throw new Error(e.detail||'Error '+r.status)}
  return r.json();
}

// ── Nav ───────────────────────────────────────────────────────────────
window.showPage=function(id,btn){
  document.querySelectorAll('.page').forEach(function(p){p.classList.remove('active')});
  document.querySelectorAll('.nav-item').forEach(function(n){n.classList.remove('active')});
  document.getElementById('page-'+id).classList.add('active');
  if(btn)btn.classList.add('active');
  var loaders={overview:loadOverviewData,sessions:loadSessions,budget:loadBudget,config:loadConfig,line:loadLine,data:loadDataFiles,logs:loadLogs,users:loadUsers,products:loadProducts,contacts:loadContacts,handoff:loadHandoffs,fallback:loadFallbacks};
  if(loaders[id])loaders[id]();
};

// ── Overview ──────────────────────────────────────────────────────────
var _lastOverviewData=null;
async function loadOverviewData(){try{renderOverview(await api('/overview'))}catch(e){toast(e.message,'err')}}
function renderOverview(d){
  _lastOverviewData=d;
  var b=d.budget||{};
  var html=card(t('ov.status'),d.status==='running'?t('ov.running'):t('ov.down'),'')+card(t('ov.uptime'),d.uptime,'')+card(t('ov.model'),d.model,d.provider)+card(t('ov.sessions'),d.sessions.active,d.sessions.backend)+card(t('ov.tokens'),b.tokens_used?b.tokens_used.toLocaleString():'0','of '+(b.daily_token_cap||0).toLocaleString())+card(t('ov.usd'),'$'+(b.usd_used||0).toFixed(4),'of $'+(b.daily_usd_cap||0).toFixed(2))+card(t('ov.ip'),d.rate_limiting.active_ip_buckets,d.rate_limiting.ip_per_minute+'/min')+card(t('ov.spam'),d.spam_detection.active_trackers,d.spam_detection.max_strikes+' strikes');
  document.getElementById('overviewCards').innerHTML=html;
  var ch=d.channels,cr='';['web','whatsapp','telegram','line'].forEach(function(c){cr+='<tr><td style="text-transform:capitalize">'+c+'</td><td>'+(ch[c]?'<span class="tag tag-on">ON</span>':'<span class="tag tag-off">OFF</span>')+'</td></tr>'});
  document.getElementById('channelRows').innerHTML=cr;
  var sec=d.security,sr='';
  sr+='<tr><td>'+t('sec.rate')+'</td><td>'+(d.rate_limiting.enabled?'<span class="tag tag-on">ON</span>':'<span class="tag tag-off">OFF</span>')+'</td></tr>';
  sr+='<tr><td>'+t('sec.spam')+'</td><td>'+(d.spam_detection.enabled?'<span class="tag tag-on">ON</span>':'<span class="tag tag-off">OFF</span>')+'</td></tr>';
  sr+='<tr><td>'+t('sec.budget')+'</td><td>'+(b.enabled?'<span class="tag tag-on">ON</span>':'<span class="tag tag-off">OFF</span>')+'</td></tr>';
  sr+='<tr><td>'+t('sec.hsts')+'</td><td>'+(sec.hsts_enabled?'<span class="tag tag-on">ON</span>':'<span class="tag tag-off">OFF</span>')+'</td></tr>';
  sr+='<tr><td>'+t('sec.cors')+'</td><td>'+(sec.strict_cors?'<span class="tag tag-on">ON</span>':'<span class="tag tag-off">OFF</span>')+'</td></tr>';
  sr+='<tr><td>'+t('sec.apikey')+'</td><td>'+(sec.api_key_set?'<span class="tag tag-on">SET</span>':'<span class="tag tag-off">NOT SET</span>')+'</td></tr>';
  document.getElementById('securityRows').innerHTML=sr;
}
function card(l,v,s){return'<div class="card"><div class="card-label">'+l+'</div><div class="card-value">'+v+'</div>'+(s?'<div class="card-sub">'+s+'</div>':'')+'</div>'}

// ── Sessions ──────────────────────────────────────────────────────────
window.loadSessions=async function(){
  try{var d=await api('/sessions');var html='';
  if(!d.sessions.length)html='<tr><td colspan="4" style="text-align:center;color:var(--muted)">No sessions</td></tr>';
  d.sessions.forEach(function(s){var ts=s.last_activity?new Date(s.last_activity).toLocaleString():'—';html+='<tr><td style="font-family:monospace;font-size:12px">'+esc(s.session_id)+'</td><td>'+s.message_count+'</td><td>'+ts+'</td><td><button class="btn btn-ghost btn-sm" onclick="viewSession(\''+esc(s.session_id)+'\')">View</button> <button class="btn btn-primary btn-sm" data-admin-only onclick="startHandoffFromSession(\''+esc(s.session_id)+'\')">🤝 Take Over</button> <button class="btn btn-danger btn-sm" onclick="deleteSession(\''+esc(s.session_id)+'\')">Delete</button></td></tr>'});
  document.getElementById('sessionRows').innerHTML=html}catch(e){toast(e.message,'err')}
};
window.startHandoffFromSession=async function(sid){
  if(!confirm('Take over session '+sid+'? The bot will be silenced and you can reply directly.'))return;
  var channel='web';
  if(sid.startsWith('line:'))channel='line';
  else if(sid.startsWith('telegram:'))channel='telegram';
  else if(sid.startsWith('whatsapp:'))channel='whatsapp';
  try{await api('/handoff/'+encodeURIComponent(sid)+'/start',{method:'POST',body:{channel:channel,reason:'admin_takeover'}});toast('Handoff started — go to Handoff page to reply','ok');loadSessions()}catch(e){toast(e.message,'err')}
};
window.viewSession=async function(id){try{var d=await api('/sessions/'+encodeURIComponent(id));var html='<div class="modal-bg" onclick="if(event.target===this)this.remove()"><div class="modal"><div class="modal-head"><h3>Session: '+esc(id.slice(0,20))+(id.length>20?'…':'')+'</h3><button class="btn btn-ghost btn-sm" onclick="this.closest(\'.modal-bg\').remove()">&times;</button></div><div class="modal-body">';if(!d.messages.length)html+='<p style="color:var(--muted)">No messages</p>';d.messages.forEach(function(m){var role=m.role||m.type||'unknown';html+='<div class="msg-row '+(role==='human'?'human':'ai')+'"><div class="msg-role">'+role+'</div><div class="msg-text">'+esc(m.content||m.text||'')+'</div></div>'});html+='</div></div></div>';document.body.insertAdjacentHTML('beforeend',html)}catch(e){toast(e.message,'err')}};
window.deleteSession=async function(id){if(!confirm('Delete session '+id+'?'))return;try{await api('/sessions/'+encodeURIComponent(id),{method:'DELETE'});toast('Session deleted','ok');loadSessions()}catch(e){toast(e.message,'err')}};
window.clearAllSessions=async function(){if(!confirm('Clear ALL sessions?'))return;try{var d=await api('/sessions',{method:'DELETE'});toast('Cleared '+d.cleared+' sessions','ok');loadSessions()}catch(e){toast(e.message,'err')}};

// ── Budget ────────────────────────────────────────────────────────────
var _lastBudgetData=null;
var _budgetHistoryFilter=30;
function renderBudget(d){
  _lastBudgetData=d;
  var hist=d.history||[];
  var tc=d.daily_token_cap||0,uc=d.daily_usd_cap||0;
  var tp=tc?Math.min(100,Math.round(d.tokens_used/tc*100)):0;
  var up=uc?Math.min(100,Math.round(d.usd_used/uc*100)):0;

  // ── Summary totals ──
  var sum7=hist.filter(function(r){return daysDiff(r.day,d.day)<=6;});
  var sum30=hist.filter(function(r){return daysDiff(r.day,d.day)<=29;});
  var usd7=sum7.reduce(function(a,r){return a+r.usd;},0);
  var usd30=sum30.reduce(function(a,r){return a+r.usd;},0);
  var tok7=sum7.reduce(function(a,r){return a+r.tokens;},0);
  var tok30=sum30.reduce(function(a,r){return a+r.tokens;},0);

  document.getElementById('budgetCards').innerHTML=
    card(t('bud.today'),'$'+d.usd_used.toFixed(4),'📅 '+d.day)+
    card(t('bud.last7'),'$'+usd7.toFixed(4),tok7.toLocaleString()+' '+t('bud.tokens_unit'))+
    card(t('bud.last30'),'$'+usd30.toFixed(4),tok30.toLocaleString()+' '+t('bud.tokens_unit'))+
    card(t('bud.model'),d.model,d.enabled?'<span class="tag tag-on">'+t('bud.budget_on')+'</span>':'<span class="tag tag-off">'+t('bud.no_cap')+'</span>');

  // ── Today progress bars ──
  var bars='';
  if(tc||uc){
    if(tc)bars+='<div class="card" style="margin-bottom:12px"><div class="card-label">'+t('bud.token_usage_today')+' ('+tp+'%) — '+d.tokens_used.toLocaleString()+' / '+tc.toLocaleString()+'</div><div class="progress"><div class="progress-fill" style="width:'+tp+'%;background:'+(tp>80?'var(--danger)':tp>50?'var(--warn)':'var(--success)')+'"></div></div></div>';
    if(uc)bars+='<div class="card" style="margin-bottom:12px"><div class="card-label">'+t('bud.usd_usage_today')+' ('+up+'%) — $'+d.usd_used.toFixed(4)+' / $'+uc.toFixed(2)+'</div><div class="progress"><div class="progress-fill" style="width:'+up+'%;background:'+(up>80?'var(--danger)':up>50?'var(--warn)':'var(--success)')+'"></div></div></div>';
  }
  document.getElementById('budgetBars').innerHTML=bars;

  // ── Bar chart ──
  if(hist.length){
    document.getElementById('budgetChartWrap').style.display='';
    var chartDays=hist.slice(0,30);
    var maxUsd=Math.max.apply(null,chartDays.map(function(r){return r.usd;}));
    if(maxUsd===0)maxUsd=1;
    var chartHtml='';
    chartDays.slice().reverse().forEach(function(row){
      var pct=Math.max(2,Math.round(row.usd/maxUsd*100));
      var isToday=row.day===d.day;
      var col=isToday?'var(--accent)':'var(--bg3)';
      var label=row.day.slice(5); // MM-DD
      var safeDay=esc(row.day);
      var safeLabel=esc(label);
      chartHtml+='<div title="'+safeDay+': $'+row.usd.toFixed(4)+'" style="flex:1;min-width:12px;max-width:28px;display:flex;flex-direction:column;align-items:center;gap:3px">'
        +'<div style="width:100%;background:'+col+';border-radius:3px 3px 0 0;height:'+pct+'px;min-height:2px;transition:height .3s"></div>'
        +'<div style="font-size:9px;color:var(--muted);white-space:nowrap;transform:rotate(-45deg);transform-origin:top center;margin-top:4px">'+safeLabel+'</div>'
        +'</div>';
    });
    document.getElementById('budgetChart').innerHTML=chartHtml;
    document.getElementById('budgetChartLegend').innerHTML=
      '<span style="display:inline-flex;align-items:center;gap:4px"><span style="width:10px;height:10px;background:var(--accent);border-radius:2px;display:inline-block"></span>'+t('bud.today')+'</span>'
      +'<span style="display:inline-flex;align-items:center;gap:4px"><span style="width:10px;height:10px;background:var(--bg3);border-radius:2px;display:inline-block"></span>'+t('bud.prev_days')+'</span>';
  }

  // ── History table ──
  if(hist.length){
    document.getElementById('budgetHistoryWrap').style.display='';
    _renderBudgetHistoryTable(d,hist,_budgetHistoryFilter);
  }
}

function daysDiff(dayStr,todayStr){
  try{return Math.round((new Date(todayStr)-new Date(dayStr))/(1000*60*60*24));}catch(e){return 999;}
}

function _renderBudgetHistoryTable(d,hist,n){
  var rows=n?hist.filter(function(r){return daysDiff(r.day,d.day)<n;}):hist;
  var uc=d.daily_usd_cap||0;
  var html='';
  var totalUsd=0,totalTok=0;
  rows.forEach(function(row){
    var isToday=row.day===d.day;
    var capPct=uc?Math.round(row.usd/uc*100):'-';
    var capCls=typeof capPct==='number'?(capPct>80?'color:var(--danger)':capPct>50?'color:var(--warn)':'color:var(--success)'):'color:var(--muted)';
    totalUsd+=row.usd; totalTok+=row.tokens;
    html+='<tr'+(isToday?' style="font-weight:600"':'')+'>'
      +'<td>'+esc(String(row.day))+(isToday?' <span class="tag tag-on" style="font-size:10px">'+t('bud.today')+'</span>':'')+'</td>'
      +'<td>'+row.tokens.toLocaleString()+'</td>'
      +'<td>$'+row.usd.toFixed(4)+'</td>'
      +'<td style="'+capCls+'">'+(typeof capPct==='number'?capPct+'%':'-')+'</td>'
      +'</tr>';
  });
  if(!html)html='<tr><td colspan="4" style="text-align:center;color:var(--muted)">'+t('bud.no_data_period')+'</td></tr>';
  document.getElementById('budgetHistoryRows').innerHTML=html;
  document.getElementById('budgetHistoryTotal').textContent=t('bud.history_total')+': $'+totalUsd.toFixed(4)+' across '+rows.length+' day(s), '+totalTok.toLocaleString()+' '+t('bud.tokens_unit');
  // active button state
  ['bh7','bh30','bhAll'].forEach(function(id){if(document.getElementById(id))document.getElementById(id).classList.remove('active')});
  var active=n===7?'bh7':n===30?'bh30':'bhAll';
  if(document.getElementById(active))document.getElementById(active).classList.add('active');
}

window.filterBudgetHistory=function(n,btn){
  _budgetHistoryFilter=n;
  if(_lastBudgetData)_renderBudgetHistoryTable(_lastBudgetData,_lastBudgetData.history||[],n);
};
async function loadBudget(){try{var d=await api('/budget');renderBudget(d)}catch(e){toast(e.message,'err')}}
window.resetBudget=async function(){if(!confirm('Reset budget?'))return;try{await api('/budget/reset',{method:'POST'});toast('Budget reset','ok');loadBudget()}catch(e){toast(e.message,'err')}};

// ══════════════════════════════════════════════════════════════════════
// Configuration
// ══════════════════════════════════════════════════════════════════════
var cfgCache={};
async function loadConfig(){try{var d=await api('/config');cfgCache=d;buildEnvForm(d.env);document.getElementById('clientFile').textContent=d.client_file;document.getElementById('personalityFile').textContent=d.personality_file;document.getElementById('clientYaml').value=yamlStringify(d.client);document.getElementById('personalityYaml').value=yamlStringify(d.personality);buildClientForm(d.client);buildPersonalityForm(d.personality)}catch(e){toast(e.message,'err')}}

var ENV_GROUPS=[
  {label:'cfg.llm',keys:['LLM_PROVIDER','LLM_MODEL','LLM_TEMPERATURE']},
  {label:'cfg.rag',keys:['EMBEDDING_MODEL','CHUNK_SIZE','CHUNK_OVERLAP','RETRIEVAL_K']},
  {label:'cfg.conversation',keys:['MAX_HISTORY_TURNS','MAX_MESSAGE_CHARS']},
  {label:'cfg.rate',keys:['RATE_LIMIT_ENABLED','RATE_LIMIT_IP_PER_MINUTE','RATE_LIMIT_IP_BURST','RATE_LIMIT_SESSION_PER_MINUTE','RATE_LIMIT_SESSION_BURST']},
  {label:'cfg.spam',keys:['SPAM_DETECTION_ENABLED','SPAM_MAX_STRIKES','SPAM_COOLDOWN_SECONDS']},
  {label:'cfg.budget_cap',keys:['DAILY_TOKEN_CAP','DAILY_USD_CAP']},
  {label:'cfg.security',keys:['API_CORS_ORIGINS','API_STRICT_CORS','API_HSTS_ENABLED']},
  {label:'cfg.general',keys:['ACTIVE_CLIENT','LOG_LEVEL','DEBUG']}
];

// Fields that admins should not edit from the dashboard (require .env change)
var LOCKED_KEYS={LLM_PROVIDER:true,EMBEDDING_MODEL:true,CHUNK_SIZE:true,CHUNK_OVERLAP:true,RETRIEVAL_K:true};

// Recommended chatbot models shown in the LLM_MODEL dropdown
var MODEL_OPTIONS=[
  {v:'gpt-4o-mini',l:'gpt-4o-mini — fast & cheap (recommended)'},
  {v:'gpt-4o',l:'gpt-4o — smartest, higher cost'},
  {v:'gpt-4-turbo',l:'gpt-4-turbo — fast, mid cost'},
  {v:'gpt-3.5-turbo',l:'gpt-3.5-turbo — cheapest'},
  {v:'claude-3-5-sonnet-20241022',l:'Claude 3.5 Sonnet'},
  {v:'claude-3-haiku-20240307',l:'Claude 3 Haiku — fast & cheap'},
];

function buildEnvForm(env){
  var html='';
  ENV_GROUPS.forEach(function(g){
    html+='<div class="cfg-card"><h4>'+t(g.label)+'</h4><div class="cfg-grid">';
    g.keys.forEach(function(k){var v=env[k];if(v===undefined)return;
      var locked=LOCKED_KEYS[k];
      if(typeof v==='boolean'){html+='<div class="form-group"><label class="form-label">'+k+'</label><label style="display:flex;align-items:center;gap:8px;cursor:pointer"><input type="checkbox" data-env="'+k+'" '+(v?'checked':'')+(locked?' disabled':'')+' style="width:18px;height:18px;accent-color:var(--accent)"><span style="font-size:13px">'+t(v?'cfg.enabled':'cfg.disabled')+'</span></label>'+(locked?'<span style="font-size:10px;color:var(--muted)">🔒</span>':'')+'</div>'}
      else if(k==='LLM_MODEL'){
        html+='<div class="form-group"><label class="form-label">'+k+'</label><select class="form-input" data-env="'+k+'" style="cursor:pointer">';
        var found=false;MODEL_OPTIONS.forEach(function(o){var sel=String(v)===o.v;if(sel)found=true;html+='<option value="'+esc(o.v)+'"'+(sel?' selected':'')+'>'+esc(o.l)+'</option>'});
        if(!found)html+='<option value="'+esc(String(v))+'" selected>'+esc(String(v))+' (custom)</option>';
        html+='</select></div>';
      }
      else{html+='<div class="form-group"><label class="form-label">'+k+(locked?' 🔒':'')+'</label><input class="form-input" data-env="'+k+'" value="'+esc(String(v))+'"'+(locked?' readonly style="opacity:.6;cursor:not-allowed"':'')+'></div>'}
    });html+='</div></div>';
  });
  var secrets=Object.keys(env).filter(function(k){return k.startsWith('_')&&k.endsWith('_SET')});
  if(secrets.length){html+='<div class="cfg-card"><h4>'+t('cfg.secrets')+'</h4><div class="cfg-grid">';secrets.forEach(function(k){var label=k.replace(/^_/,'').replace(/_SET$/,'');html+='<div class="form-group"><label class="form-label">'+label+'</label>'+(env[k]?'<span class="tag tag-on">SET</span>':'<span class="tag tag-off">NOT SET</span>')+'</div>'});html+='</div></div>'}
  document.getElementById('envForm').innerHTML=html;
}

// ── Config validation ────────────────────────────────────────────────
// Returns an error message string, or null if the object looks safe to save.
function validateCfg(type, obj){
  if(!obj||typeof obj!=='object'||Array.isArray(obj)||!Object.keys(obj).length)
    return 'Cannot save — config is empty or was wiped.';
  var req={client:['id','name'],personality:['name','system_prompt'],env:['LLM_MODEL']};
  var missing=(req[type]||[]).filter(function(k){return obj[k]===undefined||obj[k]===null||String(obj[k]).trim()===''});
  if(missing.length)return 'Required fields are missing or blank: '+missing.join(', ');
  return null;
}

window.saveEnv=async function(){var body={};document.querySelectorAll('[data-env]').forEach(function(el){if(el.disabled||el.readOnly)return;body[el.dataset.env]=el.type==='checkbox'?el.checked:el.tagName==='SELECT'?el.value:el.value});var err=validateCfg('env',body);if(err){toast(err,'warn');return}try{var r=await api('/config/env',{method:'PUT',body:body});var msg='Settings saved.';if(r.rejected&&Object.keys(r.rejected).length)msg+=' Rejected: '+Object.keys(r.rejected).join(', ');toast(msg,'ok')}catch(e){toast(e.message,'err')}};

window.showConfigTab=function(tab,btn){
  document.querySelectorAll('#page-config .config-panel').forEach(function(p){p.style.display='none'});
  document.querySelectorAll('#page-config > .tab-bar .tab-btn').forEach(function(b){b.classList.remove('active')});
  document.getElementById('cfg-'+tab).style.display='block';btn.classList.add('active');
};

// ── Client Form ───────────────────────────────────────────────────────
function buildClientForm(d){
  if(!d)return;var h='';
  h+='<div class="cfg-card"><h4>'+t('cf.basic')+'</h4><div class="cfg-grid">';
  h+=ff('cl','id',d.id,t('cf.client_id'));h+=ff('cl','name',d.name,t('cf.display_name'));
  h+=ff('cl','location',d.location,t('cf.location'));h+=ff('cl','timezone',d.timezone,t('cf.timezone'));
  h+=ff('cl','personality',d.personality,t('cf.personality'));h+='</div></div>';
  h+='<div class="cfg-card"><h4>'+t('cf.languages')+'</h4><div class="cfg-grid">';
  h+=ff('cl','language_primary',d.language_primary,t('cf.lang_primary'));
  h+=ff('cl','language_fallback',d.language_fallback,t('cf.lang_fallback'));
  h+='</div><div class="form-group" style="margin-top:8px"><label class="form-label">'+t('cf.langs_offered')+'</label><input class="form-input" data-cl="languages_offered" value="'+esc((d.languages_offered||[]).join(', '))+'"></div></div>';
  h+='<div class="cfg-card"><h4>'+t('cf.prompt_extra')+'</h4><p style="font-size:11px;color:var(--muted);margin-bottom:8px">'+t('cf.prompt_extra_hint')+'</p><div class="form-group"><textarea class="field-multiline" data-cl="system_prompt_extra" rows="8" style="min-height:150px;font-family:system-ui">'+esc(d.system_prompt_extra||'')+'</textarea></div></div>';
  if(d.greeting_override!==undefined){h+='<div class="cfg-card"><h4>'+t('cf.greeting_override')+'</h4><div class="form-group"><textarea class="field-multiline" data-cl="greeting_override" rows="3">'+esc(d.greeting_override||'')+'</textarea></div></div>'}
  if(d.data_paths){h+='<div class="cfg-card"><h4>'+t('cf.data_paths')+'</h4><div class="form-group"><label class="form-label">'+t('cf.data_paths_hint')+'</label><input class="form-input" data-cl="data_paths" value="'+esc((d.data_paths||[]).join(', '))+'"></div></div>'}
  if(d.channels){h+='<div class="cfg-card"><h4>'+t('cf.channels')+'</h4><div class="cfg-grid">';Object.keys(d.channels).forEach(function(ch){var en=d.channels[ch]&&d.channels[ch].enabled;h+='<div class="form-group"><label class="form-label" style="text-transform:capitalize">'+ch+'</label><label style="display:flex;align-items:center;gap:8px;cursor:pointer"><input type="checkbox" data-cl-ch="'+ch+'" '+(en?'checked':'')+' style="width:18px;height:18px;accent-color:var(--accent)"><span style="font-size:13px">'+t(en?'cfg.enabled':'cfg.disabled')+'</span></label></div>'});h+='</div></div>'}
  document.getElementById('clientFormFields').innerHTML=h;
}

window.saveClientForm=async function(){
  var d={};document.querySelectorAll('[data-cl]').forEach(function(el){var k=el.dataset.cl;if(k==='languages_offered'||k==='data_paths')d[k]=el.value.split(',').map(function(s){return s.trim()}).filter(Boolean);else d[k]=el.value});
  var ch={};document.querySelectorAll('[data-cl-ch]').forEach(function(el){ch[el.dataset.clCh]={enabled:el.checked}});if(Object.keys(ch).length)d.channels=ch;
  var err=validateCfg('client',d);if(err){toast(err,'warn');return}
  try{await api('/config/client',{method:'PUT',body:d});toast('Client config saved','ok')}catch(e){toast(e.message,'err')}
};
window.setClientView=function(v,btn){document.getElementById('clientFormView').style.display=v==='form'?'block':'none';document.getElementById('clientYamlView').style.display=v==='yaml'?'block':'none';btn.parentElement.querySelectorAll('.tab-btn').forEach(function(b){b.classList.remove('active')});btn.classList.add('active')};

// ── Personality Form ──────────────────────────────────────────────────
function buildPersonalityForm(d){
  if(!d)return;var h='';
  h+='<div class="cfg-card"><h4>'+t('pf.basic')+'</h4><div class="cfg-grid">';
  h+=ff('pers','name',d.name,t('pf.name'));h+=ff('pers','temperature',d.temperature||0.7,t('pf.temperature'));
  h+='</div></div>';
  h+='<div class="cfg-card"><h4>'+t('pf.description')+'</h4><div class="form-group"><textarea class="field-multiline" data-pers="description" rows="3">'+esc(d.description||'')+'</textarea></div></div>';
  h+='<div class="cfg-card"><h4>'+t('pf.system_prompt')+'</h4><p style="font-size:11px;color:var(--muted);margin-bottom:8px">'+t('pf.system_prompt_hint')+'</p><div class="form-group"><textarea class="field-multiline" data-pers="system_prompt" rows="12" style="min-height:200px;font-family:system-ui">'+esc(d.system_prompt||'')+'</textarea></div></div>';
  h+='<div class="cfg-card"><h4>'+t('pf.messages')+'</h4><div class="cfg-grid">';
  h+='<div class="form-group"><label class="form-label">'+t('pf.greeting')+'</label><textarea class="field-multiline" data-pers="greeting" rows="2" style="min-height:60px">'+esc(d.greeting||'')+'</textarea></div>';
  h+='<div class="form-group"><label class="form-label">'+t('pf.fallback')+'</label><textarea class="field-multiline" data-pers="fallback_message" rows="2" style="min-height:60px">'+esc(d.fallback_message||'')+'</textarea></div>';
  h+='</div></div>';
  h+='<div class="cfg-card"><h4>'+t('pf.style_kw')+'</h4><div class="form-group"><label class="form-label">'+t('pf.style_kw_hint')+'</label><input class="form-input" data-pers="style_keywords" value="'+esc((d.style_keywords||[]).join(', '))+'"></div></div>';
  document.getElementById('personalityFormFields').innerHTML=h;
}

window.savePersonalityForm=async function(){
  var d={};document.querySelectorAll('[data-pers]').forEach(function(el){var k=el.dataset.pers;if(k==='style_keywords')d[k]=el.value.split(',').map(function(s){return s.trim()}).filter(Boolean);else if(k==='temperature')d[k]=parseFloat(el.value)||0.7;else d[k]=el.value});
  var err=validateCfg('personality',d);if(err){toast(err,'warn');return}
  try{await api('/config/personality',{method:'PUT',body:d});toast('Personality config saved','ok')}catch(e){toast(e.message,'err')}
};
window.setPersonalityView=function(v,btn){document.getElementById('personalityFormView').style.display=v==='form'?'block':'none';document.getElementById('personalityYamlView').style.display=v==='yaml'?'block':'none';btn.parentElement.querySelectorAll('.tab-btn').forEach(function(b){b.classList.remove('active')});btn.classList.add('active')};

window.saveYaml=async function(type){var text=document.getElementById(type==='client'?'clientYaml':'personalityYaml').value;if(!text||!text.trim()){toast('Cannot save — YAML textarea is empty.','warn');return}var body;try{body=yamlParse(text)}catch(e){toast('Invalid YAML: '+e.message,'err');return}var err=validateCfg(type,body);if(err){toast(err,'warn');return}try{await api('/config/'+type,{method:'PUT',body:body});toast(type+' config saved','ok');loadConfig()}catch(e){toast(e.message,'err')}};

function ff(prefix,key,value,label){return'<div class="form-group"><label class="form-label">'+label+'</label><input class="form-input" data-'+prefix+'="'+key+'" value="'+esc(String(value||''))+'"></div>'}

// ══════════════════════════════════════════════════════════════════════
// Rich Text Editor
// ══════════════════════════════════════════════════════════════════════
function createRichEditor(containerId){
  var c=document.getElementById(containerId);if(!c)return;
  var eid=containerId+'_ed';
  c.innerHTML='<div class="editor-toolbar">'
    +'<button onclick="eCmd(\''+eid+'\',\'bold\')" title="Bold"><b>B</b></button>'
    +'<button onclick="eCmd(\''+eid+'\',\'italic\')" title="Italic"><i>I</i></button>'
    +'<div class="sep"></div>'
    +'<button onclick="eBlock(\''+eid+'\',\'h1\')" title="Heading 1">H1</button>'
    +'<button onclick="eBlock(\''+eid+'\',\'h2\')" title="Heading 2">H2</button>'
    +'<button onclick="eBlock(\''+eid+'\',\'h3\')" title="Heading 3">H3</button>'
    +'<div class="sep"></div>'
    +'<button onclick="eCmd(\''+eid+'\',\'insertUnorderedList\')" title="Bullet List">• List</button>'
    +'<button onclick="eCmd(\''+eid+'\',\'insertOrderedList\')" title="Numbered List">1. List</button>'
    +'<div class="sep"></div>'
    +'<button onclick="eCmd(\''+eid+'\',\'formatBlock\',\'blockquote\')" title="Quote">❝</button>'
    +'<button onclick="eCmd(\''+eid+'\',\'insertHorizontalRule\')" title="Divider">—</button>'
    +'<div class="sep"></div>'
    +'<button onclick="emojiPick(\''+eid+'\',event)" title="Emoji">😊</button>'
    +'</div>'
    +'<div class="rich-editor" id="'+eid+'" contenteditable="true"></div>';
  return eid;
}
window.eCmd=function(id,cmd,val){document.getElementById(id).focus();document.execCommand(cmd,false,val||null)};
window.eBlock=function(id,tag){document.getElementById(id).focus();document.execCommand('formatBlock',false,'<'+tag+'>')};

// Specialty emoji categories keyed by client id or personality name.
// Add a new key here whenever a new client type is added to the project.
var SPECIALTY_CATS={
  cannabis: {l:'🍃 Cannabis',e:['💨','🌿','🍃','🌱','☘️','🌾','🪴','♨️','🫧','🌫️','💚','🔥','🕯️','🪔','🧪','⚗️','💊','🌡️']},
  limmes:   {l:'🎨 Design',e:['🪑','🛋️','🖼️','🏠','🎨','🪞','🪟','🛏️','💡','🌈','✏️','📐','📏','🖌️','🪆','🏮','🪴','🎭']},
  clinic:   {l:'🏥 Health',e:['🏥','💊','🩺','🩹','💉','🧬','🔬','🩻','❤️','🫀','🫁','🧠','🦷','👁️','🩸','🌡️','⚕️','💆']},
  default:  {l:'⭐ Featured',e:['⭐','🏆','🎖️','💎','🌟','✨','💫','🎯','🎪','🎭','🎨','🎬','🎤','🎵','🎶','🎁','🎉','🏅']},
};
// Returns the 5 universal categories with the correct specialty category
// (slot 3) driven by the currently loaded client config.
function getEmojiCats(){
  var id=(cfgCache.client&&cfgCache.client.id)||'';
  var pers=(cfgCache.client&&cfgCache.client.personality)||'';
  var key='default';
  if(SPECIALTY_CATS[id])key=id;
  else if(id.indexOf('cannabis')>=0||pers.indexOf('budtender')>=0||pers.indexOf('cannabis')>=0)key='cannabis';
  else if(id.indexOf('limmes')>=0||pers.indexOf('design')>=0)key='limmes';
  else if(pers.indexOf('clinic')>=0||pers.indexOf('health')>=0)key='clinic';
  return [
    {l:'⚡ Quick',e:['✅','❌','⚠️','🔥','💡','⭐','👍','❤️','🎉','💯','✨','🌟','💫','🎯','📌','🔑']},
    {l:'🌿 Nature',e:['🌿','🍃','🌱','☘️','🍀','🌾','🌸','🌺','🌻','🌼','💐','🌲','🌳','🌴','🪴','🎋','🌵','🎍']},
    SPECIALTY_CATS[key],
    {l:'😊 People',e:['😊','😄','😎','🤗','😍','🥰','😌','🤙','👋','🤝','👏','💪','🙏','👌','🫶','💚','💜','🧡','💛','💙']},
    {l:'🏪 Business',e:['🛒','🏪','🏠','🏢','🏬','📦','🚚','💰','💳','🎁','💼','📋','📍','🗺️','🏅','🏷️','📊','🔒']},
    {l:'⏰ Time & Info',e:['🕑','🕐','⏰','📅','📆','🗓️','🔔','📢','ℹ️','💬','📱','✉️','📞','☎️','📣','📝','🔍']},
  ];
}
window.emojiPick=function(editorId,ev){
  var old=document.querySelector('.emoji-picker');if(old)old.remove();
  var p=document.createElement('div');p.className='emoji-picker';
  getEmojiCats().forEach(function(cat){
    var lbl=document.createElement('span');lbl.className='emoji-cat-label';lbl.textContent=cat.l;p.appendChild(lbl);
    var grid=document.createElement('div');grid.className='emoji-grid';
    cat.e.forEach(function(e){var b=document.createElement('button');b.textContent=e;b.title=e;b.onclick=function(){document.getElementById(editorId).focus();document.execCommand('insertText',false,e);p.remove()};grid.appendChild(b)});
    p.appendChild(grid);
  });
  var rect=ev.target.getBoundingClientRect();
  var ptop=rect.bottom+4;if(ptop+428>window.innerHeight)ptop=rect.top-432;
  p.style.top=Math.max(8,ptop)+'px';p.style.left=Math.max(8,Math.min(rect.left,window.innerWidth-348))+'px';
  document.body.appendChild(p);setTimeout(function(){document.addEventListener('click',function h(ev2){if(!p.contains(ev2.target)){p.remove();document.removeEventListener('click',h)}})},0);
};

function html2md(html){
  var t=document.createElement('div');t.innerHTML=html;
  function w(n){
    if(n.nodeType===3)return n.textContent;if(n.nodeType!==1)return'';
    var tag=n.tagName.toLowerCase(),ch='';for(var i=0;i<n.childNodes.length;i++)ch+=w(n.childNodes[i]);
    switch(tag){
      case'h1':return'# '+ch.trim()+'\n\n';case'h2':return'## '+ch.trim()+'\n\n';case'h3':return'### '+ch.trim()+'\n\n';
      case'b':case'strong':return'**'+ch+'**';case'i':case'em':return'*'+ch+'*';
      case'ul':return ch+'\n';case'ol':return ch+'\n';
      case'li':var pa=n.parentElement;if(pa&&pa.tagName.toLowerCase()==='ol'){var idx=1;for(var s=n;s.previousElementSibling;s=s.previousElementSibling)idx++;return idx+'. '+ch.trim()+'\n'}return'- '+ch.trim()+'\n';
      case'blockquote':return'> '+ch.trim().replace(/\n/g,'\n> ')+'\n\n';case'hr':return'\n---\n\n';case'br':return'\n';case'p':return ch.trim()+'\n\n';case'div':return ch.trim()+'\n\n';default:return ch;
    }
  }
  return w(t).replace(/\n{3,}/g,'\n\n').trim();
}

function md2html(md){
  if(!md)return'';var lines=md.split('\n'),html='',inList=false,lt='';
  for(var i=0;i<lines.length;i++){var L=lines[i];
    if(L.match(/^### /)){cl();html+='<h3>'+inf(L.slice(4))+'</h3>';continue}
    if(L.match(/^## /)){cl();html+='<h2>'+inf(L.slice(3))+'</h2>';continue}
    if(L.match(/^# /)){cl();html+='<h1>'+inf(L.slice(2))+'</h1>';continue}
    if(L.match(/^---+$/)){cl();html+='<hr>';continue}
    if(L.match(/^> /)){html+='<blockquote>'+inf(L.slice(2))+'</blockquote>';continue}
    if(L.match(/^[-*] /)){if(!inList||lt!=='ul'){cl();html+='<ul>';inList=true;lt='ul'}html+='<li>'+inf(L.slice(2))+'</li>';continue}
    var om=L.match(/^(\d+)\. /);if(om){if(!inList||lt!=='ol'){cl();html+='<ol>';inList=true;lt='ol'}html+='<li>'+inf(L.slice(om[0].length))+'</li>';continue}
    if(inList&&L.trim()===''){cl();continue}if(L.trim()==='')continue;
    html+='<p>'+inf(L)+'</p>';
  }
  cl();return html;
  function cl(){if(inList){html+='</'+lt+'>';inList=false}}
}
function inf(t){return t.replace(/\*\*(.+?)\*\*/g,'<strong>$1</strong>').replace(/\*(.+?)\*/g,'<em>$1</em>')}

// ══════════════════════════════════════════════════════════════════════
// Data Files
// ══════════════════════════════════════════════════════════════════════
var _editFile='',_edMode='rich',_mainEd='',_newEd='';

window.loadDataFiles=async function(){
  try{var d=await api('/data');var html='';
  if(!d.files.length)html='<tr><td colspan="4" style="text-align:center;color:var(--muted)">No data files. Create or upload one above.</td></tr>';
  d.files.forEach(function(f){html+='<tr><td style="font-family:monospace;font-size:12px">'+esc(f.name)+'</td><td>'+esc(f.folder||'—')+'</td><td>'+(f.size>1024?(f.size/1024).toFixed(1)+' KB':f.size+' B')+'</td><td><button class="btn btn-ghost btn-sm" onclick="editDataFile(\''+esc(f.path)+'\')">✏️ Edit</button> <button class="btn btn-danger btn-sm" onclick="removeDataFile(\''+esc(f.path)+'\')">🗑️</button></td></tr>'});
  document.getElementById('dataFileRows').innerHTML=html}catch(e){toast(e.message,'err')}
};

window.editDataFile=async function(path){
  try{var d=await api('/data/'+encodeURIComponent(path));_editFile=path;
  document.getElementById('editingFileName').textContent=t('cf.editing')+': '+path;
  _mainEd=createRichEditor('richEditorWrap');document.getElementById(_mainEd).innerHTML=md2html(d.content);
  document.getElementById('rawEditorArea').value=d.content;_edMode='rich';
  document.getElementById('richEditorWrap').style.display='block';document.getElementById('rawEditorArea').style.display='none';
  document.getElementById('fileEditor').style.display='block';document.getElementById('fileEditor').scrollIntoView({behavior:'smooth'})}catch(e){toast(e.message,'err')}
};

window.setEditorMode=function(m,btn){
  _edMode=m;btn.parentElement.querySelectorAll('.tab-btn').forEach(function(b){b.classList.remove('active')});btn.classList.add('active');
  if(m==='rich'){document.getElementById(_mainEd).innerHTML=md2html(document.getElementById('rawEditorArea').value);document.getElementById('richEditorWrap').style.display='block';document.getElementById('rawEditorArea').style.display='none'}
  else{document.getElementById('rawEditorArea').value=html2md(document.getElementById(_mainEd).innerHTML);document.getElementById('richEditorWrap').style.display='none';document.getElementById('rawEditorArea').style.display='block'}
};

window.closeEditor=function(){document.getElementById('fileEditor').style.display='none';_editFile=''};

window.saveDataFile=async function(){if(!_editFile)return;var c=_edMode==='rich'?html2md(document.getElementById(_mainEd).innerHTML):document.getElementById('rawEditorArea').value;try{var r=await api('/data/'+encodeURIComponent(_editFile),{method:'PUT',body:{content:c}});toast('Saved! '+r.note,'ok');loadDataFiles()}catch(e){toast(e.message,'err')}};

window.showNewFileForm=function(){document.getElementById('newFileForm').style.display='block';_newEd=createRichEditor('newFileEditorWrap')};

window.createDataFile=async function(){var folder=document.getElementById('newFileFolder').value.trim(),name=document.getElementById('newFileName').value.trim();if(!name){toast('Filename required','err');return}var path=folder?(folder+'/'+name):name;var content=html2md(document.getElementById(_newEd).innerHTML);try{await api('/data',{method:'POST',body:{path:path,content:content}});toast('File created: '+path,'ok');document.getElementById('newFileForm').style.display='none';document.getElementById('newFileFolder').value='';document.getElementById('newFileName').value='';loadDataFiles()}catch(e){toast(e.message,'err')}};

window.removeDataFile=async function(path){if(!confirm('Delete '+path+'?'))return;try{await api('/data/'+encodeURIComponent(path),{method:'DELETE'});toast('Deleted','ok');closeEditor();loadDataFiles()}catch(e){toast(e.message,'err')}};

// ── Upload ────────────────────────────────────────────────────────────
var uz=document.getElementById('uploadZone');
if(uz){uz.addEventListener('dragover',function(e){e.preventDefault();this.classList.add('dragover')});uz.addEventListener('dragleave',function(){this.classList.remove('dragover')});uz.addEventListener('drop',function(e){e.preventDefault();this.classList.remove('dragover');if(e.dataTransfer.files.length)handleFileUpload(e.dataTransfer.files)})}

window.handleFileUpload=async function(files){
  for(var i=0;i<files.length;i++){var f=files[i];var fd=new FormData();fd.append('file',f);fd.append('folder','');
  try{var r=await apiUpload('/data/upload',fd);toast('Uploaded: '+r.uploaded,'ok')}catch(e){toast(f.name+': '+e.message,'err')}}
  loadDataFiles();document.getElementById('fileUploadInput').value='';
};

// ══════════════════════════════════════════════════════════════════════
// Logs
// ══════════════════════════════════════════════════════════════════════
window.loadLogs=async function(){
  try{var d=await api('/logs?lines='+document.getElementById('logLines').value);
  if(d.lines&&d.lines.length){document.getElementById('logNotConfigured').style.display='none';document.getElementById('logViewer').style.display='block';document.getElementById('logViewer').textContent=d.lines.join('');document.getElementById('logViewer').scrollTop=999999}
  else if(d.note){document.getElementById('logNotConfigured').style.display='block';document.getElementById('logViewer').style.display='none';
    var p=document.getElementById('logNotConfigured').querySelector('[data-i18n="logs.nocfg.body"]');if(p)p.textContent=d.note;}
  else{document.getElementById('logNotConfigured').style.display='none';document.getElementById('logViewer').style.display='block';document.getElementById('logViewer').textContent=d.error||'No logs'}}catch(e){toast(e.message,'err')}
};

// ══════════════════════════════════════════════════════════════════════
// Channel status helper (reusable for LINE / Telegram / WhatsApp / …)
// ══════════════════════════════════════════════════════════════════════
// Renders the "not configured" / "configured + status cards" pattern.
// cfg = {
//   rootId       : 'line-channel-root',   — container element id
//   toolsId      : 'lineTools',           — channel-specific tools div (shown when configured)
//   name         : 'LINE',                — display name
//   icon         : '📱',                  — icon for the not-configured card
//   nocfgTitleK  : 'line.nocfg.title',    — i18n key for title
//   nocfgBodyK   : 'line.nocfg.body',     — i18n key for body
//   envVars      : ['LINE_CHANNEL_ACCESS_TOKEN','LINE_CHANNEL_SECRET'],
//   statusCards  : function(data){ return card(...) + card(...); }  — returns card HTML
// }
function renderChannelStatus(cfg, data){
  var root=document.getElementById(cfg.rootId);if(!root)return;
  if(!data||!data.configured){
    var envHtml=cfg.envVars.map(function(v){return'<code style="background:var(--bg3);padding:2px 6px;border-radius:4px">'+esc(v)+'</code>'}).join(' and ');
    root.innerHTML='<div class="card" style="padding:24px;text-align:center">'
      +'<div style="font-size:36px;margin-bottom:12px">'+cfg.icon+'</div>'
      +'<h3 style="margin-bottom:8px">'+t(cfg.nocfgTitleK)+'</h3>'
      +'<p style="color:var(--muted);font-size:13px;margin-bottom:16px">'+t(cfg.nocfgBodyK)+'</p>'
      +'<p style="color:var(--muted);font-size:12px">Go to <a href="#" onclick="showPage(\'config\',document.querySelector(\'[data-page=config]\'));return false">Configuration</a> to set these.</p></div>';
    if(cfg.toolsId)document.getElementById(cfg.toolsId).style.display='none';
    return false;
  }
  root.innerHTML='<div class="cards">'+cfg.statusCards(data)+'</div>';
  if(cfg.toolsId)document.getElementById(cfg.toolsId).style.display='block';
  return true;
}

// ══════════════════════════════════════════════════════════════════════
// LINE
// ══════════════════════════════════════════════════════════════════════
var _lineCfg={
  rootId:'line-channel-root', toolsId:'lineTools', name:'LINE', icon:'📱',
  nocfgTitleK:'line.nocfg.title', nocfgBodyK:'line.nocfg.body',
  envVars:['LINE_CHANNEL_ACCESS_TOKEN','LINE_CHANNEL_SECRET'],
  statusCards:function(s){
    return card('LINE','\u{1F7E2} Active','')+card('Secret',s.channel_secret_set?'✅ Set':'❌ Missing','')+card('Token','✅ Set','')+card('Webhook',esc(s.webhook_url),'');
  }
};
async function loadLine(){
  try{var s=await api('/line/status');
  if(renderChannelStatus(_lineCfg,s))loadLineMenus();
  }catch(e){toast(e.message,'err')}
  updateFlexForm();
}
window.loadLineMenus=async function(){try{var d=await api('/line/rich-menus');if(!d.menus||!d.menus.length){document.getElementById('richMenuList').innerHTML='<div class="card" style="padding:16px;text-align:center;color:var(--muted)">No rich menus</div>';return}var html='<div class="tbl-wrap"><table><thead><tr><th>Name</th><th>Chat Bar</th><th>Areas</th><th>Default</th><th>Actions</th></tr></thead><tbody>';d.menus.forEach(function(m){var isd=m.richMenuId===d.default_id;html+='<tr><td>'+esc(m.name)+'</td><td>'+esc(m.chatBarText||'')+'</td><td>'+((m.areas||[]).length)+'</td><td>'+(isd?'<span class="tag tag-on">DEFAULT</span>':'<button class="btn btn-ghost btn-sm" onclick="setDefaultMenu(\''+m.richMenuId+'\')">Set Default</button>')+'</td><td><button class="btn btn-danger btn-sm" onclick="deleteRichMenu(\''+m.richMenuId+'\')">Delete</button></td></tr>'});html+='</tbody></table></div>';document.getElementById('richMenuList').innerHTML=html}catch(e){document.getElementById('richMenuList').innerHTML='<div class="card" style="padding:16px;color:var(--danger)">'+esc(e.message)+'</div>'}};
window.showRichMenuCreator=function(){document.getElementById('richMenuCreator').style.display='block';updateRMFields()};
window.updateRMFields=function(){var layout=document.getElementById('rmLayout').value;var count=layout==='2col'?2:layout==='3col'?3:6;var dl=['Products','Contact Us','Hours','Curtains','Sofas','Wallpapers'],dt=['Show products','Contact details','Opening hours','About curtains','About sofas','About wallpapers'];if(count===3){dl=['Products','Hours','Contact'];dt=['Show products','Opening hours','Contact details']}else if(count===6){dl=['Curtains','Sofas','Wallpapers','Poufs','Hours','Contact'];dt=['Tell me about curtains','Tell me about sofas','Tell me about wallpapers','Tell me about poufs','Opening hours','Contact details']}var html='<div style="margin-top:12px"><div class="form-label">Areas ('+count+')</div><div style="display:grid;grid-template-columns:1fr 1fr;gap:8px">';for(var i=0;i<count;i++){html+='<div class="card" style="padding:10px"><div class="form-group" style="margin-bottom:6px"><label class="form-label">Label '+(i+1)+'</label><input class="form-input rm-label" value="'+esc(dl[i]||'')+'"></div><div class="form-group" style="margin-bottom:0"><label class="form-label">Message Text</label><input class="form-input rm-text" value="'+esc(dt[i]||'')+'"></div></div>'}html+='</div></div>';document.getElementById('rmAreasForm').innerHTML=html};
window.createRichMenu=async function(){var labels=[],texts=[];document.querySelectorAll('.rm-label').forEach(function(el){labels.push(el.value)});document.querySelectorAll('.rm-text').forEach(function(el){texts.push(el.value)});try{var r=await api('/line/rich-menus',{method:'POST',body:{layout:document.getElementById('rmLayout').value,name:document.getElementById('rmName').value,chat_bar_text:document.getElementById('rmChatBar').value,labels:labels,texts:texts}});toast('Rich Menu created: '+r.menu_id,'ok');document.getElementById('richMenuCreator').style.display='none';loadLineMenus()}catch(e){toast(e.message,'err')}};
window.setDefaultMenu=async function(id){try{await api('/line/rich-menus/'+id+'/default',{method:'POST'});toast('Set as default','ok');loadLineMenus()}catch(e){toast(e.message,'err')}};
window.deleteRichMenu=async function(id){if(!confirm('Delete this rich menu?'))return;try{await api('/line/rich-menus/'+id,{method:'DELETE'});toast('Deleted','ok');loadLineMenus()}catch(e){toast(e.message,'err')}};
window.updateFlexForm=function(){var type=document.getElementById('flexType').value;var html='';if(type==='product'){html+='<div class="form-group"><label class="form-label">Title</label><input class="form-input" id="fxTitle" value="Roman Curtain"></div><div class="form-group"><label class="form-label">Description</label><input class="form-input" id="fxDesc" value="Custom made, premium fabric"></div><div class="form-group"><label class="form-label">Price</label><input class="form-input" id="fxPrice" value="₪440 – ₪550"></div><div class="form-group"><label class="form-label">Image URL</label><input class="form-input" id="fxImage" placeholder="https://..."></div><div class="form-group"><label class="form-label">Button Label</label><input class="form-input" id="fxBtnLabel" value="Learn more"></div><div class="form-group"><label class="form-label">Button URL</label><input class="form-input" id="fxBtnUri" placeholder="https://..."></div>'}else{html+='<div class="form-group"><label class="form-label">Business Name</label><input class="form-input" id="fxBizName" value="Limmes Studio"></div><div class="form-group"><label class="form-label">Phone</label><input class="form-input" id="fxPhone" value="+972-54-123-4567"></div><div class="form-group"><label class="form-label">WhatsApp</label><input class="form-input" id="fxWhatsApp" value="+972-54-123-4567"></div><div class="form-group"><label class="form-label">Email</label><input class="form-input" id="fxEmail" value="info@limmes.co.il"></div><div class="form-group"><label class="form-label">Address</label><input class="form-input" id="fxAddress" value="Nes Ziona, Israel"></div>'}document.getElementById('flexForm').innerHTML=html};
window.previewFlex=async function(){var type=document.getElementById('flexType').value;var body={type:type};if(type==='product'){body.title=document.getElementById('fxTitle').value;body.description=document.getElementById('fxDesc').value;body.price=document.getElementById('fxPrice').value;body.image_url=document.getElementById('fxImage').value||undefined;body.action_label=document.getElementById('fxBtnLabel').value;body.action_uri=document.getElementById('fxBtnUri').value||undefined}else{body.business_name=document.getElementById('fxBizName').value;body.phone=document.getElementById('fxPhone').value;body.whatsapp=document.getElementById('fxWhatsApp').value;body.email=document.getElementById('fxEmail').value;body.address=document.getElementById('fxAddress').value}try{var r=await api('/line/flex-preview',{method:'POST',body:body});document.getElementById('flexPreview').textContent=JSON.stringify(r.flex,null,2)}catch(e){toast(e.message,'err')}};

// ══════════════════════════════════════════════════════════════════════
// Users
// ══════════════════════════════════════════════════════════════════════
window.loadUsers=async function(){
  if(ROLE!=='admin'){document.getElementById('userRows').innerHTML='<tr><td colspan="4" style="text-align:center;color:var(--muted)">Admin access required</td></tr>';return}
  try{var d=await api('/users');var html='';
  if(!d.users.length)html='<tr><td colspan="4" style="text-align:center;color:var(--muted)">No users</td></tr>';
  d.users.forEach(function(u){html+='<tr><td style="font-weight:600">'+esc(u.username)+'</td><td><span class="tag '+(u.role==='admin'?'tag-on':'tag-off')+'">'+esc(u.role)+'</span></td><td>'+esc(u.created_by||'—')+'</td><td>'+(u.username!==USERNAME?'<button class="btn btn-danger btn-sm" onclick="removeUser(\''+esc(u.username)+'\')">Delete</button>':'<span style="font-size:11px;color:var(--muted)">You</span>')+'</td></tr>'});
  document.getElementById('userRows').innerHTML=html}catch(e){toast(e.message,'err')}
};

window.showNewUserForm=function(){document.getElementById('newUserForm').style.display='block'};

window.createNewUser=async function(){
  var u=document.getElementById('newUserName').value.trim();
  var p=document.getElementById('newUserPass').value;
  var r=document.getElementById('newUserRole').value;
  if(!u||!p){toast('Username and password required','err');return}
  if(p.length<4){toast('Password must be at least 4 characters','err');return}
  try{await api('/users',{method:'POST',body:{username:u,password:p,role:r}});toast('User created: '+u,'ok');document.getElementById('newUserForm').style.display='none';document.getElementById('newUserName').value='';document.getElementById('newUserPass').value='';loadUsers()}catch(e){toast(e.message,'err')}
};

window.removeUser=async function(u){if(!confirm('Delete user '+u+'?'))return;try{await api('/users/'+encodeURIComponent(u),{method:'DELETE'});toast('User deleted','ok');loadUsers()}catch(e){toast(e.message,'err')}};

// ══════════════════════════════════════════════════════════════════════
// Utils
// ══════════════════════════════════════════════════════════════════════
function toast(msg,type){var t=document.getElementById('toast');t.textContent=msg;t.className='toast toast-'+(type||'ok')+' show';clearTimeout(t._tid);t._tid=setTimeout(function(){t.classList.remove('show')},3500)}
function esc(s){var d=document.createElement('div');d.textContent=s;return d.innerHTML}

function yamlStringify(obj,indent){
  if(!obj)return'';indent=indent||0;var pad='  '.repeat(indent),lines=[];
  Object.keys(obj).forEach(function(k){var v=obj[k];
    if(v&&typeof v==='object'&&!Array.isArray(v)){lines.push(pad+k+':');lines.push(yamlStringify(v,indent+1))}
    else if(Array.isArray(v)){lines.push(pad+k+':');v.forEach(function(item){lines.push(pad+'  - '+(typeof item==='object'?JSON.stringify(item):item))})}
    else if(typeof v==='string'&&v.indexOf('\n')>=0){lines.push(pad+k+': |');v.split('\n').forEach(function(l){lines.push(pad+'  '+l)})}
    else{lines.push(pad+k+': '+JSON.stringify(v))}
  });return lines.join('\n');
}

function yamlParse(text){
  try{return JSON.parse(text)}catch(e){}
  var result={},stack=[{obj:result,indent:-1}],pm=null,mi=0,lines=text.split('\n');
  for(var i=0;i<lines.length;i++){var line=lines[i],stripped=line.replace(/\s+$/,'');
    if(pm!==null){var ci=line.match(/^(\s*)/)[1].length;if(ci>mi||stripped===''){pm.val+=line.slice(mi+2)+'\n';continue}else{pm.parent[pm.key]=pm.val.replace(/\n+$/,'\n');pm=null}}
    if(!stripped||stripped.match(/^\s*#/))continue;
    var indent=line.match(/^(\s*)/)[1].length;var m=stripped.match(/^(\s*)([^:]+):\s*(.*)?$/);if(!m)continue;
    var key=m[2].trim(),val=(m[3]||'').trim();
    while(stack.length>1&&stack[stack.length-1].indent>=indent)stack.pop();
    var parent=stack[stack.length-1].obj;
    if(val==='|'){pm={parent:parent,key:key,val:''};mi=indent;continue}
    if(!val){parent[key]={};stack.push({obj:parent[key],indent:indent})}
    else if(val.startsWith('[')){try{parent[key]=JSON.parse(val)}catch(e2){parent[key]=val}}
    else if(val==='true')parent[key]=true;else if(val==='false')parent[key]=false;else if(val==='null')parent[key]=null;
    else if(!isNaN(Number(val))&&val!=='')parent[key]=Number(val);
    else parent[key]=val.replace(/^["']|["']$/g,'');
  }
  if(pm)pm.parent[pm.key]=pm.val.replace(/\n+$/,'\n');
  return result;
}

// ── Products ──────────────────────────────────────────────────────────
var _productCache=[];
async function loadProducts(){
  try{
    var d=await api('/products');
    _productCache=d.products||[];
    var cats=d.categories||[];
    var dl=document.getElementById('pf_catlist');
    if(dl){dl.innerHTML='';cats.forEach(function(c){var o=document.createElement('option');o.value=c;dl.appendChild(o)});}
    var inStock=_productCache.filter(function(p){return p.in_stock;}).length;
    document.getElementById('productStats').innerHTML=
      '<div class="card"><div class="card-label">'+t('products.total')+'</div><div class="card-value">'+d.total+'</div></div>'
      +'<div class="card"><div class="card-label">'+t('products.categories')+'</div><div class="card-value">'+cats.length+'</div></div>'
      +'<div class="card"><div class="card-label">In Stock</div><div class="card-value" style="color:var(--success)">'+inStock+'</div></div>'
      +'<div class="card"><div class="card-label">Out of Stock</div><div class="card-value" style="color:var(--danger)">'+(d.total-inStock)+'</div></div>';
    _renderProductRows();
  }catch(e){toast(e.message,'err')}
}
function _renderProductRows(){
  var rows=document.getElementById('productRows');
  rows.innerHTML='';
  _productCache.forEach(function(p,idx){
    var imgCell=p.image_url?'<img src="'+esc(p.image_url)+'" style="width:40px;height:40px;object-fit:cover;border-radius:6px" onerror="this.style.display=\'none\'">':'<span style="color:var(--muted)">—</span>';
    var stockTag=p.in_stock?'<span class="tag tag-on">In Stock</span>':'<span class="tag tag-off">Out</span>';
    var actions='<button class="btn btn-ghost btn-sm" onclick="showProductForm('+idx+')">Edit</button> '
      +'<button class="btn btn-ghost btn-sm" onclick="toggleStock('+idx+')">'+(!p.in_stock?'✓ In stock':'✕ Out of stock')+'</button> '
      +'<button class="btn btn-danger btn-sm" onclick="deleteProduct('+idx+')">Delete</button>';
    rows.innerHTML+='<tr>'
      +'<td><code style="font-size:11px">'+esc(p.id)+'</code></td>'
      +'<td>'+esc(p.name)+(p.name_en?' <small style="color:var(--muted)">('+esc(p.name_en)+')</small>':'')+'</td>'
      +'<td>'+esc(p.category||'—')+'</td><td>'+esc(p.price||'—')+'</td>'
      +'<td>'+imgCell+'</td><td>'+stockTag+'</td><td>'+actions+'</td></tr>';
  });
  if(!_productCache.length)rows.innerHTML='<tr><td colspan="7" style="text-align:center;color:var(--muted)">No products yet — click "+ Add Product" to start.</td></tr>';
}
var _editingIdx=null;
function slugify(s){return s.toLowerCase().replace(/[^a-z0-9\u0590-\u05ff\u0e00-\u0e7f]+/g,'-').replace(/^-+|-+$/g,'').slice(0,60);}
window.autoSlugId=function(){if(_editingIdx!==null&&_editingIdx>=0)return;var n=document.getElementById('pf_name').value;document.getElementById('pf_id').value=slugify(n);};
window.showProductForm=function(idx){
  _editingIdx=idx;
  var p=(idx!==null&&idx>=0)?_productCache[idx]:null;
  document.getElementById('productFormTitle').textContent=p?'Edit: '+p.name:'Add Product';
  document.getElementById('pf_id').value=p?p.id:'';
  document.getElementById('pf_id').readOnly=!!p;
  document.getElementById('pf_id').style.opacity=p?'0.6':'0.6';
  document.getElementById('pf_name').value=p?p.name:'';
  document.getElementById('pf_name_en').value=p?(p.name_en||''):'';
  document.getElementById('pf_category').value=p?(p.category||''):'';
  document.getElementById('pf_price').value=p?(p.price||''):'';
  document.getElementById('pf_image_url').value=p?(p.image_url||''):'';
  document.getElementById('pf_description').value=p?(p.description||''):'';
  document.getElementById('pf_in_stock').checked=p?p.in_stock:true;
  document.getElementById('productForm').style.display='block';
  document.getElementById('productForm').scrollIntoView({behavior:'smooth',block:'center'});
};
window.saveProduct=async function(){
  var name=document.getElementById('pf_name').value.trim();
  if(!name){toast('Product name is required','err');return;}
  var id=document.getElementById('pf_id').value.trim()||slugify(name);
  if(!id){toast('Could not generate ID — enter a name','err');return;}
  var updated=JSON.parse(JSON.stringify(_productCache));
  var product={id:id,name:name,
    name_en:document.getElementById('pf_name_en').value.trim(),
    category:document.getElementById('pf_category').value.trim(),
    price:document.getElementById('pf_price').value.trim(),
    image_url:document.getElementById('pf_image_url').value.trim(),
    description:document.getElementById('pf_description').value.trim(),
    tags:[],
    in_stock:document.getElementById('pf_in_stock').checked
  };
  if(_editingIdx!==null&&_editingIdx>=0){updated[_editingIdx]=product;}
  else{
    if(updated.some(function(p){return p.id===id;})){toast('A product with this ID already exists','err');return;}
    updated.push(product);
  }
  try{
    await api('/products',{method:'PUT',body:{products:updated}});
    document.getElementById('productForm').style.display='none';
    toast(_editingIdx!==null&&_editingIdx>=0?'Product updated':'Product added','ok');
    await loadProducts();
  }catch(e){toast(e.message,'err')}
};
window.deleteProduct=async function(idx){
  var p=_productCache[idx];
  if(!confirm('Delete "'+p.name+'"?'))return;
  var updated=_productCache.filter(function(_,i){return i!==idx;});
  try{
    await api('/products',{method:'PUT',body:{products:updated}});
    toast('Product deleted','ok');
    await loadProducts();
  }catch(e){toast(e.message,'err')}
};
window.toggleStock=async function(idx){
  var updated=JSON.parse(JSON.stringify(_productCache));
  updated[idx].in_stock=!updated[idx].in_stock;
  try{
    await api('/products',{method:'PUT',body:{products:updated}});
    toast(updated[idx].in_stock?'Marked in stock':'Marked out of stock','ok');
    await loadProducts();
  }catch(e){toast(e.message,'err')}
};
window.loadProducts=loadProducts;

// ── Contacts / Messages ───────────────────────────────────────────────
async function loadContacts(){
  try{
    var d=await api('/contacts');
    var stats=document.getElementById('contactStats');
    stats.innerHTML='<div class="card"><div class="card-label">'+t('contacts.unread')+'</div><div class="card-value" style="color:var(--warn)">'+d.unread+'</div></div>'
      +'<div class="card"><div class="card-label">'+t('contacts.total')+'</div><div class="card-value">'+d.messages.length+'</div></div>';
    var rows=document.getElementById('contactRows');
    rows.innerHTML='';
    (d.messages||[]).forEach(function(m){
      var statusTag=m.replied?'<span class="tag tag-on">Replied</span>':m.read?'<span class="tag" style="background:rgba(245,158,11,.15);color:var(--warn)">Read</span>':'<span class="tag tag-off">Unread</span>';
      var actions='<button class="btn btn-ghost btn-sm" onclick="markContactRead(\''+m.id+'\')">✓ Read</button> <button class="btn btn-ghost btn-sm" onclick="markContactReplied(\''+m.id+'\')">↩ Replied</button> <button class="btn btn-danger btn-sm" onclick="deleteContact(\''+m.id+'\')">✕</button>';
      rows.innerHTML+='<tr><td>'+m.channel+'</td><td>'+m.customer_name+'</td><td style="font-size:12px">'+m.customer_contact+'</td><td style="max-width:200px;white-space:pre-wrap;font-size:12px">'+m.message+'</td><td style="font-size:11px">'+new Date(m.created_at).toLocaleString()+'</td><td>'+statusTag+'</td><td>'+actions+'</td></tr>';
    });
  }catch(e){toast(e.message,'err')}
}
window.loadContacts=loadContacts;
window.markContactRead=async function(id){try{await api('/contacts/'+id+'/read',{method:'PATCH'});loadContacts();toast('Marked read','ok')}catch(e){toast(e.message,'err')}};
window.markContactReplied=async function(id){try{await api('/contacts/'+id+'/replied',{method:'PATCH'});loadContacts();toast('Marked replied','ok')}catch(e){toast(e.message,'err')}};
window.deleteContact=async function(id){if(!confirm('Delete this message?'))return;try{await api('/contacts/'+id,{method:'DELETE'});loadContacts();toast('Deleted','ok')}catch(e){toast(e.message,'err')}};

// ── Handoff ───────────────────────────────────────────────────────────
var _handoffTarget='';
var _handoffPollTimer=null;
var _handoffLastMsgCount=0;
function _stopHandoffPoll(){if(_handoffPollTimer){clearInterval(_handoffPollTimer);_handoffPollTimer=null}}
async function loadHandoffs(){
  try{
    var d=await api('/handoff?active_only=true');
    var rows=document.getElementById('handoffRows');
    rows.innerHTML='';
    (d.sessions||[]).forEach(function(s){
      var msgCount=(s.pending_messages||[]).length;
      var userMsgs=(s.pending_messages||[]).filter(function(m){return m.role==='user'}).length;
      var channelTag='<span class="tag '+(s.channel==='line'?'tag-on':s.channel==='web'?'tag-on':'')+'">'+s.channel+'</span>';
      var reasonTag=s.reason==='user_request'?'<span class="tag" style="background:rgba(59,130,246,.15);color:#3b82f6">User request</span>':'<span class="tag" style="background:rgba(245,158,11,.15);color:var(--warn)">Admin takeover</span>';
      var actions='<button class="btn btn-primary btn-sm" onclick="openHandoffReply(\''+esc(s.session_id)+'\')">💬 Reply</button> <button class="btn btn-danger btn-sm" onclick="resolveHandoff(\''+esc(s.session_id)+'\')">✓ Resolve</button>';
      rows.innerHTML+='<tr><td><code style="font-size:11px">'+esc(s.session_id)+'</code></td><td>'+channelTag+'</td><td>'+reasonTag+'</td><td>'+msgCount+' <span style="color:var(--muted);font-size:11px">('+userMsgs+' from user)</span></td><td style="font-size:11px">'+new Date(s.created_at).toLocaleString()+'</td><td>'+actions+'</td></tr>';
    });
    if(!d.sessions||!d.sessions.length)rows.innerHTML='<tr><td colspan="6" style="text-align:center;color:var(--muted);padding:24px">No active handoffs</td></tr>';
  }catch(e){toast(e.message,'err')}
}
window.loadHandoffs=loadHandoffs;
async function _refreshHandoffMessages(sid){
  try{
    var s=await api('/handoff/'+encodeURIComponent(sid));
    var msgs=s.pending_messages||[];
    if(msgs.length===_handoffLastMsgCount)return;
    _handoffLastMsgCount=msgs.length;
    var historyEl=document.getElementById('handoffMsgHistory');
    if(!historyEl)return;
    var html='';
    msgs.forEach(function(m){
      var cls=m.role==='admin'?'ai':'human';
      var label=m.role==='admin'?'👤 Admin':'💬 User';
      var time=m.at?new Date(m.at).toLocaleTimeString():'';
      html+='<div class="msg-row '+cls+'" style="margin-bottom:6px"><div class="msg-role" style="font-size:11px">'+label+' <span style="color:var(--muted)">'+time+'</span></div><div class="msg-text" style="font-size:13px">'+esc(m.text||'')+'</div></div>';
    });
    if(!html)html='<p style="color:var(--muted);font-size:12px">No messages yet — the user is waiting for your reply.</p>';
    historyEl.innerHTML=html;
    historyEl.scrollTop=historyEl.scrollHeight;
    loadHandoffs();
  }catch(e){}
}
window.openHandoffReply=async function(sid){
  _stopHandoffPoll();
  _handoffTarget=sid;
  _handoffLastMsgCount=0;
  document.getElementById('handoffReplyTarget').textContent=sid;
  document.getElementById('handoffReplyText').value='';
  await _refreshHandoffMessages(sid);
  document.getElementById('handoffReplyBox').style.display='block';
  _handoffPollTimer=setInterval(function(){_refreshHandoffMessages(sid)},3000);
};
window.sendHandoffReply=async function(){
  var text=document.getElementById('handoffReplyText').value.trim();
  if(!text)return;
  try{await api('/handoff/'+encodeURIComponent(_handoffTarget)+'/reply',{method:'POST',body:{text:text}});document.getElementById('handoffReplyText').value='';toast('Reply sent','ok');_handoffLastMsgCount=0;await _refreshHandoffMessages(_handoffTarget);loadHandoffs()}catch(e){toast(e.message,'err')}
};
window.resolveCurrentHandoff=async function(){
  if(!confirm('Resolve this handoff and return session to bot?'))return;
  _stopHandoffPoll();
  try{await api('/handoff/'+encodeURIComponent(_handoffTarget)+'/resolve',{method:'POST'});document.getElementById('handoffReplyBox').style.display='none';toast('Handoff resolved — bot is back in control','ok');loadHandoffs()}catch(e){toast(e.message,'err')}
};
window.resolveHandoff=async function(sid){
  if(!confirm('Resolve handoff for '+sid+'? Bot will resume.'))return;
  _stopHandoffPoll();
  try{await api('/handoff/'+encodeURIComponent(sid)+'/resolve',{method:'POST'});toast('Resolved','ok');if(sid===_handoffTarget)document.getElementById('handoffReplyBox').style.display='none';loadHandoffs()}catch(e){toast(e.message,'err')}
};

// ── Fallback / Unanswered ─────────────────────────────────────────────
async function loadFallbacks(){
  try{
    var d=await api('/fallback-log?unresolved_only=true');
    var stats=document.getElementById('fallbackStats');
    stats.innerHTML='<div class="card"><div class="card-label">'+t('fallback.unresolved')+'</div><div class="card-value" style="color:var(--danger)">'+d.unresolved+'</div></div>';
    var rows=document.getElementById('fallbackRows');
    rows.innerHTML='';
    (d.questions||[]).forEach(function(q){
      var statusTag=q.added_to_kb?'<span class="tag tag-on">In KB</span>':q.resolved?'<span class="tag" style="background:rgba(245,158,11,.15);color:var(--warn)">Resolved</span>':'<span class="tag tag-off">Open</span>';
      var actions='<button class="btn btn-ghost btn-sm" onclick="resolveFallback(\''+encodeURIComponent(q.question)+'\')">✓ Resolve</button> <button class="btn btn-primary btn-sm" onclick="addToKb(\''+encodeURIComponent(q.question)+'\')">+ KB</button> <button class="btn btn-danger btn-sm" onclick="deleteFallback(\''+encodeURIComponent(q.question)+'\')">✕</button>';
      rows.innerHTML+='<tr><td style="max-width:200px;white-space:pre-wrap;font-size:12px">'+q.question+'</td><td style="max-width:200px;white-space:pre-wrap;font-size:11px;color:var(--muted)">'+q.answer_given.substring(0,100)+'</td><td style="font-size:11px">'+q.session_id+'</td><td style="font-size:11px">'+new Date(q.created_at).toLocaleString()+'</td><td>'+statusTag+'</td><td>'+actions+'</td></tr>';
    });
    if(!d.questions||!d.questions.length)rows.innerHTML='<tr><td colspan="6" style="text-align:center;color:var(--muted);padding:24px">No unanswered questions — great!</td></tr>';
  }catch(e){toast(e.message,'err')}
}
window.loadFallbacks=loadFallbacks;
window.resolveFallback=async function(q){try{await api('/fallback-log/resolve',{method:'PATCH',body:{question:decodeURIComponent(q)}});loadFallbacks();toast('Resolved','ok')}catch(e){toast(e.message,'err')}};
window.addToKb=async function(q){try{await api('/fallback-log/add-to-kb',{method:'PATCH',body:{question:decodeURIComponent(q)}});loadFallbacks();toast('Marked as added to KB','ok')}catch(e){toast(e.message,'err')}};
window.deleteFallback=async function(q){if(!confirm('Delete this entry?'))return;try{await api('/fallback-log',{method:'DELETE',body:{question:decodeURIComponent(q)}});loadFallbacks();toast('Deleted','ok')}catch(e){toast(e.message,'err')}};

})();"""

# ══════════════════════════════════════════════════════════════════════
# Translations (injected as JSON into __LANGS_JSON__)
# ══════════════════════════════════════════════════════════════════════
_TRANSLATIONS: dict[str, dict[str, str]] = {
    "en": {
        "nav.overview": "Overview",
        "nav.sessions": "Sessions",
        "nav.budget": "Budget",
        "nav.config": "Configuration",
        "nav.line": "LINE",
        "nav.data": "Data Files",
        "nav.logs": "Logs",
        "nav.section.channels": "Channels",
        "nav.section.content": "Content",
        "page.overview": "\U0001f4ca Overview",
        "page.sessions": "\U0001f4ac Sessions",
        "page.budget": "\U0001f4b0 Budget",
        "page.config": "\u2699\ufe0f Configuration",
        "page.line": "\U0001f4ac LINE Channel",
        "page.data": "\U0001f4c1 Data Files",
        "page.logs": "\U0001f4cb Logs",
        "cfg.tab.env": "Environment",
        "cfg.tab.client": "Client",
        "cfg.tab.personality": "Personality",
        "btn.refresh": "\u21bb Refresh",
        "btn.clearAll": "Clear All",
        "btn.resetToday": "Reset Today",
        "btn.saveEnv": "Save Environment Settings",
        "btn.saveClient": "Save Client Config",
        "btn.savePersonality": "Save Personality Config",
        "btn.newFile": "+ New File",
        "btn.create": "Create",
        "btn.cancel": "Cancel",
        "btn.closeEditor": "\u2715 Close",
        "view.form": "Form",
        "view.yaml": "YAML",
        "view.visual": "Visual",
        "view.markdown": "Markdown",
        "restart.note": "Restart required for changes to take effect",
        "data.hint": "Knowledge base files for the chatbot. Edit content, then re-ingest to update the vector store.",
        "data.upload.cta": "<strong>Click to upload</strong> or drag files here",
        "data.upload.hint": ".md, .txt files \u2014 UTF-8 only",
        "data.newfile": "Create New Data File",
        "line.nocfg.title": "LINE Not Configured",
        "line.nocfg.body": "Set LINE_CHANNEL_ACCESS_TOKEN and LINE_CHANNEL_SECRET in your .env file to enable LINE integration.",
        "logs.nocfg.title": "Log File Not Configured",
        "logs.nocfg.body": "Log file is auto-configured. It will appear after the server starts logging.",
        "logs.nocfg.go": "Go to",
        "logs.nocfg.link": "Configuration \u2192 Environment",
        "logs.nocfg.set": "to set this.",
        "ov.status": "Status",
        "ov.uptime": "Uptime",
        "ov.model": "Model",
        "ov.sessions": "Sessions",
        "ov.tokens": "Tokens",
        "ov.usd": "USD Spent",
        "ov.ip": "IP Buckets",
        "ov.spam": "Spam Trackers",
        "ov.running": "\U0001f7e2 Running",
        "ov.down": "\U0001f534 Down",
        "ov.channels": "Channels",
        "ov.security": "Security",
        "th.channel": "Channel",
        "th.status": "Status",
        "th.feature": "Feature",
        "sec.rate": "Rate Limiting",
        "sec.spam": "Spam Detection",
        "sec.budget": "Budget Guard",
        "sec.hsts": "HSTS",
        "sec.cors": "Strict CORS",
        "sec.apikey": "API Key",
        "bud.today": "Today",
        "bud.model": "Model",
        "bud.tokens": "Tokens Used",
        "bud.usd": "USD Spent",
        "bud.status": "Status",
        "bud.enabled": "\U0001f6e1\ufe0f Enabled",
        "bud.disabled": "\u26a0\ufe0f Disabled",
        "bud.token_usage": "Token Usage",
        "bud.usd_usage": "USD Usage",
        "bud.last7": "Last 7 days",
        "bud.last30": "Last 30 days",
        "bud.budget_on": "Budget ON",
        "bud.no_cap": "No cap",
        "bud.tokens_unit": "tokens",
        "bud.token_usage_today": "Token usage today",
        "bud.usd_usage_today": "USD usage today",
        "bud.prev_days": "Previous days",
        "bud.no_data_period": "No data for this period",
        "bud.history_total": "Total",
        "budget.chart.dailySpend30dUsd": "Daily spend \u2014 last 30 days (USD)",
        "budget.history.title": "Spend History",
        "budget.history.filter.7days": "7 days",
        "budget.history.filter.30days": "30 days",
        "budget.history.filter.all": "All",
        "budget.history.header.date": "Date",
        "budget.history.header.tokensUsed": "Tokens Used",
        "budget.history.header.usdSpent": "USD Spent",
        "budget.history.header.dailyCapPct": "% of Daily Cap",
        "cfg.llm": "LLM",
        "cfg.rag": "RAG",
        "cfg.conversation": "Conversation",
        "cfg.rate": "Rate Limiting",
        "cfg.spam": "Spam Detection",
        "cfg.budget_cap": "Budget",
        "cfg.security": "Security",
        "cfg.general": "General",
        "cfg.secrets": "Secrets (read-only)",
        "cfg.enabled": "Enabled",
        "cfg.disabled": "Disabled",
        "th.session_id": "Session ID",
        "th.messages": "Messages",
        "th.last_active": "Last Activity",
        "th.actions": "Actions",
        "th.file": "File",
        "th.folder": "Folder",
        "th.size": "Size",
        "onb.welcome": "Welcome to Admin Dashboard",
        "onb.welcome_sub": "Quick tour \u2014 takes 10 seconds",
        "onb.step1_title": "\U0001f4c1 Data Files",
        "onb.step1_body": "Add your business knowledge here \u2014 products, hours, policies. The chatbot learns from these files.",
        "onb.step2_title": "\U0001f3e2 Business Info",
        "onb.step2_body": "Set your business name, location, language, and which personality preset to use. This tells the bot who it's representing.",
        "onb.step3_title": "\U0001f916 AI Personalization",
        "onb.step3_body": "Customize the bot's tone, character, and response style. The personality shapes how the bot speaks to your customers.",
        "onb.step4_title": "\U0001f4ca Overview",
        "onb.step4_body": "Monitor sessions, budget, and channels. All live stats in one place.",
        "onb.skip": "Skip",
        "onb.next": "Next",
        "onb.prev": "Back",
        "onb.done": "Get Started",
        "onb.go_data": "Go to Data Files",
        "onb.go_config": "Go to Configuration",
        "cf.basic": "Basic Info",
        "cf.client_id": "Client ID",
        "cf.display_name": "Display Name",
        "cf.location": "Location",
        "cf.timezone": "Timezone",
        "cf.personality": "Personality",
        "cf.languages": "Languages",
        "cf.lang_primary": "Primary Language",
        "cf.lang_fallback": "Fallback Language",
        "cf.langs_offered": "Languages Offered (comma-separated)",
        "cf.prompt_extra": "System Prompt Extra",
        "cf.prompt_extra_hint": "Additional business info and instructions for the AI. Line breaks work naturally \u2014 no special formatting needed.",
        "cf.greeting_override": "Greeting Override",
        "cf.data_paths": "Data Paths",
        "cf.data_paths_hint": "Comma-separated paths",
        "cf.channels": "Channels",
        "cf.editing": "Editing",
        "pf.basic": "Basic Info",
        "pf.name": "Name",
        "pf.temperature": "Temperature (0-1)",
        "pf.description": "Description",
        "pf.system_prompt": "System Prompt",
        "pf.system_prompt_hint": "The AI personality. Write naturally \u2014 line breaks are preserved. No \\n needed.",
        "pf.messages": "Messages",
        "pf.greeting": "Greeting",
        "pf.fallback": "Fallback Message",
        "pf.style_kw": "Style Keywords",
        "pf.style_kw_hint": "Comma-separated",
        "nav.section.admin": "Admin",
        "nav.users": "Users",
        "page.users": "\U0001f465 Users",
        "btn.addUser": "+ Add User",
        "users.newuser": "Create New User",
        "users.username": "Username",
        "users.password": "Password",
        "users.role": "Role",
        "users.created_by": "Created By",
        "users.role_hint": "Admin: full access, can manage users. Viewer: read-only access to dashboard.",
        "nav.section.business": "Business",
        "nav.products": "Products",
        "nav.contacts": "Messages",
        "nav.handoff": "Handoff",
        "nav.fallback": "Unanswered",
        "page.products": "\U0001f6cd\ufe0f Products",
        "page.contacts": "\U0001f4e7 Messages",
        "page.handoff": "\U0001f91d Live Handoff",
        "page.fallback": "\u2753 Unanswered Questions",
        "products.total": "Total Products",
        "products.categories": "Categories",
        "contacts.unread": "Unread",
        "contacts.total": "Total Messages",
        "fallback.unresolved": "Unresolved",
        "th.name": "Name",
        "th.category": "Category",
        "th.price": "Price",
        "th.image": "Image",
        "th.message": "Message",
        "th.time": "Time",
        "th.question": "Question",
    },
    "he": {
        "nav.overview": "\u05e1\u05e7\u05d9\u05e8\u05d4",
        "nav.sessions": "\u05e9\u05d9\u05d7\u05d5\u05ea",
        "nav.budget": "\u05ea\u05e7\u05e6\u05d9\u05d1",
        "nav.config": "\u05d4\u05d2\u05d3\u05e8\u05d5\u05ea",
        "nav.line": "LINE",
        "nav.data": "\u05e7\u05d1\u05e6\u05d9 \u05de\u05d9\u05d3\u05e2",
        "nav.logs": "\u05dc\u05d5\u05d2\u05d9\u05dd",
        "nav.section.channels": "\u05e2\u05e8\u05d5\u05e6\u05d9\u05dd",
        "nav.section.content": "\u05ea\u05d5\u05db\u05df",
        "page.overview": "\U0001f4ca \u05e1\u05e7\u05d9\u05e8\u05d4 \u05db\u05dc\u05dc\u05d9\u05ea",
        "page.sessions": "\U0001f4ac \u05e9\u05d9\u05d7\u05d5\u05ea",
        "page.budget": "\U0001f4b0 \u05ea\u05e7\u05e6\u05d9\u05d1",
        "page.config": "\u2699\ufe0f \u05d4\u05d2\u05d3\u05e8\u05d5\u05ea",
        "page.line": "\U0001f4ac \u05e2\u05e8\u05d5\u05e5 LINE",
        "page.data": "\U0001f4c1 \u05e7\u05d1\u05e6\u05d9 \u05de\u05d9\u05d3\u05e2",
        "page.logs": "\U0001f4cb \u05dc\u05d5\u05d2\u05d9\u05dd",
        "cfg.tab.env": "\u05e1\u05d1\u05d9\u05d1\u05d4",
        "cfg.tab.client": "\u05dc\u05e7\u05d5\u05d7",
        "cfg.tab.personality": "\u05d0\u05d9\u05e9\u05d9\u05d5\u05ea",
        "btn.refresh": "\u21bb \u05e8\u05e2\u05e0\u05df",
        "btn.clearAll": "\u05e0\u05e7\u05d4 \u05d4\u05db\u05dc",
        "btn.resetToday": "\u05d0\u05e4\u05e1 \u05dc\u05d4\u05d9\u05d5\u05dd",
        "btn.saveEnv": "\u05e9\u05de\u05d5\u05e8 \u05d4\u05d2\u05d3\u05e8\u05d5\u05ea \u05e1\u05d1\u05d9\u05d1\u05d4",
        "btn.saveClient": "\u05e9\u05de\u05d5\u05e8 \u05d4\u05d2\u05d3\u05e8\u05d5\u05ea \u05dc\u05e7\u05d5\u05d7",
        "btn.savePersonality": "\u05e9\u05de\u05d5\u05e8 \u05d4\u05d2\u05d3\u05e8\u05d5\u05ea \u05d0\u05d9\u05e9\u05d9\u05d5\u05ea",
        "btn.newFile": "+ \u05e7\u05d5\u05d1\u05e5 \u05d7\u05d3\u05e9",
        "btn.create": "\u05e6\u05d5\u05e8",
        "btn.cancel": "\u05d1\u05d9\u05d8\u05d5\u05dc",
        "btn.closeEditor": "\u2715 \u05e1\u05d2\u05d5\u05e8",
        "view.form": "\u05d8\u05d5\u05e4\u05e1",
        "view.yaml": "YAML",
        "view.visual": "\u05d5\u05d9\u05d6\u05d5\u05d0\u05dc\u05d9",
        "view.markdown": "Markdown",
        "restart.note": "\u05e0\u05d3\u05e8\u05e9 \u05d4\u05e4\u05e2\u05dc\u05d4 \u05de\u05d7\u05d3\u05e9 \u05dc\u05d9\u05d9\u05e9\u05d5\u05dd \u05d4\u05e9\u05d9\u05e0\u05d5\u05d9\u05d9\u05dd",
        "data.hint": "\u05e7\u05d1\u05e6\u05d9 \u05d1\u05e1\u05d9\u05e1 \u05d9\u05d3\u05e2 \u05dc\u05e6'\u05d0\u05d8\u05d1\u05d5\u05d8. \u05e2\u05e8\u05d5\u05da \u05ea\u05d5\u05db\u05df \u05d5\u05d0\u05d6 \u05d4\u05db\u05e0\u05e1 \u05de\u05d7\u05d3\u05e9 \u05dc\u05e2\u05d3\u05db\u05d5\u05df \u05de\u05d0\u05d2\u05e8 \u05d4\u05d5\u05d5\u05e7\u05d8\u05d5\u05e8\u05d9\u05dd.",
        "data.upload.cta": "<strong>\u05dc\u05d7\u05e5 \u05dc\u05d4\u05e2\u05dc\u05d0\u05d4</strong> \u05d0\u05d5 \u05d2\u05e8\u05d5\u05e8 \u05e7\u05d1\u05e6\u05d9\u05dd \u05dc\u05db\u05d0\u05df",
        "data.upload.hint": "\u05e7\u05d1\u05e6\u05d9 .md, .txt \u2014 UTF-8 \u05d1\u05dc\u05d1\u05d3",
        "data.newfile": "\u05e6\u05d5\u05e8 \u05e7\u05d5\u05d1\u05e5 \u05de\u05d9\u05d3\u05e2 \u05d7\u05d3\u05e9",
        "line.nocfg.title": "LINE \u05dc\u05d0 \u05de\u05d5\u05d2\u05d3\u05e8",
        "line.nocfg.body": "\u05d4\u05d2\u05d3\u05e8 LINE_CHANNEL_ACCESS_TOKEN \u05d5-LINE_CHANNEL_SECRET \u05d1\u05e7\u05d5\u05d1\u05e5 \u05d4-.env \u05e9\u05dc\u05da.",
        "logs.nocfg.title": "\u05e7\u05d5\u05d1\u05e5 \u05dc\u05d5\u05d2 \u05d8\u05e8\u05dd \u05e0\u05d5\u05e6\u05e8",
        "logs.nocfg.body": "\u05e7\u05d5\u05d1\u05e5 \u05d4\u05dc\u05d5\u05d2 \u05de\u05d5\u05d2\u05d3\u05e8 \u05d0\u05d5\u05d8\u05d5\u05de\u05d8\u05d9\u05ea. \u05d4\u05d5\u05d0 \u05d9\u05d5\u05e4\u05d9\u05e2 \u05dc\u05d0\u05d7\u05e8 \u05e9\u05d4\u05e9\u05e8\u05ea \u05d9\u05ea\u05d7\u05d9\u05dc \u05dc\u05e8\u05e9\u05d5\u05dd \u05dc\u05d5\u05d2\u05d9\u05dd.",
        "logs.nocfg.go": "\u05e2\u05d1\u05d5\u05e8 \u05dc",
        "logs.nocfg.link": "\u05d4\u05d2\u05d3\u05e8\u05d5\u05ea \u2190 \u05e1\u05d1\u05d9\u05d1\u05d4",
        "logs.nocfg.set": "\u05dc\u05d4\u05d2\u05d3\u05e8\u05d4.",
        "ov.status": "\u05e1\u05d8\u05d8\u05d5\u05e1",
        "ov.uptime": "\u05d6\u05de\u05df \u05e4\u05e2\u05d9\u05dc\u05d5\u05ea",
        "ov.model": "\u05de\u05d5\u05d3\u05dc",
        "ov.sessions": "\u05e9\u05d9\u05d7\u05d5\u05ea",
        "ov.tokens": "\u05d8\u05d5\u05e7\u05e0\u05d9\u05dd",
        "ov.usd": "\u05d4\u05d5\u05e6\u05d0\u05d4 ($)",
        "ov.ip": "IP \u05e4\u05e2\u05d9\u05dc\u05d9\u05dd",
        "ov.spam": "\u05de\u05e2\u05e7\u05d1 \u05e1\u05e4\u05d0\u05dd",
        "ov.running": "\U0001f7e2 \u05e4\u05e2\u05d9\u05dc",
        "ov.down": "\U0001f534 \u05de\u05d5\u05e9\u05d1\u05ea",
        "ov.channels": "\u05e2\u05e8\u05d5\u05e6\u05d9\u05dd",
        "ov.security": "\u05d0\u05d1\u05d8\u05d7\u05d4",
        "th.channel": "\u05e2\u05e8\u05d5\u05e5",
        "th.status": "\u05e1\u05d8\u05d8\u05d5\u05e1",
        "th.feature": "\u05ea\u05db\u05d5\u05e0\u05d4",
        "sec.rate": "\u05d4\u05d2\u05d1\u05dc\u05ea \u05e7\u05e6\u05d1",
        "sec.spam": "\u05d6\u05d9\u05d4\u05d5\u05d9 \u05e1\u05e4\u05d0\u05dd",
        "sec.budget": "\u05de\u05d2\u05df \u05ea\u05e7\u05e6\u05d9\u05d1",
        "sec.hsts": "HSTS",
        "sec.cors": "CORS \u05de\u05d7\u05de\u05d9\u05e8",
        "sec.apikey": "\u05de\u05e4\u05ea\u05d7 API",
        "bud.today": "\u05d4\u05d9\u05d5\u05dd",
        "bud.model": "\u05de\u05d5\u05d3\u05dc",
        "bud.tokens": "\u05d8\u05d5\u05e7\u05e0\u05d9\u05dd",
        "bud.usd": "\u05d4\u05d5\u05e6\u05d0\u05d4 ($)",
        "bud.status": "\u05e1\u05d8\u05d8\u05d5\u05e1",
        "bud.enabled": "\U0001f6e1\ufe0f \u05de\u05d5\u05e4\u05e2\u05dc",
        "bud.disabled": "\u26a0\ufe0f \u05de\u05d5\u05e9\u05d1\u05ea",
        "bud.token_usage": "\u05e9\u05d9\u05de\u05d5\u05e9 \u05d1\u05d8\u05d5\u05e7\u05e0\u05d9\u05dd",
        "bud.usd_usage": "\u05e9\u05d9\u05de\u05d5\u05e9 \u05d1\u05d3\u05d5\u05dc\u05e8\u05d9\u05dd",
        "bud.last7": "7 \u05d9\u05de\u05d9\u05dd \u05d0\u05d7\u05e8\u05d5\u05e0\u05d9\u05dd",
        "bud.last30": "30 \u05d9\u05de\u05d9\u05dd \u05d0\u05d7\u05e8\u05d5\u05e0\u05d9\u05dd",
        "bud.budget_on": "\u05ea\u05e7\u05e6\u05d9\u05d1 \u05e4\u05e2\u05d9\u05dc",
        "bud.no_cap": "\u05dc\u05dc\u05d0 \u05de\u05d2\u05d1\u05dc\u05d4",
        "bud.tokens_unit": "\u05d8\u05d5\u05e7\u05e0\u05d9\u05dd",
        "bud.token_usage_today": "\u05e9\u05d9\u05de\u05d5\u05e9 \u05d1\u05d8\u05d5\u05e7\u05e0\u05d9\u05dd \u05d4\u05d9\u05d5\u05dd",
        "bud.usd_usage_today": "\u05d4\u05d5\u05e6\u05d0\u05d4 \u05d1\u05d3\u05d5\u05dc\u05e8\u05d9\u05dd \u05d4\u05d9\u05d5\u05dd",
        "bud.prev_days": "\u05d9\u05de\u05d9\u05dd \u05e7\u05d5\u05d3\u05de\u05d9\u05dd",
        "bud.no_data_period": "\u05d0\u05d9\u05df \u05e0\u05ea\u05d5\u05e0\u05d9\u05dd \u05dc\u05ea\u05e7\u05d5\u05e4\u05d4 \u05d6\u05d5",
        "bud.history_total": '\u05e1\u05d4"\u05db',
        "budget.chart.dailySpend30dUsd": "\u05d4\u05d5\u05e6\u05d0\u05d4 \u05d9\u05d5\u05de\u05d9\u05ea \u2014 30 \u05d9\u05de\u05d9\u05dd \u05d0\u05d7\u05e8\u05d5\u05e0\u05d9\u05dd (USD)",
        "budget.history.title": "\u05d4\u05d9\u05e1\u05d8\u05d5\u05e8\u05d9\u05d9\u05ea \u05d4\u05d5\u05e6\u05d0\u05d5\u05ea",
        "budget.history.filter.7days": "7 \u05d9\u05de\u05d9\u05dd",
        "budget.history.filter.30days": "30 \u05d9\u05de\u05d9\u05dd",
        "budget.history.filter.all": "\u05d4\u05db\u05dc",
        "budget.history.header.date": "\u05ea\u05d0\u05e8\u05d9\u05da",
        "budget.history.header.tokensUsed": "\u05d8\u05d5\u05e7\u05e0\u05d9\u05dd",
        "budget.history.header.usdSpent": "\u05d4\u05d5\u05e6\u05d0\u05d4 ($)",
        "budget.history.header.dailyCapPct": "% \u05de\u05d4\u05de\u05d2\u05d1\u05dc\u05d4",
        "cfg.llm": "\u05de\u05d5\u05d3\u05dc \u05e9\u05e4\u05d4",
        "cfg.rag": "RAG",
        "cfg.conversation": "\u05e9\u05d9\u05d7\u05d4",
        "cfg.rate": "\u05d4\u05d2\u05d1\u05dc\u05ea \u05e7\u05e6\u05d1",
        "cfg.spam": "\u05d6\u05d9\u05d4\u05d5\u05d9 \u05e1\u05e4\u05d0\u05dd",
        "cfg.budget_cap": "\u05ea\u05e7\u05e6\u05d9\u05d1",
        "cfg.security": "\u05d0\u05d1\u05d8\u05d7\u05d4",
        "cfg.general": "\u05db\u05dc\u05dc\u05d9",
        "cfg.secrets": "\u05e1\u05d5\u05d3\u05d5\u05ea (\u05e7\u05e8\u05d9\u05d0\u05d4 \u05d1\u05dc\u05d1\u05d3)",
        "cfg.enabled": "\u05de\u05d5\u05e4\u05e2\u05dc",
        "cfg.disabled": "\u05de\u05d5\u05e9\u05d1\u05ea",
        "th.session_id": "\u05de\u05d6\u05d4\u05d4 \u05e9\u05d9\u05d7\u05d4",
        "th.messages": "\u05d4\u05d5\u05d3\u05e2\u05d5\u05ea",
        "th.last_active": "\u05e4\u05e2\u05d9\u05dc\u05d5\u05ea \u05d0\u05d7\u05e8\u05d5\u05e0\u05d4",
        "th.actions": "\u05e4\u05e2\u05d5\u05dc\u05d5\u05ea",
        "th.file": "\u05e7\u05d5\u05d1\u05e5",
        "th.folder": "\u05ea\u05d9\u05e7\u05d9\u05d9\u05d4",
        "th.size": "\u05d2\u05d5\u05d3\u05dc",
        "onb.welcome": "\u05d1\u05e8\u05d5\u05db\u05d9\u05dd \u05d4\u05d1\u05d0\u05d9\u05dd \u05dc\u05e4\u05d0\u05e0\u05dc \u05d4\u05e0\u05d9\u05d4\u05d5\u05dc",
        "onb.welcome_sub": "\u05e1\u05d9\u05d5\u05e8 \u05de\u05d4\u05d9\u05e8 \u2014 10 \u05e9\u05e0\u05d9\u05d5\u05ea",
        "onb.step1_title": "\U0001f4c1 \u05e7\u05d1\u05e6\u05d9 \u05de\u05d9\u05d3\u05e2",
        "onb.step1_body": "\u05d4\u05d5\u05e1\u05d9\u05e4\u05d5 \u05d0\u05ea \u05d4\u05de\u05d9\u05d3\u05e2 \u05d4\u05e2\u05e1\u05e7\u05d9 \u05db\u05d0\u05df \u2014 \u05de\u05d5\u05e6\u05e8\u05d9\u05dd, \u05e9\u05e2\u05d5\u05ea, \u05de\u05d3\u05d9\u05e0\u05d9\u05d5\u05ea. \u05d4\u05e6'\u05d0\u05d8\u05d1\u05d5\u05d8 \u05dc\u05d5\u05de\u05d3 \u05de\u05d4\u05e7\u05d1\u05e6\u05d9\u05dd \u05d4\u05d0\u05dc\u05d4.",
        "onb.step2_title": "\U0001f3e2 \u05e4\u05e8\u05d8\u05d9 \u05d4\u05e2\u05e1\u05e7",
        "onb.step2_body": "\u05d4\u05d2\u05d3\u05d9\u05e8\u05d5 \u05e9\u05dd \u05e2\u05e1\u05e7, \u05de\u05d9\u05e7\u05d5\u05dd, \u05e9\u05e4\u05d4 \u05d5\u05d0\u05d9\u05d6\u05d5 \u05d0\u05d9\u05e9\u05d9\u05d5\u05ea \u05dc\u05d4\u05e9\u05ea\u05de\u05e9. \u05d4\u05d1\u05d5\u05d8 \u05d9\u05d3\u05e2 \u05de\u05d9 \u05d4\u05d5\u05d0 \u05de\u05d9\u05d9\u05e6\u05d2.",
        "onb.step3_title": "\U0001f916 \u05d4\u05ea\u05d0\u05de\u05ea AI",
        "onb.step3_body": "\u05d4\u05ea\u05d0\u05d9\u05de\u05d5 \u05d0\u05ea \u05d4\u05d8\u05d5\u05df, \u05d4\u05d0\u05d5\u05e4\u05d9 \u05d5\u05e1\u05d2\u05e0\u05d5\u05df \u05d4\u05ea\u05d2\u05d5\u05d1\u05d4. \u05d4\u05d0\u05d9\u05e9\u05d9\u05d5\u05ea \u05e7\u05d5\u05d1\u05e2\u05ea \u05d0\u05d9\u05da \u05d4\u05d1\u05d5\u05d8 \u05de\u05d3\u05d1\u05e8 \u05e2\u05dd \u05d4\u05dc\u05e7\u05d5\u05d7\u05d5\u05ea \u05e9\u05dc\u05db\u05dd.",
        "onb.step4_title": "\U0001f4ca \u05e1\u05e7\u05d9\u05e8\u05d4",
        "onb.step4_body": "\u05e2\u05e7\u05d1\u05d5 \u05d0\u05d7\u05e8\u05d9 \u05e9\u05d9\u05d7\u05d5\u05ea, \u05ea\u05e7\u05e6\u05d9\u05d1 \u05d5\u05e2\u05e8\u05d5\u05e6\u05d9\u05dd. \u05db\u05dc \u05d4\u05e0\u05ea\u05d5\u05e0\u05d9\u05dd \u05d1\u05de\u05e7\u05d5\u05dd \u05d0\u05d7\u05d3.",
        "onb.skip": "\u05d3\u05dc\u05d2",
        "onb.next": "\u05d4\u05d1\u05d0",
        "onb.prev": "\u05d4\u05e7\u05d5\u05d3\u05dd",
        "onb.done": "\u05d1\u05d5\u05d0\u05d5 \u05e0\u05ea\u05d7\u05d9\u05dc",
        "onb.go_data": "\u05dc\u05e7\u05d1\u05e6\u05d9 \u05de\u05d9\u05d3\u05e2",
        "onb.go_config": "\u05dc\u05d4\u05d2\u05d3\u05e8\u05d5\u05ea",
        "cf.basic": "\u05de\u05d9\u05d3\u05e2 \u05d1\u05e1\u05d9\u05e1\u05d9",
        "cf.client_id": "\u05de\u05d6\u05d4\u05d4 \u05dc\u05e7\u05d5\u05d7",
        "cf.display_name": "\u05e9\u05dd \u05ea\u05e6\u05d5\u05d2\u05d4",
        "cf.location": "\u05de\u05d9\u05e7\u05d5\u05dd",
        "cf.timezone": "\u05d0\u05d6\u05d5\u05e8 \u05d6\u05de\u05df",
        "cf.personality": "\u05d0\u05d9\u05e9\u05d9\u05d5\u05ea",
        "cf.languages": "\u05e9\u05e4\u05d5\u05ea",
        "cf.lang_primary": "\u05e9\u05e4\u05d4 \u05e8\u05d0\u05e9\u05d9\u05ea",
        "cf.lang_fallback": "\u05e9\u05e4\u05ea \u05d2\u05d9\u05d1\u05d5\u05d9",
        "cf.langs_offered": "\u05e9\u05e4\u05d5\u05ea \u05de\u05d5\u05e6\u05e2\u05d5\u05ea (\u05de\u05d5\u05e4\u05e8\u05d3\u05d5\u05ea \u05d1\u05e4\u05e1\u05d9\u05e7)",
        "cf.prompt_extra": "\u05e4\u05e8\u05d5\u05de\u05e4\u05d8 \u05de\u05e2\u05e8\u05db\u05ea \u05e0\u05d5\u05e1\u05e3",
        "cf.prompt_extra_hint": "\u05de\u05d9\u05d3\u05e2 \u05e2\u05e1\u05e7\u05d9 \u05e0\u05d5\u05e1\u05e3 \u05d5\u05d4\u05e0\u05d7\u05d9\u05d5\u05ea \u05dc-AI. \u05e9\u05d5\u05e8\u05d5\u05ea \u05d7\u05d3\u05e9\u05d5\u05ea \u05e2\u05d5\u05d1\u05d3\u05d5\u05ea \u05db\u05e8\u05d2\u05d9\u05dc \u2014 \u05dc\u05d0 \u05e6\u05e8\u05d9\u05da \u05e2\u05d9\u05e6\u05d5\u05d1 \u05de\u05d9\u05d5\u05d7\u05d3.",
        "cf.greeting_override": "\u05d1\u05e8\u05db\u05d4 \u05de\u05d5\u05ea\u05d0\u05de\u05ea",
        "cf.data_paths": "\u05e0\u05ea\u05d9\u05d1\u05d9 \u05e0\u05ea\u05d5\u05e0\u05d9\u05dd",
        "cf.data_paths_hint": "\u05e0\u05ea\u05d9\u05d1\u05d9\u05dd \u05de\u05d5\u05e4\u05e8\u05d3\u05d9\u05dd \u05d1\u05e4\u05e1\u05d9\u05e7",
        "cf.channels": "\u05e2\u05e8\u05d5\u05e6\u05d9\u05dd",
        "cf.editing": "\u05e2\u05e8\u05d9\u05db\u05d4",
        "pf.basic": "\u05de\u05d9\u05d3\u05e2 \u05d1\u05e1\u05d9\u05e1\u05d9",
        "pf.name": "\u05e9\u05dd",
        "pf.temperature": "\u05d8\u05de\u05e4\u05e8\u05d8\u05d5\u05e8\u05d4 (0-1)",
        "pf.description": "\u05ea\u05d9\u05d0\u05d5\u05e8",
        "pf.system_prompt": "\u05e4\u05e8\u05d5\u05de\u05e4\u05d8 \u05de\u05e2\u05e8\u05db\u05ea",
        "pf.system_prompt_hint": "\u05d0\u05d9\u05e9\u05d9\u05d5\u05ea \u05d4-AI. \u05db\u05ea\u05d1\u05d5 \u05d1\u05d8\u05d1\u05e2\u05d9\u05d5\u05ea \u2014 \u05e9\u05d5\u05e8\u05d5\u05ea \u05d7\u05d3\u05e9\u05d5\u05ea \u05e0\u05e9\u05de\u05e8\u05d5\u05ea.",
        "pf.messages": "\u05d4\u05d5\u05d3\u05e2\u05d5\u05ea",
        "pf.greeting": "\u05d1\u05e8\u05db\u05d4",
        "pf.fallback": "\u05d4\u05d5\u05d3\u05e2\u05ea \u05d2\u05d9\u05d1\u05d5\u05d9",
        "pf.style_kw": "\u05de\u05d9\u05dc\u05d5\u05ea \u05e1\u05d2\u05e0\u05d5\u05df",
        "pf.style_kw_hint": "\u05de\u05d5\u05e4\u05e8\u05d3\u05d5\u05ea \u05d1\u05e4\u05e1\u05d9\u05e7",
        "nav.section.admin": "\u05e0\u05d9\u05d4\u05d5\u05dc",
        "nav.users": "\u05de\u05e9\u05ea\u05de\u05e9\u05d9\u05dd",
        "page.users": "\U0001f465 \u05de\u05e9\u05ea\u05de\u05e9\u05d9\u05dd",
        "btn.addUser": "+ \u05d4\u05d5\u05e1\u05e3 \u05de\u05e9\u05ea\u05de\u05e9",
        "users.newuser": "\u05e6\u05d5\u05e8 \u05de\u05e9\u05ea\u05de\u05e9 \u05d7\u05d3\u05e9",
        "users.username": "\u05e9\u05dd \u05de\u05e9\u05ea\u05de\u05e9",
        "users.password": "\u05e1\u05d9\u05e1\u05de\u05d4",
        "users.role": "\u05ea\u05e4\u05e7\u05d9\u05d3",
        "users.created_by": "\u05e0\u05d5\u05e6\u05e8 \u05e2\u05dc \u05d9\u05d3\u05d9",
        "users.role_hint": "\u05de\u05e0\u05d4\u05dc: \u05d2\u05d9\u05e9\u05d4 \u05de\u05dc\u05d0\u05d4, \u05d9\u05db\u05d5\u05dc \u05dc\u05e0\u05d4\u05dc \u05de\u05e9\u05ea\u05de\u05e9\u05d9\u05dd. \u05e6\u05d5\u05e4\u05d4: \u05d2\u05d9\u05e9\u05ea \u05e7\u05e8\u05d9\u05d0\u05d4 \u05d1\u05dc\u05d1\u05d3.",
        "nav.section.business": "\u05e2\u05e1\u05e7",
        "nav.products": "\u05de\u05d5\u05e6\u05e8\u05d9\u05dd",
        "nav.contacts": "\u05d4\u05d5\u05d3\u05e2\u05d5\u05ea",
        "nav.handoff": "\u05d4\u05e2\u05d1\u05e8\u05d4",
        "nav.fallback": "\u05dc\u05dc\u05d0 \u05de\u05e2\u05e0\u05d4",
        "page.products": "\U0001f6cd\ufe0f \u05de\u05d5\u05e6\u05e8\u05d9\u05dd",
        "page.contacts": "\U0001f4e7 \u05d4\u05d5\u05d3\u05e2\u05d5\u05ea",
        "page.handoff": "\U0001f91d \u05d4\u05e2\u05d1\u05e8\u05d4 \u05dc\u05e0\u05e6\u05d9\u05d2",
        "page.fallback": "\u2753 \u05e9\u05d0\u05dc\u05d5\u05ea \u05dc\u05dc\u05d0 \u05de\u05e2\u05e0\u05d4",
        "products.total": "\u05e1\u05d4\u05f4\u05db \u05de\u05d5\u05e6\u05e8\u05d9\u05dd",
        "products.categories": "\u05e7\u05d8\u05d2\u05d5\u05e8\u05d9\u05d5\u05ea",
        "contacts.unread": "\u05dc\u05d0 \u05e0\u05e7\u05e8\u05d0\u05d5",
        "contacts.total": "\u05e1\u05d4\u05f4\u05db \u05d4\u05d5\u05d3\u05e2\u05d5\u05ea",
        "fallback.unresolved": "\u05dc\u05d0 \u05e0\u05e4\u05ea\u05e8\u05d5",
    },
    "th": {
        "nav.overview": "\u0e20\u0e32\u0e1e\u0e23\u0e27\u0e21",
        "nav.sessions": "\u0e40\u0e0b\u0e2a\u0e0a\u0e31\u0e19",
        "nav.budget": "\u0e07\u0e1a\u0e1b\u0e23\u0e30\u0e21\u0e32\u0e13",
        "nav.config": "\u0e01\u0e32\u0e23\u0e15\u0e31\u0e49\u0e07\u0e04\u0e48\u0e32",
        "nav.line": "LINE",
        "nav.data": "\u0e44\u0e1f\u0e25\u0e4c\u0e02\u0e49\u0e2d\u0e21\u0e39\u0e25",
        "nav.logs": "\u0e1a\u0e31\u0e19\u0e17\u0e36\u0e01",
        "nav.section.channels": "\u0e0a\u0e48\u0e2d\u0e07\u0e17\u0e32\u0e07",
        "nav.section.content": "\u0e40\u0e19\u0e37\u0e49\u0e2d\u0e2b\u0e32",
        "page.overview": "\U0001f4ca \u0e20\u0e32\u0e1e\u0e23\u0e27\u0e21",
        "page.sessions": "\U0001f4ac \u0e40\u0e0b\u0e2a\u0e0a\u0e31\u0e19",
        "page.budget": "\U0001f4b0 \u0e07\u0e1a\u0e1b\u0e23\u0e30\u0e21\u0e32\u0e13",
        "page.config": "\u2699\ufe0f \u0e01\u0e32\u0e23\u0e15\u0e31\u0e49\u0e07\u0e04\u0e48\u0e32",
        "page.line": "\U0001f4ac \u0e0a\u0e48\u0e2d\u0e07 LINE",
        "page.data": "\U0001f4c1 \u0e44\u0e1f\u0e25\u0e4c\u0e02\u0e49\u0e2d\u0e21\u0e39\u0e25",
        "page.logs": "\U0001f4cb \u0e1a\u0e31\u0e19\u0e17\u0e36\u0e01",
        "cfg.tab.env": "\u0e2a\u0e20\u0e32\u0e1e\u0e41\u0e27\u0e14\u0e25\u0e49\u0e2d\u0e21",
        "cfg.tab.client": "\u0e25\u0e39\u0e01\u0e04\u0e49\u0e32",
        "cfg.tab.personality": "\u0e1a\u0e38\u0e04\u0e25\u0e34\u0e01\u0e20\u0e32\u0e1e",
        "btn.refresh": "\u21bb \u0e23\u0e35\u0e40\u0e1f\u0e23\u0e0a",
        "btn.clearAll": "\u0e25\u0e49\u0e32\u0e07\u0e17\u0e31\u0e49\u0e07\u0e2b\u0e21\u0e14",
        "btn.resetToday": "\u0e23\u0e35\u0e40\u0e0b\u0e47\u0e15\u0e27\u0e31\u0e19\u0e19\u0e35\u0e49",
        "btn.saveEnv": "\u0e1a\u0e31\u0e19\u0e17\u0e36\u0e01\u0e01\u0e32\u0e23\u0e15\u0e31\u0e49\u0e07\u0e04\u0e48\u0e32\u0e2a\u0e20\u0e32\u0e1e\u0e41\u0e27\u0e14\u0e25\u0e49\u0e2d\u0e21",
        "btn.saveClient": "\u0e1a\u0e31\u0e19\u0e17\u0e36\u0e01\u0e01\u0e32\u0e23\u0e15\u0e31\u0e49\u0e07\u0e04\u0e48\u0e32\u0e25\u0e39\u0e01\u0e04\u0e49\u0e32",
        "btn.savePersonality": "\u0e1a\u0e31\u0e19\u0e17\u0e36\u0e01\u0e01\u0e32\u0e23\u0e15\u0e31\u0e49\u0e07\u0e04\u0e48\u0e32\u0e1a\u0e38\u0e04\u0e25\u0e34\u0e01\u0e20\u0e32\u0e1e",
        "btn.newFile": "+ \u0e44\u0e1f\u0e25\u0e4c\u0e43\u0e2b\u0e21\u0e48",
        "btn.create": "\u0e2a\u0e23\u0e49\u0e32\u0e07",
        "btn.cancel": "\u0e22\u0e01\u0e40\u0e25\u0e34\u0e01",
        "btn.closeEditor": "\u2715 \u0e1b\u0e34\u0e14",
        "view.form": "\u0e1f\u0e2d\u0e23\u0e4c\u0e21",
        "view.yaml": "YAML",
        "view.visual": "\u0e20\u0e32\u0e1e",
        "view.markdown": "Markdown",
        "restart.note": "\u0e15\u0e49\u0e2d\u0e07\u0e23\u0e35\u0e2a\u0e15\u0e32\u0e23\u0e4c\u0e17\u0e40\u0e1e\u0e37\u0e48\u0e2d\u0e43\u0e2b\u0e49\u0e01\u0e32\u0e23\u0e40\u0e1b\u0e25\u0e35\u0e48\u0e22\u0e19\u0e41\u0e1b\u0e25\u0e07\u0e21\u0e35\u0e1c\u0e25",
        "data.hint": "\u0e44\u0e1f\u0e25\u0e4c\u0e10\u0e32\u0e19\u0e04\u0e27\u0e32\u0e21\u0e23\u0e39\u0e49\u0e2a\u0e33\u0e2b\u0e23\u0e31\u0e1a\u0e41\u0e0a\u0e17\u0e1a\u0e2d\u0e17 \u0e41\u0e01\u0e49\u0e44\u0e02\u0e40\u0e19\u0e37\u0e49\u0e2d\u0e2b\u0e32 \u0e08\u0e32\u0e01\u0e19\u0e31\u0e49\u0e19\u0e1d\u0e31\u0e07\u0e02\u0e49\u0e2d\u0e21\u0e39\u0e25\u0e43\u0e2b\u0e21\u0e48\u0e40\u0e1e\u0e37\u0e48\u0e2d\u0e2d\u0e31\u0e1b\u0e40\u0e14\u0e15",
        "data.upload.cta": "<strong>\u0e04\u0e25\u0e34\u0e01\u0e40\u0e1e\u0e37\u0e48\u0e2d\u0e2d\u0e31\u0e1b\u0e42\u0e2b\u0e25\u0e14</strong> \u0e2b\u0e23\u0e37\u0e2d\u0e25\u0e32\u0e01\u0e44\u0e1f\u0e25\u0e4c\u0e21\u0e32\u0e27\u0e32\u0e07",
        "data.upload.hint": "\u0e44\u0e1f\u0e25\u0e4c .md, .txt \u2014 UTF-8 \u0e40\u0e17\u0e48\u0e32\u0e19\u0e31\u0e49\u0e19",
        "data.newfile": "\u0e2a\u0e23\u0e49\u0e32\u0e07\u0e44\u0e1f\u0e25\u0e4c\u0e02\u0e49\u0e2d\u0e21\u0e39\u0e25\u0e43\u0e2b\u0e21\u0e48",
        "line.nocfg.title": "\u0e22\u0e31\u0e07\u0e44\u0e21\u0e48\u0e44\u0e14\u0e49\u0e15\u0e31\u0e49\u0e07\u0e04\u0e48\u0e32 LINE",
        "line.nocfg.body": "\u0e15\u0e31\u0e49\u0e07\u0e04\u0e48\u0e32 LINE_CHANNEL_ACCESS_TOKEN \u0e41\u0e25\u0e30 LINE_CHANNEL_SECRET \u0e43\u0e19 .env \u0e02\u0e2d\u0e07\u0e04\u0e38\u0e13",
        "logs.nocfg.title": "\u0e22\u0e31\u0e07\u0e44\u0e21\u0e48\u0e44\u0e14\u0e49\u0e2a\u0e23\u0e49\u0e32\u0e07\u0e44\u0e1f\u0e25\u0e4c\u0e1a\u0e31\u0e19\u0e17\u0e36\u0e01",
        "logs.nocfg.body": "\u0e44\u0e1f\u0e25\u0e4c\u0e1a\u0e31\u0e19\u0e17\u0e36\u0e01\u0e16\u0e39\u0e01\u0e15\u0e31\u0e49\u0e07\u0e04\u0e48\u0e32\u0e2d\u0e31\u0e15\u0e42\u0e19\u0e21\u0e31\u0e15\u0e34 \u0e08\u0e30\u0e1b\u0e23\u0e32\u0e01\u0e0f\u0e2b\u0e25\u0e31\u0e07\u0e08\u0e32\u0e01\u0e40\u0e0b\u0e34\u0e23\u0e4c\u0e1f\u0e40\u0e27\u0e2d\u0e23\u0e4c\u0e40\u0e23\u0e34\u0e48\u0e21\u0e1a\u0e31\u0e19\u0e17\u0e36\u0e01",
        "logs.nocfg.go": "\u0e44\u0e1b\u0e17\u0e35\u0e48",
        "logs.nocfg.link": "\u0e01\u0e32\u0e23\u0e15\u0e31\u0e49\u0e07\u0e04\u0e48\u0e32 \u2192 \u0e2a\u0e20\u0e32\u0e1e\u0e41\u0e27\u0e14\u0e25\u0e49\u0e2d\u0e21",
        "logs.nocfg.set": "\u0e40\u0e1e\u0e37\u0e48\u0e2d\u0e15\u0e31\u0e49\u0e07\u0e04\u0e48\u0e32",
        "ov.status": "\u0e2a\u0e16\u0e32\u0e19\u0e30",
        "ov.uptime": "\u0e40\u0e27\u0e25\u0e32\u0e17\u0e33\u0e07\u0e32\u0e19",
        "ov.model": "\u0e42\u0e21\u0e40\u0e14\u0e25",
        "ov.sessions": "\u0e40\u0e0b\u0e2a\u0e0a\u0e31\u0e19",
        "ov.tokens": "\u0e42\u0e17\u0e40\u0e04\u0e19",
        "ov.usd": "\u0e04\u0e48\u0e32\u0e43\u0e0a\u0e49\u0e08\u0e48\u0e32\u0e22 ($)",
        "ov.ip": "IP \u0e17\u0e35\u0e48\u0e43\u0e0a\u0e49\u0e07\u0e32\u0e19",
        "ov.spam": "\u0e15\u0e23\u0e27\u0e08\u0e08\u0e31\u0e1a\u0e2a\u0e41\u0e1b\u0e21",
        "ov.running": "\U0001f7e2 \u0e01\u0e33\u0e25\u0e31\u0e07\u0e17\u0e33\u0e07\u0e32\u0e19",
        "ov.down": "\U0001f534 \u0e2b\u0e22\u0e38\u0e14",
        "ov.channels": "\u0e0a\u0e48\u0e2d\u0e07\u0e17\u0e32\u0e07",
        "ov.security": "\u0e04\u0e27\u0e32\u0e21\u0e1b\u0e25\u0e2d\u0e14\u0e20\u0e31\u0e22",
        "th.channel": "\u0e0a\u0e48\u0e2d\u0e07\u0e17\u0e32\u0e07",
        "th.status": "\u0e2a\u0e16\u0e32\u0e19\u0e30",
        "th.feature": "\u0e1f\u0e35\u0e40\u0e08\u0e2d\u0e23\u0e4c",
        "sec.rate": "\u0e08\u0e33\u0e01\u0e31\u0e14\u0e2d\u0e31\u0e15\u0e23\u0e32",
        "sec.spam": "\u0e15\u0e23\u0e27\u0e08\u0e08\u0e31\u0e1a\u0e2a\u0e41\u0e1b\u0e21",
        "sec.budget": "\u0e04\u0e27\u0e1a\u0e04\u0e38\u0e21\u0e07\u0e1a",
        "sec.hsts": "HSTS",
        "sec.cors": "CORS \u0e40\u0e02\u0e49\u0e21\u0e07\u0e27\u0e14",
        "sec.apikey": "API Key",
        "bud.today": "\u0e27\u0e31\u0e19\u0e19\u0e35\u0e49",
        "bud.model": "\u0e42\u0e21\u0e40\u0e14\u0e25",
        "bud.tokens": "\u0e42\u0e17\u0e40\u0e04\u0e19\u0e17\u0e35\u0e48\u0e43\u0e0a\u0e49",
        "bud.usd": "\u0e04\u0e48\u0e32\u0e43\u0e0a\u0e49\u0e08\u0e48\u0e32\u0e22 ($)",
        "bud.status": "\u0e2a\u0e16\u0e32\u0e19\u0e30",
        "bud.enabled": "\U0001f6e1\ufe0f \u0e40\u0e1b\u0e34\u0e14\u0e43\u0e0a\u0e49\u0e07\u0e32\u0e19",
        "bud.disabled": "\u26a0\ufe0f \u0e1b\u0e34\u0e14\u0e43\u0e0a\u0e49\u0e07\u0e32\u0e19",
        "bud.token_usage": "\u0e01\u0e32\u0e23\u0e43\u0e0a\u0e49\u0e42\u0e17\u0e40\u0e04\u0e19",
        "bud.usd_usage": "\u0e01\u0e32\u0e23\u0e43\u0e0a\u0e49\u0e08\u0e48\u0e32\u0e22",
        "bud.last7": "7 \u0e27\u0e31\u0e19\u0e17\u0e35\u0e48\u0e1c\u0e48\u0e32\u0e19\u0e21\u0e32",
        "bud.last30": "30 \u0e27\u0e31\u0e19\u0e17\u0e35\u0e48\u0e1c\u0e48\u0e32\u0e19\u0e21\u0e32",
        "bud.budget_on": "\u0e07\u0e1a\u0e1b\u0e23\u0e30\u0e21\u0e32\u0e13\u0e40\u0e1b\u0e34\u0e14",
        "bud.no_cap": "\u0e44\u0e21\u0e48\u0e08\u0e33\u0e01\u0e31\u0e14",
        "bud.tokens_unit": "\u0e42\u0e17\u0e40\u0e04\u0e19",
        "bud.token_usage_today": "\u0e01\u0e32\u0e23\u0e43\u0e0a\u0e49\u0e42\u0e17\u0e40\u0e04\u0e19\u0e27\u0e31\u0e19\u0e19\u0e35\u0e49",
        "bud.usd_usage_today": "\u0e04\u0e48\u0e32\u0e43\u0e0a\u0e49\u0e08\u0e48\u0e32\u0e22\u0e27\u0e31\u0e19\u0e19\u0e35\u0e49",
        "bud.prev_days": "\u0e27\u0e31\u0e19\u0e01\u0e48\u0e2d\u0e19\u0e2b\u0e19\u0e49\u0e32",
        "bud.no_data_period": "\u0e44\u0e21\u0e48\u0e21\u0e35\u0e02\u0e49\u0e2d\u0e21\u0e39\u0e25\u0e43\u0e19\u0e0a\u0e48\u0e27\u0e07\u0e19\u0e35\u0e49",
        "bud.history_total": "\u0e23\u0e27\u0e21",
        "budget.chart.dailySpend30dUsd": "\u0e04\u0e48\u0e32\u0e43\u0e0a\u0e49\u0e08\u0e48\u0e32\u0e22\u0e23\u0e32\u0e22\u0e27\u0e31\u0e19 \u2014 30 \u0e27\u0e31\u0e19\u0e25\u0e48\u0e32\u0e2a\u0e38\u0e14 (USD)",
        "budget.history.title": "\u0e1b\u0e23\u0e30\u0e27\u0e31\u0e15\u0e34\u0e04\u0e48\u0e32\u0e43\u0e0a\u0e49\u0e08\u0e48\u0e32\u0e22",
        "budget.history.filter.7days": "7 \u0e27\u0e31\u0e19",
        "budget.history.filter.30days": "30 \u0e27\u0e31\u0e19",
        "budget.history.filter.all": "\u0e17\u0e31\u0e49\u0e07\u0e2b\u0e21\u0e14",
        "budget.history.header.date": "\u0e27\u0e31\u0e19\u0e17\u0e35\u0e48",
        "budget.history.header.tokensUsed": "\u0e42\u0e17\u0e40\u0e04\u0e19\u0e17\u0e35\u0e48\u0e43\u0e0a\u0e49",
        "budget.history.header.usdSpent": "\u0e04\u0e48\u0e32\u0e43\u0e0a\u0e49\u0e08\u0e48\u0e32\u0e22 ($)",
        "budget.history.header.dailyCapPct": "% \u0e02\u0e2d\u0e07\u0e27\u0e07\u0e40\u0e07\u0e34\u0e19",
        "cfg.llm": "\u0e42\u0e21\u0e40\u0e14\u0e25\u0e20\u0e32\u0e29\u0e32",
        "cfg.rag": "RAG",
        "cfg.conversation": "\u0e01\u0e32\u0e23\u0e2a\u0e19\u0e17\u0e19\u0e32",
        "cfg.rate": "\u0e08\u0e33\u0e01\u0e31\u0e14\u0e2d\u0e31\u0e15\u0e23\u0e32",
        "cfg.spam": "\u0e15\u0e23\u0e27\u0e08\u0e08\u0e31\u0e1a\u0e2a\u0e41\u0e1b\u0e21",
        "cfg.budget_cap": "\u0e07\u0e1a\u0e1b\u0e23\u0e30\u0e21\u0e32\u0e13",
        "cfg.security": "\u0e04\u0e27\u0e32\u0e21\u0e1b\u0e25\u0e2d\u0e14\u0e20\u0e31\u0e22",
        "cfg.general": "\u0e17\u0e31\u0e48\u0e27\u0e44\u0e1b",
        "cfg.secrets": "\u0e04\u0e27\u0e32\u0e21\u0e25\u0e31\u0e1a (\u0e2d\u0e48\u0e32\u0e19\u0e2d\u0e22\u0e48\u0e32\u0e07\u0e40\u0e14\u0e35\u0e22\u0e27)",
        "cfg.enabled": "\u0e40\u0e1b\u0e34\u0e14\u0e43\u0e0a\u0e49\u0e07\u0e32\u0e19",
        "cfg.disabled": "\u0e1b\u0e34\u0e14\u0e43\u0e0a\u0e49\u0e07\u0e32\u0e19",
        "th.session_id": "\u0e23\u0e2b\u0e31\u0e2a\u0e40\u0e0b\u0e2a\u0e0a\u0e31\u0e19",
        "th.messages": "\u0e02\u0e49\u0e2d\u0e04\u0e27\u0e32\u0e21",
        "th.last_active": "\u0e43\u0e0a\u0e49\u0e07\u0e32\u0e19\u0e25\u0e48\u0e32\u0e2a\u0e38\u0e14",
        "th.actions": "\u0e01\u0e32\u0e23\u0e14\u0e33\u0e40\u0e19\u0e34\u0e19\u0e01\u0e32\u0e23",
        "th.file": "\u0e44\u0e1f\u0e25\u0e4c",
        "th.folder": "\u0e42\u0e1f\u0e25\u0e40\u0e14\u0e2d\u0e23\u0e4c",
        "th.size": "\u0e02\u0e19\u0e32\u0e14",
        "onb.welcome": "\u0e22\u0e34\u0e19\u0e14\u0e35\u0e15\u0e49\u0e2d\u0e19\u0e23\u0e31\u0e1a\u0e2a\u0e39\u0e48\u0e41\u0e14\u0e0a\u0e1a\u0e2d\u0e23\u0e4c\u0e14",
        "onb.welcome_sub": "\u0e17\u0e31\u0e27\u0e23\u0e4c\u0e2a\u0e31\u0e49\u0e19 \u2014 \u0e43\u0e0a\u0e49\u0e40\u0e27\u0e25\u0e32 10 \u0e27\u0e34\u0e19\u0e32\u0e17\u0e35",
        "onb.step1_title": "\U0001f4c1 \u0e44\u0e1f\u0e25\u0e4c\u0e02\u0e49\u0e2d\u0e21\u0e39\u0e25",
        "onb.step1_body": "\u0e40\u0e1e\u0e34\u0e48\u0e21\u0e02\u0e49\u0e2d\u0e21\u0e39\u0e25\u0e18\u0e38\u0e23\u0e01\u0e34\u0e08\u0e17\u0e35\u0e48\u0e19\u0e35\u0e48 \u2014 \u0e2a\u0e34\u0e19\u0e04\u0e49\u0e32, \u0e40\u0e27\u0e25\u0e32\u0e40\u0e1b\u0e34\u0e14, \u0e19\u0e42\u0e22\u0e1a\u0e32\u0e22 \u0e41\u0e0a\u0e17\u0e1a\u0e2d\u0e17\u0e08\u0e30\u0e40\u0e23\u0e35\u0e22\u0e19\u0e23\u0e39\u0e49\u0e08\u0e32\u0e01\u0e44\u0e1f\u0e25\u0e4c\u0e40\u0e2b\u0e25\u0e48\u0e32\u0e19\u0e35\u0e49",
        "onb.step2_title": "\U0001f3e2 \u0e02\u0e49\u0e2d\u0e21\u0e39\u0e25\u0e18\u0e38\u0e23\u0e01\u0e34\u0e08",
        "onb.step2_body": "\u0e15\u0e31\u0e49\u0e07\u0e04\u0e48\u0e32\u0e0a\u0e37\u0e48\u0e2d\u0e18\u0e38\u0e23\u0e01\u0e34\u0e08, \u0e2a\u0e16\u0e32\u0e19\u0e17\u0e35\u0e48, \u0e20\u0e32\u0e29\u0e32, \u0e41\u0e25\u0e30\u0e1a\u0e38\u0e04\u0e25\u0e34\u0e01\u0e20\u0e32\u0e1e \u0e1a\u0e2d\u0e17\u0e08\u0e30\u0e23\u0e39\u0e49\u0e27\u0e48\u0e32\u0e15\u0e31\u0e27\u0e40\u0e2d\u0e07\u0e01\u0e33\u0e25\u0e31\u0e07\u0e40\u0e1b\u0e47\u0e19\u0e15\u0e31\u0e27\u0e41\u0e17\u0e19\u0e02\u0e2d\u0e07\u0e43\u0e04\u0e23",
        "onb.step3_title": "\U0001f916 \u0e1b\u0e23\u0e31\u0e1a\u0e41\u0e15\u0e48\u0e07 AI",
        "onb.step3_body": "\u0e1b\u0e23\u0e31\u0e1a\u0e41\u0e15\u0e48\u0e07\u0e42\u0e17\u0e19, \u0e1a\u0e38\u0e04\u0e25\u0e34\u0e01, \u0e41\u0e25\u0e30\u0e23\u0e39\u0e1b\u0e41\u0e1a\u0e1a\u0e01\u0e32\u0e23\u0e15\u0e2d\u0e1a\u0e02\u0e2d\u0e07\u0e1a\u0e2d\u0e17 \u0e1a\u0e38\u0e04\u0e25\u0e34\u0e01\u0e20\u0e32\u0e1e\u0e01\u0e33\u0e2b\u0e19\u0e14\u0e27\u0e34\u0e18\u0e35\u0e17\u0e35\u0e48\u0e1a\u0e2d\u0e17\u0e1e\u0e39\u0e14\u0e01\u0e31\u0e1a\u0e25\u0e39\u0e01\u0e04\u0e49\u0e32\u0e02\u0e2d\u0e07\u0e04\u0e38\u0e13",
        "onb.step4_title": "\U0001f4ca \u0e20\u0e32\u0e1e\u0e23\u0e27\u0e21",
        "onb.step4_body": "\u0e14\u0e39\u0e40\u0e0b\u0e2a\u0e0a\u0e31\u0e19, \u0e07\u0e1a\u0e1b\u0e23\u0e30\u0e21\u0e32\u0e13, \u0e41\u0e25\u0e30\u0e0a\u0e48\u0e2d\u0e07\u0e17\u0e32\u0e07 \u0e02\u0e49\u0e2d\u0e21\u0e39\u0e25\u0e2a\u0e14\u0e17\u0e31\u0e49\u0e07\u0e2b\u0e21\u0e14\u0e43\u0e19\u0e17\u0e35\u0e48\u0e40\u0e14\u0e35\u0e22\u0e27",
        "onb.skip": "\u0e02\u0e49\u0e32\u0e21",
        "onb.next": "\u0e16\u0e31\u0e14\u0e44\u0e1b",
        "onb.prev": "\u0e01\u0e25\u0e31\u0e1a",
        "onb.done": "\u0e40\u0e23\u0e34\u0e48\u0e21\u0e40\u0e25\u0e22",
        "onb.go_data": "\u0e44\u0e1b\u0e44\u0e1f\u0e25\u0e4c\u0e02\u0e49\u0e2d\u0e21\u0e39\u0e25",
        "onb.go_config": "\u0e44\u0e1b\u0e01\u0e32\u0e23\u0e15\u0e31\u0e49\u0e07\u0e04\u0e48\u0e32",
        "cf.basic": "\u0e02\u0e49\u0e2d\u0e21\u0e39\u0e25\u0e1e\u0e37\u0e49\u0e19\u0e10\u0e32\u0e19",
        "cf.client_id": "\u0e23\u0e2b\u0e31\u0e2a\u0e25\u0e39\u0e01\u0e04\u0e49\u0e32",
        "cf.display_name": "\u0e0a\u0e37\u0e48\u0e2d\u0e17\u0e35\u0e48\u0e41\u0e2a\u0e14\u0e07",
        "cf.location": "\u0e17\u0e35\u0e48\u0e15\u0e31\u0e49\u0e07",
        "cf.timezone": "\u0e40\u0e02\u0e15\u0e40\u0e27\u0e25\u0e32",
        "cf.personality": "\u0e1a\u0e38\u0e04\u0e25\u0e34\u0e01\u0e20\u0e32\u0e1e",
        "cf.languages": "\u0e20\u0e32\u0e29\u0e32",
        "cf.lang_primary": "\u0e20\u0e32\u0e29\u0e32\u0e2b\u0e25\u0e31\u0e01",
        "cf.lang_fallback": "\u0e20\u0e32\u0e29\u0e32\u0e2a\u0e33\u0e23\u0e2d\u0e07",
        "cf.langs_offered": "\u0e20\u0e32\u0e29\u0e32\u0e17\u0e35\u0e48\u0e43\u0e2b\u0e49\u0e1a\u0e23\u0e34\u0e01\u0e32\u0e23 (\u0e04\u0e31\u0e48\u0e19\u0e14\u0e49\u0e27\u0e22\u0e40\u0e04\u0e23\u0e37\u0e48\u0e2d\u0e07\u0e2b\u0e21\u0e32\u0e22\u0e08\u0e38\u0e25\u0e20\u0e32\u0e04)",
        "cf.prompt_extra": "\u0e1e\u0e23\u0e2d\u0e21\u0e15\u0e4c\u0e23\u0e30\u0e1a\u0e1a\u0e40\u0e1e\u0e34\u0e48\u0e21\u0e40\u0e15\u0e34\u0e21",
        "cf.prompt_extra_hint": "\u0e02\u0e49\u0e2d\u0e21\u0e39\u0e25\u0e18\u0e38\u0e23\u0e01\u0e34\u0e08\u0e40\u0e1e\u0e34\u0e48\u0e21\u0e40\u0e15\u0e34\u0e21\u0e41\u0e25\u0e30\u0e04\u0e33\u0e41\u0e19\u0e30\u0e19\u0e33\u0e2a\u0e33\u0e2b\u0e23\u0e31\u0e1a AI \u0e02\u0e36\u0e49\u0e19\u0e1a\u0e23\u0e23\u0e17\u0e31\u0e14\u0e43\u0e2b\u0e21\u0e48\u0e44\u0e14\u0e49\u0e15\u0e32\u0e21\u0e1b\u0e01\u0e15\u0e34 \u0e44\u0e21\u0e48\u0e15\u0e49\u0e2d\u0e07\u0e08\u0e31\u0e14\u0e23\u0e39\u0e1b\u0e41\u0e1a\u0e1a\u0e1e\u0e34\u0e40\u0e28\u0e29",
        "cf.greeting_override": "\u0e02\u0e49\u0e2d\u0e04\u0e27\u0e32\u0e21\u0e17\u0e31\u0e01\u0e17\u0e32\u0e22\u0e17\u0e35\u0e48\u0e01\u0e33\u0e2b\u0e19\u0e14\u0e40\u0e2d\u0e07",
        "cf.data_paths": "\u0e40\u0e2a\u0e49\u0e19\u0e17\u0e32\u0e07\u0e02\u0e49\u0e2d\u0e21\u0e39\u0e25",
        "cf.data_paths_hint": "\u0e40\u0e2a\u0e49\u0e19\u0e17\u0e32\u0e07\u0e04\u0e31\u0e48\u0e19\u0e14\u0e49\u0e27\u0e22\u0e08\u0e38\u0e25\u0e20\u0e32\u0e04",
        "cf.channels": "\u0e0a\u0e48\u0e2d\u0e07\u0e17\u0e32\u0e07",
        "cf.editing": "\u0e01\u0e33\u0e25\u0e31\u0e07\u0e41\u0e01\u0e49\u0e44\u0e02",
        "pf.basic": "\u0e02\u0e49\u0e2d\u0e21\u0e39\u0e25\u0e1e\u0e37\u0e49\u0e19\u0e10\u0e32\u0e19",
        "pf.name": "\u0e0a\u0e37\u0e48\u0e2d",
        "pf.temperature": "\u0e2d\u0e38\u0e13\u0e2b\u0e20\u0e39\u0e21\u0e34 (0-1)",
        "pf.description": "\u0e04\u0e33\u0e2d\u0e18\u0e34\u0e1a\u0e32\u0e22",
        "pf.system_prompt": "\u0e1e\u0e23\u0e2d\u0e21\u0e15\u0e4c\u0e23\u0e30\u0e1a\u0e1a",
        "pf.system_prompt_hint": "\u0e1a\u0e38\u0e04\u0e25\u0e34\u0e01\u0e20\u0e32\u0e1e\u0e02\u0e2d\u0e07 AI \u0e40\u0e02\u0e35\u0e22\u0e19\u0e15\u0e32\u0e21\u0e18\u0e23\u0e23\u0e21\u0e0a\u0e32\u0e15\u0e34 \u2014 \u0e23\u0e30\u0e1a\u0e1a\u0e08\u0e30\u0e40\u0e01\u0e47\u0e1a\u0e1a\u0e23\u0e23\u0e17\u0e31\u0e14\u0e43\u0e2b\u0e21\u0e48\u0e44\u0e27\u0e49 \u0e44\u0e21\u0e48\u0e15\u0e49\u0e2d\u0e07\u0e43\u0e2a\u0e48 \\n",
        "pf.messages": "\u0e02\u0e49\u0e2d\u0e04\u0e27\u0e32\u0e21",
        "pf.greeting": "\u0e02\u0e49\u0e2d\u0e04\u0e27\u0e32\u0e21\u0e17\u0e31\u0e01\u0e17\u0e32\u0e22",
        "pf.fallback": "\u0e02\u0e49\u0e2d\u0e04\u0e27\u0e32\u0e21\u0e2a\u0e33\u0e23\u0e2d\u0e07",
        "pf.style_kw": "\u0e04\u0e33\u0e2a\u0e44\u0e15\u0e25\u0e4c",
        "pf.style_kw_hint": "\u0e04\u0e31\u0e48\u0e19\u0e14\u0e49\u0e27\u0e22\u0e08\u0e38\u0e25\u0e20\u0e32\u0e04",
        "nav.section.admin": "\u0e41\u0e2d\u0e14\u0e21\u0e34\u0e19",
        "nav.users": "\u0e1c\u0e39\u0e49\u0e43\u0e0a\u0e49",
        "page.users": "\U0001f465 \u0e1c\u0e39\u0e49\u0e43\u0e0a\u0e49",
        "btn.addUser": "+ \u0e40\u0e1e\u0e34\u0e48\u0e21\u0e1c\u0e39\u0e49\u0e43\u0e0a\u0e49",
        "users.newuser": "\u0e2a\u0e23\u0e49\u0e32\u0e07\u0e1c\u0e39\u0e49\u0e43\u0e0a\u0e49\u0e43\u0e2b\u0e21\u0e48",
        "users.username": "\u0e0a\u0e37\u0e48\u0e2d\u0e1c\u0e39\u0e49\u0e43\u0e0a\u0e49",
        "users.password": "\u0e23\u0e2b\u0e31\u0e2a\u0e1c\u0e48\u0e32\u0e19",
        "users.role": "\u0e1a\u0e17\u0e1a\u0e32\u0e17",
        "users.created_by": "\u0e2a\u0e23\u0e49\u0e32\u0e07\u0e42\u0e14\u0e22",
        "users.role_hint": "\u0e41\u0e2d\u0e14\u0e21\u0e34\u0e19: \u0e40\u0e02\u0e49\u0e32\u0e16\u0e36\u0e07\u0e40\u0e15\u0e47\u0e21\u0e23\u0e39\u0e1b\u0e41\u0e1a\u0e1a \u0e08\u0e31\u0e14\u0e01\u0e32\u0e23\u0e1c\u0e39\u0e49\u0e43\u0e0a\u0e49\u0e44\u0e14\u0e49 \u0e1c\u0e39\u0e49\u0e0a\u0e21: \u0e14\u0e39\u0e44\u0e14\u0e49\u0e2d\u0e22\u0e48\u0e32\u0e07\u0e40\u0e14\u0e35\u0e22\u0e27",
        "nav.section.business": "\u0e18\u0e38\u0e23\u0e01\u0e34\u0e08",
        "nav.products": "\u0e2a\u0e34\u0e19\u0e04\u0e49\u0e32",
        "nav.contacts": "\u0e02\u0e49\u0e2d\u0e04\u0e27\u0e32\u0e21",
        "nav.handoff": "\u0e2a\u0e48\u0e07\u0e15\u0e48\u0e2d",
        "nav.fallback": "\u0e44\u0e21\u0e48\u0e21\u0e35\u0e04\u0e33\u0e15\u0e2d\u0e1a",
        "page.products": "\U0001f6cd\ufe0f \u0e2a\u0e34\u0e19\u0e04\u0e49\u0e32",
        "page.contacts": "\U0001f4e7 \u0e02\u0e49\u0e2d\u0e04\u0e27\u0e32\u0e21",
        "page.handoff": "\U0001f91d \u0e2a\u0e48\u0e07\u0e15\u0e48\u0e2d\u0e40\u0e08\u0e49\u0e32\u0e2b\u0e19\u0e49\u0e32\u0e17\u0e35\u0e48",
        "page.fallback": "\u2753 \u0e04\u0e33\u0e16\u0e32\u0e21\u0e17\u0e35\u0e48\u0e44\u0e21\u0e48\u0e21\u0e35\u0e04\u0e33\u0e15\u0e2d\u0e1a",
        "products.total": "\u0e2a\u0e34\u0e19\u0e04\u0e49\u0e32\u0e17\u0e31\u0e49\u0e07\u0e2b\u0e21\u0e14",
        "products.categories": "\u0e2b\u0e21\u0e27\u0e14\u0e2b\u0e21\u0e39\u0e48",
        "contacts.unread": "\u0e22\u0e31\u0e07\u0e44\u0e21\u0e48\u0e44\u0e14\u0e49\u0e2d\u0e48\u0e32\u0e19",
        "contacts.total": "\u0e02\u0e49\u0e2d\u0e04\u0e27\u0e32\u0e21\u0e17\u0e31\u0e49\u0e07\u0e2b\u0e21\u0e14",
        "fallback.unresolved": "\u0e22\u0e31\u0e07\u0e44\u0e21\u0e48\u0e44\u0e14\u0e49\u0e41\u0e01\u0e49\u0e44\u0e02",
    },
}
