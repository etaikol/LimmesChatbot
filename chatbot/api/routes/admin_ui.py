"""
Admin dashboard HTML/JS.

Single-page application served inline — no build step, no CDN.
Styled with system fonts and a dark sidebar layout.
Communicates with the /admin/api/* endpoints.
"""

from __future__ import annotations


def dashboard_html() -> str:
    return _HTML


_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Chatbot Admin</title>
<style>
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
</style>
</head>
<body>

<!-- Auth -->
<div class="auth-overlay" id="auth">
  <div class="auth-box">
    <div style="font-size:36px;margin-bottom:12px">🔒</div>
    <h2>Admin Dashboard</h2>
    <p>Enter your admin API key to continue</p>
    <input type="password" class="form-input" id="keyInput" placeholder="ADMIN_API_KEY" autofocus>
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
    <div class="nav-section" data-i18n="nav.section.content">Content</div>
    <button class="nav-item" data-page="data" onclick="showPage('data',this)">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>
      <span data-i18n="nav.data">Data Files</span>
    </button>
    <button class="nav-item" data-page="logs" onclick="showPage('logs',this)">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="4 17 10 11 4 5"/><line x1="12" y1="19" x2="20" y2="19"/></svg>
      <span data-i18n="nav.logs">Logs</span>
    </button>
  </div>
  <div class="lang-switcher">
    <button class="lang-btn active" data-lang="en" onclick="setLang('en')" title="English">EN</button>
    <button class="lang-btn" data-lang="he" onclick="setLang('he')" title="עברית">HE</button>
    <button class="lang-btn" data-lang="th" onclick="setLang('th')" title="ภาษาไทย">TH</button>
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
        <h3 style="font-size:14px;color:var(--muted);margin-bottom:10px">Channels</h3>
        <div class="tbl-wrap"><table><thead><tr><th>Channel</th><th>Status</th></tr></thead><tbody id="channelRows"></tbody></table></div>
      </div>
      <div>
        <h3 style="font-size:14px;color:var(--muted);margin-bottom:10px">Security</h3>
        <div class="tbl-wrap"><table><thead><tr><th>Feature</th><th>Status</th></tr></thead><tbody id="securityRows"></tbody></table></div>
      </div>
    </div>
  </div>

  <!-- ═══════ Sessions ═══════ -->
  <div class="page" id="page-sessions">
    <div class="page-title" style="justify-content:space-between">
      <span data-i18n="page.sessions">💬 Sessions</span>
      <div><button class="btn btn-ghost btn-sm" onclick="loadSessions()" data-i18n="btn.refresh">↻ Refresh</button> <button class="btn btn-danger btn-sm" onclick="clearAllSessions()" data-i18n="btn.clearAll">Clear All</button></div>
    </div>
    <div class="tbl-wrap"><table><thead><tr><th>Session ID</th><th>Messages</th><th>Last Activity</th><th>Actions</th></tr></thead><tbody id="sessionRows"></tbody></table></div>
  </div>

  <!-- ═══════ Budget ═══════ -->
  <div class="page" id="page-budget">
    <div class="page-title" style="justify-content:space-between">
      <span data-i18n="page.budget">💰 Budget</span>
      <button class="btn btn-danger btn-sm" onclick="resetBudget()" data-i18n="btn.resetToday">Reset Today</button>
    </div>
    <div class="cards" id="budgetCards"></div>
    <div id="budgetBars"></div>
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
        <button class="btn btn-primary" onclick="saveEnv()" data-i18n="btn.saveEnv">Save Environment Settings</button>
        <span style="font-size:11px;color:var(--muted)" data-i18n="restart.note">Restart required for changes to take effect</span>
      </div>
    </div>

    <!-- Client -->
    <div class="config-panel" id="cfg-client" style="display:none">
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:16px">
        <span style="font-size:13px;color:var(--muted)">Editing: <strong id="clientFile"></strong></span>
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
        <span style="font-size:13px;color:var(--muted)">Editing: <strong id="personalityFile"></strong></span>
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
    <div id="lineNotConfigured" style="display:none">
      <div class="card" style="padding:24px;text-align:center">
        <div style="font-size:36px;margin-bottom:12px">📱</div>
        <h3 style="margin-bottom:8px" data-i18n="line.nocfg.title">LINE Not Configured</h3>
        <p style="color:var(--muted);font-size:13px;margin-bottom:16px" data-i18n="line.nocfg.body">Set <code style="background:var(--bg3);padding:2px 6px;border-radius:4px">LINE_CHANNEL_ACCESS_TOKEN</code> and <code style="background:var(--bg3);padding:2px 6px;border-radius:4px">LINE_CHANNEL_SECRET</code> in your .env file to enable LINE integration.</p>
        <p style="color:var(--muted);font-size:12px">Go to <a href="#" onclick="showPage('config',document.querySelector('[data-page=config]'));return false">Configuration</a> to set these.</p>
      </div>
    </div>
    <div id="lineConfigured" style="display:none">
      <div class="cards" id="lineStatusCards"></div>
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
        <button class="btn btn-primary btn-sm" onclick="showNewFileForm()" data-i18n="btn.newFile">+ New File</button>
      </div>
    </div>
    <p style="font-size:12px;color:var(--muted);margin-bottom:16px" data-i18n="data.hint">Knowledge base files for the chatbot. Edit content, then re-ingest to update the vector store.</p>

    <!-- Upload -->
    <div class="upload-zone" id="uploadZone" onclick="document.getElementById('fileUploadInput').click()" style="margin-bottom:16px">
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
    <div class="tbl-wrap"><table><thead><tr><th>File</th><th>Folder</th><th>Size</th><th>Actions</th></tr></thead><tbody id="dataFileRows"></tbody></table></div>

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

</div>

<div class="toast" id="toast"></div>

<script>
(function(){
"use strict";

// ── i18n ─────────────────────────────────────────────────────────────
var LANGS={
  en:{
    'nav.overview':'Overview','nav.sessions':'Sessions','nav.budget':'Budget','nav.config':'Configuration',
    'nav.line':'LINE','nav.data':'Data Files','nav.logs':'Logs',
    'nav.section.channels':'Channels','nav.section.content':'Content',
    'page.overview':'📊 Overview','page.sessions':'💬 Sessions','page.budget':'💰 Budget',
    'page.config':'⚙️ Configuration','page.line':'💬 LINE Channel','page.data':'📁 Data Files','page.logs':'📋 Logs',
    'cfg.tab.env':'Environment','cfg.tab.client':'Client','cfg.tab.personality':'Personality',
    'btn.refresh':'↻ Refresh','btn.clearAll':'Clear All','btn.resetToday':'Reset Today',
    'btn.saveEnv':'Save Environment Settings','btn.saveClient':'Save Client Config','btn.savePersonality':'Save Personality Config',
    'btn.newFile':'+ New File','btn.create':'Create','btn.cancel':'Cancel','btn.closeEditor':'✕ Close',
    'view.form':'Form','view.yaml':'YAML','view.visual':'Visual','view.markdown':'Markdown',
    'restart.note':'Restart required for changes to take effect',
    'data.hint':'Knowledge base files for the chatbot. Edit content, then re-ingest to update the vector store.',
    'data.upload.cta':'<strong>Click to upload</strong> or drag files here',
    'data.upload.hint':'.md, .txt files — UTF-8 only','data.newfile':'Create New Data File',
    'line.nocfg.title':'LINE Not Configured',
    'line.nocfg.body':'Set LINE_CHANNEL_ACCESS_TOKEN and LINE_CHANNEL_SECRET in your .env file to enable LINE integration.',
    'logs.nocfg.title':'Log File Not Configured',
    'logs.nocfg.body':'Log file is auto-configured. It will appear after the server starts logging.',
    'logs.nocfg.go':'Go to','logs.nocfg.link':'Configuration → Environment','logs.nocfg.set':'to set this.',
  },
  he:{
    'nav.overview':'סקירה','nav.sessions':'שיחות','nav.budget':'תקציב','nav.config':'הגדרות',
    'nav.line':'LINE','nav.data':'קבצי מידע','nav.logs':'לוגים',
    'nav.section.channels':'ערוצים','nav.section.content':'תוכן',
    'page.overview':'📊 סקירה כללית','page.sessions':'💬 שיחות','page.budget':'💰 תקציב',
    'page.config':'⚙️ הגדרות','page.line':'💬 ערוץ LINE','page.data':'📁 קבצי מידע','page.logs':'📋 לוגים',
    'cfg.tab.env':'סביבה','cfg.tab.client':'לקוח','cfg.tab.personality':'אישיות',
    'btn.refresh':'↻ רענן','btn.clearAll':'נקה הכל','btn.resetToday':'אפס להיום',
    'btn.saveEnv':'שמור הגדרות סביבה','btn.saveClient':'שמור הגדרות לקוח','btn.savePersonality':'שמור הגדרות אישיות',
    'btn.newFile':'+ קובץ חדש','btn.create':'צור','btn.cancel':'ביטול','btn.closeEditor':'✕ סגור',
    'view.form':'טופס','view.yaml':'YAML','view.visual':'ויזואלי','view.markdown':'Markdown',
    'restart.note':'נדרש הפעלה מחדש ליישום השינויים',
    'data.hint':'קבצי בסיס ידע לצ\'אטבוט. ערוך תוכן ואז הכנס מחדש לעדכון מאגר הווקטורים.',
    'data.upload.cta':'<strong>לחץ להעלאה</strong> או גרור קבצים לכאן',
    'data.upload.hint':'קבצי .md, .txt — UTF-8 בלבד','data.newfile':'צור קובץ מידע חדש',
    'line.nocfg.title':'LINE לא מוגדר',
    'line.nocfg.body':'הגדר LINE_CHANNEL_ACCESS_TOKEN ו-LINE_CHANNEL_SECRET בקובץ ה-.env שלך.',
    'logs.nocfg.title':'קובץ לוג טרם נוצר',
    'logs.nocfg.body':'קובץ הלוג מוגדר אוטומטית. הוא יופיע לאחר שהשרת יתחיל לרשום לוגים.',
    'logs.nocfg.go':'עבור ל','logs.nocfg.link':'הגדרות ← סביבה','logs.nocfg.set':'להגדרה.',
  },
  th:{
    'nav.overview':'ภาพรวม','nav.sessions':'เซสชัน','nav.budget':'งบประมาณ','nav.config':'การตั้งค่า',
    'nav.line':'LINE','nav.data':'ไฟล์ข้อมูล','nav.logs':'บันทึก',
    'nav.section.channels':'ช่องทาง','nav.section.content':'เนื้อหา',
    'page.overview':'📊 ภาพรวม','page.sessions':'💬 เซสชัน','page.budget':'💰 งบประมาณ',
    'page.config':'⚙️ การตั้งค่า','page.line':'💬 ช่อง LINE','page.data':'📁 ไฟล์ข้อมูล','page.logs':'📋 บันทึก',
    'cfg.tab.env':'สภาพแวดล้อม','cfg.tab.client':'ลูกค้า','cfg.tab.personality':'บุคลิกภาพ',
    'btn.refresh':'↻ รีเฟรช','btn.clearAll':'ล้างทั้งหมด','btn.resetToday':'รีเซ็ตวันนี้',
    'btn.saveEnv':'บันทึกการตั้งค่าสภาพแวดล้อม','btn.saveClient':'บันทึกการตั้งค่าลูกค้า','btn.savePersonality':'บันทึกการตั้งค่าบุคลิกภาพ',
    'btn.newFile':'+ ไฟล์ใหม่','btn.create':'สร้าง','btn.cancel':'ยกเลิก','btn.closeEditor':'✕ ปิด',
    'view.form':'ฟอร์ม','view.yaml':'YAML','view.visual':'ภาพ','view.markdown':'Markdown',
    'restart.note':'ต้องรีสตาร์ทเพื่อให้การเปลี่ยนแปลงมีผล',
    'data.hint':'ไฟล์ฐานความรู้สำหรับแชทบอท แก้ไขเนื้อหา จากนั้นฝังข้อมูลใหม่เพื่ออัปเดต',
    'data.upload.cta':'<strong>คลิกเพื่ออัปโหลด</strong> หรือลากไฟล์มาวาง',
    'data.upload.hint':'ไฟล์ .md, .txt — UTF-8 เท่านั้น','data.newfile':'สร้างไฟล์ข้อมูลใหม่',
    'line.nocfg.title':'ยังไม่ได้ตั้งค่า LINE',
    'line.nocfg.body':'ตั้งค่า LINE_CHANNEL_ACCESS_TOKEN และ LINE_CHANNEL_SECRET ใน .env ของคุณ',
    'logs.nocfg.title':'ยังไม่ได้สร้างไฟล์บันทึก',
    'logs.nocfg.body':'ไฟล์บันทึกถูกตั้งค่าอัตโนมัติ จะปรากฏหลังจากเซิร์ฟเวอร์เริ่มบันทึก',
    'logs.nocfg.go':'ไปที่','logs.nocfg.link':'การตั้งค่า → สภาพแวดล้อม','logs.nocfg.set':'เพื่อตั้งค่า',
  }
};
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
};
function initLang(){setLang(localStorage.getItem('admin_lang')||'en')}

var KEY='',BASE=window.location.origin+'/admin/api';

// ── Auth ──────────────────────────────────────────────────────────────
window.tryLogin=async function(){
  var k=document.getElementById('keyInput').value.trim();
  if(!k){document.getElementById('authErr').textContent='Key required';document.getElementById('authErr').style.display='block';return}
  KEY=k;
  try{
    var r=await api('/overview');
    document.getElementById('auth').style.display='none';
    document.getElementById('sidebar').style.display='flex';
    document.getElementById('mainContent').style.display='block';
    initLang();
    renderOverview(r);
  }catch(e){document.getElementById('authErr').textContent=e.message||'Authentication failed';document.getElementById('authErr').style.display='block';KEY=''}
};
document.getElementById('keyInput').addEventListener('keydown',function(e){if(e.key==='Enter')tryLogin()});

// ── API ───────────────────────────────────────────────────────────────
async function api(path,opts){
  opts=opts||{};
  var headers={'X-Admin-Key':KEY};
  if(opts.body&&!opts.raw)headers['Content-Type']='application/json';
  var fo={method:opts.method||'GET',headers:headers};
  if(opts.body)fo.body=opts.raw?opts.body:JSON.stringify(opts.body);
  var r=await fetch(BASE+path,fo);
  if(!r.ok){var e=await r.json().catch(function(){return{detail:'Request failed'}});throw new Error(e.detail||'Error '+r.status)}
  return r.json();
}
async function apiUpload(path,fd){
  var r=await fetch(BASE+path,{method:'POST',headers:{'X-Admin-Key':KEY},body:fd});
  if(!r.ok){var e=await r.json().catch(function(){return{detail:'Upload failed'}});throw new Error(e.detail||'Error '+r.status)}
  return r.json();
}

// ── Nav ───────────────────────────────────────────────────────────────
window.showPage=function(id,btn){
  document.querySelectorAll('.page').forEach(function(p){p.classList.remove('active')});
  document.querySelectorAll('.nav-item').forEach(function(n){n.classList.remove('active')});
  document.getElementById('page-'+id).classList.add('active');
  if(btn)btn.classList.add('active');
  var loaders={overview:loadOverviewData,sessions:loadSessions,budget:loadBudget,config:loadConfig,line:loadLine,data:loadDataFiles,logs:loadLogs};
  if(loaders[id])loaders[id]();
};

// ── Overview ──────────────────────────────────────────────────────────
async function loadOverviewData(){try{renderOverview(await api('/overview'))}catch(e){toast(e.message,'err')}}
function renderOverview(d){
  var b=d.budget||{};
  var html=card('Status',d.status==='running'?'🟢 Running':'🔴 Down','')+card('Uptime',d.uptime,'')+card('Model',d.model,d.provider)+card('Sessions',d.sessions.active,d.sessions.backend)+card('Tokens',b.tokens_used?b.tokens_used.toLocaleString():'0','of '+(b.daily_token_cap||0).toLocaleString())+card('USD Spent','$'+(b.usd_used||0).toFixed(4),'of $'+(b.daily_usd_cap||0).toFixed(2))+card('IP Buckets',d.rate_limiting.active_ip_buckets,d.rate_limiting.ip_per_minute+'/min')+card('Spam Trackers',d.spam_detection.active_trackers,d.spam_detection.max_strikes+' strikes');
  document.getElementById('overviewCards').innerHTML=html;
  var ch=d.channels,cr='';['web','whatsapp','telegram','line'].forEach(function(c){cr+='<tr><td style="text-transform:capitalize">'+c+'</td><td>'+(ch[c]?'<span class="tag tag-on">ON</span>':'<span class="tag tag-off">OFF</span>')+'</td></tr>'});
  document.getElementById('channelRows').innerHTML=cr;
  var sec=d.security,sr='';
  sr+='<tr><td>Rate Limiting</td><td>'+(d.rate_limiting.enabled?'<span class="tag tag-on">ON</span>':'<span class="tag tag-off">OFF</span>')+'</td></tr>';
  sr+='<tr><td>Spam Detection</td><td>'+(d.spam_detection.enabled?'<span class="tag tag-on">ON</span>':'<span class="tag tag-off">OFF</span>')+'</td></tr>';
  sr+='<tr><td>Budget Guard</td><td>'+(b.enabled?'<span class="tag tag-on">ON</span>':'<span class="tag tag-off">OFF</span>')+'</td></tr>';
  sr+='<tr><td>HSTS</td><td>'+(sec.hsts_enabled?'<span class="tag tag-on">ON</span>':'<span class="tag tag-off">OFF</span>')+'</td></tr>';
  sr+='<tr><td>Strict CORS</td><td>'+(sec.strict_cors?'<span class="tag tag-on">ON</span>':'<span class="tag tag-off">OFF</span>')+'</td></tr>';
  sr+='<tr><td>API Key</td><td>'+(sec.api_key_set?'<span class="tag tag-on">SET</span>':'<span class="tag tag-off">NOT SET</span>')+'</td></tr>';
  document.getElementById('securityRows').innerHTML=sr;
}
function card(l,v,s){return'<div class="card"><div class="card-label">'+l+'</div><div class="card-value">'+v+'</div>'+(s?'<div class="card-sub">'+s+'</div>':'')+'</div>'}

// ── Sessions ──────────────────────────────────────────────────────────
window.loadSessions=async function(){
  try{var d=await api('/sessions');var html='';
  if(!d.sessions.length)html='<tr><td colspan="4" style="text-align:center;color:var(--muted)">No sessions</td></tr>';
  d.sessions.forEach(function(s){var ts=s.last_activity?new Date(s.last_activity).toLocaleString():'—';html+='<tr><td style="font-family:monospace;font-size:12px">'+esc(s.session_id)+'</td><td>'+s.message_count+'</td><td>'+ts+'</td><td><button class="btn btn-ghost btn-sm" onclick="viewSession(\''+esc(s.session_id)+'\')">View</button> <button class="btn btn-danger btn-sm" onclick="deleteSession(\''+esc(s.session_id)+'\')">Delete</button></td></tr>'});
  document.getElementById('sessionRows').innerHTML=html}catch(e){toast(e.message,'err')}
};
window.viewSession=async function(id){try{var d=await api('/sessions/'+encodeURIComponent(id));var html='<div class="modal-bg" onclick="if(event.target===this)this.remove()"><div class="modal"><div class="modal-head"><h3>Session: '+esc(id.slice(0,20))+(id.length>20?'…':'')+'</h3><button class="btn btn-ghost btn-sm" onclick="this.closest(\'.modal-bg\').remove()">&times;</button></div><div class="modal-body">';if(!d.messages.length)html+='<p style="color:var(--muted)">No messages</p>';d.messages.forEach(function(m){var role=m.role||m.type||'unknown';html+='<div class="msg-row '+(role==='human'?'human':'ai')+'"><div class="msg-role">'+role+'</div><div class="msg-text">'+esc(m.content||m.text||'')+'</div></div>'});html+='</div></div></div>';document.body.insertAdjacentHTML('beforeend',html)}catch(e){toast(e.message,'err')}};
window.deleteSession=async function(id){if(!confirm('Delete session '+id+'?'))return;try{await api('/sessions/'+encodeURIComponent(id),{method:'DELETE'});toast('Session deleted','ok');loadSessions()}catch(e){toast(e.message,'err')}};
window.clearAllSessions=async function(){if(!confirm('Clear ALL sessions?'))return;try{var d=await api('/sessions',{method:'DELETE'});toast('Cleared '+d.cleared+' sessions','ok');loadSessions()}catch(e){toast(e.message,'err')}};

// ── Budget ────────────────────────────────────────────────────────────
async function loadBudget(){try{var d=await api('/budget');var tc=d.daily_token_cap||1,uc=d.daily_usd_cap||1;var tp=Math.min(100,Math.round(d.tokens_used/tc*100)),up=Math.min(100,Math.round(d.usd_used/uc*100));document.getElementById('budgetCards').innerHTML=card('Today','📅 '+d.day,'')+card('Model',d.model,'')+card('Tokens Used',d.tokens_used.toLocaleString(),'/ '+tc.toLocaleString())+card('USD Spent','$'+d.usd_used.toFixed(4),'/ $'+d.daily_usd_cap.toFixed(2))+card('Status',d.enabled?'🛡️ Enabled':'⚠️ Disabled','');document.getElementById('budgetBars').innerHTML='<div class="card" style="margin-bottom:16px"><div class="card-label">Token Usage ('+tp+'%)</div><div class="progress"><div class="progress-fill" style="width:'+tp+'%;background:'+(tp>80?'var(--danger)':tp>50?'var(--warn)':'var(--success)')+'"></div></div></div><div class="card"><div class="card-label">USD Usage ('+up+'%)</div><div class="progress"><div class="progress-fill" style="width:'+up+'%;background:'+(up>80?'var(--danger)':up>50?'var(--warn)':'var(--success)')+'"></div></div></div>'}catch(e){toast(e.message,'err')}}
window.resetBudget=async function(){if(!confirm('Reset budget?'))return;try{await api('/budget/reset',{method:'POST'});toast('Budget reset','ok');loadBudget()}catch(e){toast(e.message,'err')}};

// ══════════════════════════════════════════════════════════════════════
// Configuration
// ══════════════════════════════════════════════════════════════════════
var cfgCache={};
async function loadConfig(){try{var d=await api('/config');cfgCache=d;buildEnvForm(d.env);document.getElementById('clientFile').textContent=d.client_file;document.getElementById('personalityFile').textContent=d.personality_file;document.getElementById('clientYaml').value=yamlStringify(d.client);document.getElementById('personalityYaml').value=yamlStringify(d.personality);buildClientForm(d.client);buildPersonalityForm(d.personality)}catch(e){toast(e.message,'err')}}

var ENV_GROUPS=[
  {label:'LLM',keys:['LLM_PROVIDER','LLM_MODEL','LLM_TEMPERATURE']},
  {label:'RAG',keys:['EMBEDDING_MODEL','CHUNK_SIZE','CHUNK_OVERLAP','RETRIEVAL_K']},
  {label:'Conversation',keys:['MAX_HISTORY_TURNS','MAX_MESSAGE_CHARS']},
  {label:'Rate Limiting',keys:['RATE_LIMIT_ENABLED','RATE_LIMIT_IP_PER_MINUTE','RATE_LIMIT_IP_BURST','RATE_LIMIT_SESSION_PER_MINUTE','RATE_LIMIT_SESSION_BURST']},
  {label:'Spam Detection',keys:['SPAM_DETECTION_ENABLED','SPAM_MAX_STRIKES','SPAM_COOLDOWN_SECONDS']},
  {label:'Budget',keys:['DAILY_TOKEN_CAP','DAILY_USD_CAP']},
  {label:'Security',keys:['API_CORS_ORIGINS','API_STRICT_CORS','API_HSTS_ENABLED']},
  {label:'General',keys:['ACTIVE_CLIENT','LOG_LEVEL','DEBUG']}
];

function buildEnvForm(env){
  var html='';
  ENV_GROUPS.forEach(function(g){
    html+='<div class="cfg-card"><h4>'+g.label+'</h4><div class="cfg-grid">';
    g.keys.forEach(function(k){var v=env[k];if(v===undefined)return;
      if(typeof v==='boolean'){html+='<div class="form-group"><label class="form-label">'+k+'</label><label style="display:flex;align-items:center;gap:8px;cursor:pointer"><input type="checkbox" data-env="'+k+'" '+(v?'checked':'')+' style="width:18px;height:18px;accent-color:var(--accent)"><span style="font-size:13px">'+(v?'Enabled':'Disabled')+'</span></label></div>'}
      else{html+='<div class="form-group"><label class="form-label">'+k+'</label><input class="form-input" data-env="'+k+'" value="'+esc(String(v))+'"></div>'}
    });html+='</div></div>';
  });
  var secrets=Object.keys(env).filter(function(k){return k.startsWith('_')&&k.endsWith('_SET')});
  if(secrets.length){html+='<div class="cfg-card"><h4>Secrets (read-only)</h4><div class="cfg-grid">';secrets.forEach(function(k){var label=k.replace(/^_/,'').replace(/_SET$/,'');html+='<div class="form-group"><label class="form-label">'+label+'</label>'+(env[k]?'<span class="tag tag-on">SET</span>':'<span class="tag tag-off">NOT SET</span>')+'</div>'});html+='</div></div>'}
  document.getElementById('envForm').innerHTML=html;
}

window.saveEnv=async function(){var body={};document.querySelectorAll('[data-env]').forEach(function(el){body[el.dataset.env]=el.type==='checkbox'?el.checked:el.value});try{var r=await api('/config/env',{method:'PUT',body:body});var msg='Settings saved.';if(r.rejected&&Object.keys(r.rejected).length)msg+=' Rejected: '+Object.keys(r.rejected).join(', ');toast(msg,'ok')}catch(e){toast(e.message,'err')}};

window.showConfigTab=function(tab,btn){
  document.querySelectorAll('#page-config .config-panel').forEach(function(p){p.style.display='none'});
  document.querySelectorAll('#page-config > .tab-bar .tab-btn').forEach(function(b){b.classList.remove('active')});
  document.getElementById('cfg-'+tab).style.display='block';btn.classList.add('active');
};

// ── Client Form ───────────────────────────────────────────────────────
function buildClientForm(d){
  if(!d)return;var h='';
  h+='<div class="cfg-card"><h4>Basic Info</h4><div class="cfg-grid">';
  h+=ff('cl','id',d.id,'Client ID');h+=ff('cl','name',d.name,'Display Name');
  h+=ff('cl','location',d.location,'Location');h+=ff('cl','timezone',d.timezone,'Timezone');
  h+=ff('cl','personality',d.personality,'Personality');h+='</div></div>';
  h+='<div class="cfg-card"><h4>Languages</h4><div class="cfg-grid">';
  h+=ff('cl','language_primary',d.language_primary,'Primary Language');
  h+=ff('cl','language_fallback',d.language_fallback,'Fallback Language');
  h+='</div><div class="form-group" style="margin-top:8px"><label class="form-label">Languages Offered (comma-separated)</label><input class="form-input" data-cl="languages_offered" value="'+esc((d.languages_offered||[]).join(', '))+'"></div></div>';
  h+='<div class="cfg-card"><h4>System Prompt Extra</h4><p style="font-size:11px;color:var(--muted);margin-bottom:8px">Additional business info and instructions for the AI. Line breaks work naturally — no special formatting needed.</p><div class="form-group"><textarea class="field-multiline" data-cl="system_prompt_extra" rows="8" style="min-height:150px;font-family:system-ui">'+esc(d.system_prompt_extra||'')+'</textarea></div></div>';
  if(d.greeting_override!==undefined){h+='<div class="cfg-card"><h4>Greeting Override</h4><div class="form-group"><textarea class="field-multiline" data-cl="greeting_override" rows="3">'+esc(d.greeting_override||'')+'</textarea></div></div>'}
  if(d.data_paths){h+='<div class="cfg-card"><h4>Data Paths</h4><div class="form-group"><label class="form-label">Comma-separated paths</label><input class="form-input" data-cl="data_paths" value="'+esc((d.data_paths||[]).join(', '))+'"></div></div>'}
  if(d.channels){h+='<div class="cfg-card"><h4>Channels</h4><div class="cfg-grid">';Object.keys(d.channels).forEach(function(ch){var en=d.channels[ch]&&d.channels[ch].enabled;h+='<div class="form-group"><label class="form-label" style="text-transform:capitalize">'+ch+'</label><label style="display:flex;align-items:center;gap:8px;cursor:pointer"><input type="checkbox" data-cl-ch="'+ch+'" '+(en?'checked':'')+' style="width:18px;height:18px;accent-color:var(--accent)"><span style="font-size:13px">'+(en?'Enabled':'Disabled')+'</span></label></div>'});h+='</div></div>'}
  document.getElementById('clientFormFields').innerHTML=h;
}

window.saveClientForm=async function(){
  var d={};document.querySelectorAll('[data-cl]').forEach(function(el){var k=el.dataset.cl;if(k==='languages_offered'||k==='data_paths')d[k]=el.value.split(',').map(function(s){return s.trim()}).filter(Boolean);else d[k]=el.value});
  var ch={};document.querySelectorAll('[data-cl-ch]').forEach(function(el){ch[el.dataset.clCh]={enabled:el.checked}});if(Object.keys(ch).length)d.channels=ch;
  try{await api('/config/client',{method:'PUT',body:d});toast('Client config saved','ok')}catch(e){toast(e.message,'err')}
};
window.setClientView=function(v,btn){document.getElementById('clientFormView').style.display=v==='form'?'block':'none';document.getElementById('clientYamlView').style.display=v==='yaml'?'block':'none';btn.parentElement.querySelectorAll('.tab-btn').forEach(function(b){b.classList.remove('active')});btn.classList.add('active')};

// ── Personality Form ──────────────────────────────────────────────────
function buildPersonalityForm(d){
  if(!d)return;var h='';
  h+='<div class="cfg-card"><h4>Basic Info</h4><div class="cfg-grid">';
  h+=ff('pers','name',d.name,'Name');h+=ff('pers','temperature',d.temperature||0.7,'Temperature (0-1)');
  h+='</div></div>';
  h+='<div class="cfg-card"><h4>Description</h4><div class="form-group"><textarea class="field-multiline" data-pers="description" rows="3">'+esc(d.description||'')+'</textarea></div></div>';
  h+='<div class="cfg-card"><h4>System Prompt</h4><p style="font-size:11px;color:var(--muted);margin-bottom:8px">The AI personality. Write naturally — line breaks are preserved. No \\n needed.</p><div class="form-group"><textarea class="field-multiline" data-pers="system_prompt" rows="12" style="min-height:200px;font-family:system-ui">'+esc(d.system_prompt||'')+'</textarea></div></div>';
  h+='<div class="cfg-card"><h4>Messages</h4><div class="cfg-grid">';
  h+='<div class="form-group"><label class="form-label">Greeting</label><textarea class="field-multiline" data-pers="greeting" rows="2" style="min-height:60px">'+esc(d.greeting||'')+'</textarea></div>';
  h+='<div class="form-group"><label class="form-label">Fallback Message</label><textarea class="field-multiline" data-pers="fallback_message" rows="2" style="min-height:60px">'+esc(d.fallback_message||'')+'</textarea></div>';
  h+='</div></div>';
  h+='<div class="cfg-card"><h4>Style Keywords</h4><div class="form-group"><label class="form-label">Comma-separated</label><input class="form-input" data-pers="style_keywords" value="'+esc((d.style_keywords||[]).join(', '))+'"></div></div>';
  document.getElementById('personalityFormFields').innerHTML=h;
}

window.savePersonalityForm=async function(){
  var d={};document.querySelectorAll('[data-pers]').forEach(function(el){var k=el.dataset.pers;if(k==='style_keywords')d[k]=el.value.split(',').map(function(s){return s.trim()}).filter(Boolean);else if(k==='temperature')d[k]=parseFloat(el.value)||0.7;else d[k]=el.value});
  try{await api('/config/personality',{method:'PUT',body:d});toast('Personality config saved','ok')}catch(e){toast(e.message,'err')}
};
window.setPersonalityView=function(v,btn){document.getElementById('personalityFormView').style.display=v==='form'?'block':'none';document.getElementById('personalityYamlView').style.display=v==='yaml'?'block':'none';btn.parentElement.querySelectorAll('.tab-btn').forEach(function(b){b.classList.remove('active')});btn.classList.add('active')};

window.saveYaml=async function(type){var text=document.getElementById(type==='client'?'clientYaml':'personalityYaml').value;var body;try{body=yamlParse(text)}catch(e){toast('Invalid YAML: '+e.message,'err');return}try{await api('/config/'+type,{method:'PUT',body:body});toast(type+' config saved','ok');loadConfig()}catch(e){toast(e.message,'err')}};

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

var EMOJI_CATS=[
  {l:'⚡ Quick',e:['✅','❌','⚠️','🔥','💡','⭐','👍','❤️','🎉','💯','✨','🌟','💫','🎯','📌','🔑']},
  {l:'🌿 Nature',e:['🌿','🍃','🌱','☘️','🍀','🌾','🌸','🌺','🌻','🌼','💐','🌲','🌳','🌴','🪴','🎋','🌵','🎍']},
  {l:'💨 Smoke',e:['💨','🌫️','🫧','♨️','🔥','🚬','🚭','🏮','💭','🌡️','🧪','⚗️','🌪️','💥','🕯️','🪔']},
  {l:'😊 People',e:['😊','😄','😎','🤗','😍','🥰','😌','🤙','👋','🤝','👏','💪','🙏','👌','🫶','💚','💜','🧡','💛','💙']},
  {l:'🏪 Business',e:['🛒','🏪','🏠','🏢','🏬','📦','🚚','💰','💳','🎁','💼','📋','📍','🗺️','🏅','🏷️','📊','🔒']},
  {l:'⏰ Time & Info',e:['🕑','🕐','⏰','📅','📆','🗓️','🔔','📢','ℹ️','💬','📱','✉️','📞','☎️','📣','📝','🔍']},
];
window.emojiPick=function(editorId,ev){
  var old=document.querySelector('.emoji-picker');if(old)old.remove();
  var p=document.createElement('div');p.className='emoji-picker';
  EMOJI_CATS.forEach(function(cat){
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
  document.getElementById('editingFileName').textContent='Editing: '+path;
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
// LINE
// ══════════════════════════════════════════════════════════════════════
async function loadLine(){
  try{var s=await api('/line/status');
  if(!s.configured){document.getElementById('lineNotConfigured').style.display='block';document.getElementById('lineConfigured').style.display='none';return}
  document.getElementById('lineNotConfigured').style.display='none';document.getElementById('lineConfigured').style.display='block';
  document.getElementById('lineStatusCards').innerHTML=card('LINE','🟢 Active','')+card('Secret',s.channel_secret_set?'✅ Set':'❌ Missing','')+card('Token','✅ Set','')+card('Webhook',esc(s.webhook_url),'');
  loadLineMenus()}catch(e){toast(e.message,'err')}
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

})();
</script>
</body>
</html>"""
