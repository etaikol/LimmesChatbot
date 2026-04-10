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
.sidebar-nav{flex:1;padding:12px 8px;display:flex;flex-direction:column;gap:2px}
.nav-item{display:flex;align-items:center;gap:10px;padding:10px 14px;border-radius:8px;color:var(--muted);font-size:14px;font-weight:500;border:none;background:none;text-align:left;width:100%;transition:all .15s}
.nav-item:hover{background:var(--bg3);color:var(--fg)}
.nav-item.active{background:rgba(14,165,233,.15);color:var(--accent)}
.nav-item svg{width:18px;height:18px;flex-shrink:0}

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

/* Toast */
.toast{position:fixed;bottom:24px;right:24px;padding:12px 20px;border-radius:10px;font-size:13px;font-weight:600;color:#fff;z-index:9999;opacity:0;transform:translateY(10px);transition:all .25s}
.toast.show{opacity:1;transform:none}
.toast-ok{background:var(--success)}.toast-err{background:var(--danger)}.toast-warn{background:var(--warn)}

/* Progress bar */
.progress{height:8px;background:var(--bg3);border-radius:4px;overflow:hidden;margin-top:8px}
.progress-fill{height:100%;border-radius:4px;transition:width .3s}

/* Key-value block */
.kv{display:grid;grid-template-columns:200px 1fr;gap:1px;background:var(--border);border-radius:var(--radius);overflow:hidden;margin-bottom:20px}
.kv dt,.kv dd{padding:10px 14px;background:var(--card);font-size:13px}
.kv dt{color:var(--muted);font-weight:600}

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

/* Session detail modal */
.modal-bg{position:fixed;inset:0;background:rgba(0,0,0,.6);z-index:100;display:flex;align-items:center;justify-content:center}
.modal{background:var(--card);border:1px solid var(--border);border-radius:16px;width:600px;max-width:90vw;max-height:85vh;display:flex;flex-direction:column;box-shadow:var(--shadow)}
.modal-head{padding:16px 20px;border-bottom:1px solid var(--border);display:flex;align-items:center;justify-content:space-between}
.modal-head h3{font-size:16px}
.modal-body{flex:1;overflow-y:auto;padding:20px}
.msg-row{margin-bottom:12px;display:flex;flex-direction:column;gap:4px}
.msg-role{font-size:11px;font-weight:700;text-transform:uppercase;color:var(--muted)}
.msg-text{padding:10px 14px;border-radius:12px;font-size:13px;line-height:1.55;white-space:pre-wrap}
.msg-row.human .msg-text{background:var(--bg3);align-self:flex-end;max-width:85%}
.msg-row.ai .msg-text{background:rgba(14,165,233,.1);align-self:flex-start;max-width:85%}
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
      <span>Overview</span>
    </button>
    <button class="nav-item" data-page="sessions" onclick="showPage('sessions',this)">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
      <span>Sessions</span>
    </button>
    <button class="nav-item" data-page="budget" onclick="showPage('budget',this)">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>
      <span>Budget</span>
    </button>
    <button class="nav-item" data-page="config" onclick="showPage('config',this)">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>
      <span>Configuration</span>
    </button>
    <div style="padding:8px 14px 4px;font-size:10px;color:var(--bg3);text-transform:uppercase;letter-spacing:.08em;margin-top:8px">Channels</div>
    <button class="nav-item" data-page="line" onclick="showPage('line',this)">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"/></svg>
      <span>LINE</span>
    </button>
    <div style="padding:8px 14px 4px;font-size:10px;color:var(--bg3);text-transform:uppercase;letter-spacing:.08em;margin-top:8px">Content</div>
    <button class="nav-item" data-page="data" onclick="showPage('data',this)">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>
      <span>Data Files</span>
    </button>
    <button class="nav-item" data-page="logs" onclick="showPage('logs',this)">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="4 17 10 11 4 5"/><line x1="12" y1="19" x2="20" y2="19"/></svg>
      <span>Logs</span>
    </button>
  </div>
</nav>

<!-- Content -->
<div class="main" id="mainContent" style="display:none">

  <!-- Overview Page -->
  <div class="page active" id="page-overview">
    <div class="page-title">📊 Overview</div>
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

  <!-- Sessions Page -->
  <div class="page" id="page-sessions">
    <div class="page-title" style="justify-content:space-between">
      <span>💬 Sessions</span>
      <div><button class="btn btn-ghost btn-sm" onclick="loadSessions()">↻ Refresh</button> <button class="btn btn-danger btn-sm" onclick="clearAllSessions()">Clear All</button></div>
    </div>
    <div class="tbl-wrap"><table><thead><tr><th>Session ID</th><th>Messages</th><th>Last Activity</th><th>Actions</th></tr></thead><tbody id="sessionRows"></tbody></table></div>
  </div>

  <!-- Budget Page -->
  <div class="page" id="page-budget">
    <div class="page-title" style="justify-content:space-between">
      <span>💰 Budget</span>
      <button class="btn btn-danger btn-sm" onclick="resetBudget()">Reset Today</button>
    </div>
    <div class="cards" id="budgetCards"></div>
    <div id="budgetBars"></div>
  </div>

  <!-- Config Page -->
  <div class="page" id="page-config">
    <div class="page-title">⚙️ Configuration</div>

    <div style="display:flex;gap:12px;margin-bottom:20px">
      <button class="btn btn-ghost btn-sm config-tab active" data-tab="env" onclick="showConfigTab('env',this)">Environment</button>
      <button class="btn btn-ghost btn-sm config-tab" data-tab="client" onclick="showConfigTab('client',this)">Client YAML</button>
      <button class="btn btn-ghost btn-sm config-tab" data-tab="personality" onclick="showConfigTab('personality',this)">Personality YAML</button>
    </div>

    <!-- Env settings -->
    <div class="config-panel" id="cfg-env">
      <div id="envForm"></div>
      <button class="btn btn-primary" onclick="saveEnv()" style="margin-top:12px">Save Environment Settings</button>
      <span style="font-size:11px;color:var(--muted);margin-left:12px">Restart required for changes to take effect</span>
    </div>

    <!-- Client YAML -->
    <div class="config-panel" id="cfg-client" style="display:none">
      <div class="form-group">
        <label class="form-label">Client YAML (<span id="clientFile"></span>)</label>
        <textarea class="form-textarea" id="clientYaml" rows="20" style="min-height:300px"></textarea>
      </div>
      <button class="btn btn-primary" onclick="saveYaml('client')">Save Client Config</button>
    </div>

    <!-- Personality YAML -->
    <div class="config-panel" id="cfg-personality" style="display:none">
      <div class="form-group">
        <label class="form-label">Personality YAML (<span id="personalityFile"></span>)</label>
        <textarea class="form-textarea" id="personalityYaml" rows="20" style="min-height:300px"></textarea>
      </div>
      <button class="btn btn-primary" onclick="saveYaml('personality')">Save Personality Config</button>
    </div>
  </div>

  <!-- Logs Page -->
  <div class="page" id="page-logs">

  <!-- LINE Page -->
  <div class="page" id="page-line">
    <div class="page-title">💬 LINE Channel</div>

    <!-- Status -->
    <div class="cards" id="lineStatusCards"></div>

    <!-- Rich Menus -->
    <div style="display:flex;align-items:center;justify-content:space-between;margin:24px 0 12px">
      <h3 style="font-size:16px;font-weight:600">Rich Menus</h3>
      <div><button class="btn btn-ghost btn-sm" onclick="loadLineMenus()">↻ Refresh</button> <button class="btn btn-primary btn-sm" onclick="showRichMenuCreator()">+ Create Menu</button></div>
    </div>
    <div id="richMenuList"></div>

    <!-- Rich Menu Creator (hidden) -->
    <div id="richMenuCreator" style="display:none;margin-top:16px">
      <div class="card" style="padding:20px">
        <h4 style="margin-bottom:12px;font-size:14px">Create Rich Menu</h4>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
          <div class="form-group"><label class="form-label">Name</label><input class="form-input" id="rmName" value="Main Menu"></div>
          <div class="form-group"><label class="form-label">Chat Bar Text</label><input class="form-input" id="rmChatBar" value="Tap to open" maxlength="14"></div>
          <div class="form-group"><label class="form-label">Layout</label>
            <select class="form-input" id="rmLayout" onchange="updateRMFields()">
              <option value="2col">2 Columns</option><option value="3col">3 Columns</option><option value="2x3" selected>2x3 Grid (6 areas)</option>
            </select>
          </div>
        </div>
        <div id="rmAreasForm"></div>
        <div style="margin-top:12px;display:flex;gap:8px">
          <button class="btn btn-primary" onclick="createRichMenu()">Create on LINE</button>
          <button class="btn btn-ghost" onclick="document.getElementById('richMenuCreator').style.display='none'">Cancel</button>
        </div>
      </div>
    </div>

    <!-- Flex Message Builder -->
    <div style="display:flex;align-items:center;justify-content:space-between;margin:32px 0 12px">
      <h3 style="font-size:16px;font-weight:600">Flex Message Preview</h3>
    </div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px">
      <div>
        <div class="form-group"><label class="form-label">Type</label>
          <select class="form-input" id="flexType" onchange="updateFlexForm()">
            <option value="product">Product Card</option><option value="contact">Contact Card</option>
          </select>
        </div>
        <div id="flexForm"></div>
        <button class="btn btn-primary" onclick="previewFlex()" style="margin-top:8px">Generate Preview</button>
      </div>
      <div>
        <div class="form-label">JSON Preview</div>
        <pre class="log-viewer" id="flexPreview" style="min-height:200px;max-height:600px;font-size:11px">{}</pre>
      </div>
    </div>
  </div>

  <!-- Data Files Page -->
  <div class="page" id="page-data">
    <div class="page-title" style="justify-content:space-between">
      <span>📁 Data Files</span>
      <div>
        <button class="btn btn-ghost btn-sm" onclick="loadDataFiles()">↻ Refresh</button>
        <button class="btn btn-primary btn-sm" onclick="showNewFileForm()">+ New File</button>
      </div>
    </div>
    <p style="font-size:12px;color:var(--muted);margin-bottom:16px">These markdown files are the knowledge base that feeds the chatbot's RAG pipeline. Edit content here, then re-ingest.</p>

    <!-- New file form (hidden) -->
    <div id="newFileForm" style="display:none;margin-bottom:16px">
      <div class="card" style="padding:16px">
        <h4 style="margin-bottom:10px;font-size:14px">Create New Data File</h4>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px">
          <div class="form-group"><label class="form-label">Folder</label><input class="form-input" id="newFileFolder" placeholder="e.g. products"></div>
          <div class="form-group"><label class="form-label">Filename</label><input class="form-input" id="newFileName" placeholder="e.g. new_product.md"></div>
        </div>
        <div class="form-group"><label class="form-label">Content</label><textarea class="form-textarea" id="newFileContent" rows="6" placeholder="# Title\n\nContent here..."></textarea></div>
        <div style="display:flex;gap:8px"><button class="btn btn-primary btn-sm" onclick="createDataFile()">Create</button><button class="btn btn-ghost btn-sm" onclick="document.getElementById('newFileForm').style.display='none'">Cancel</button></div>
      </div>
    </div>

    <!-- File list -->
    <div class="tbl-wrap"><table><thead><tr><th>File</th><th>Folder</th><th>Size</th><th>Actions</th></tr></thead><tbody id="dataFileRows"></tbody></table></div>

    <!-- File editor (hidden) -->
    <div id="fileEditor" style="display:none">
      <div class="card" style="padding:20px">
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px">
          <h4 style="font-size:14px" id="editingFileName">Editing: ...</h4>
          <button class="btn btn-ghost btn-sm" onclick="closeEditor()">✕ Close</button>
        </div>
        <textarea class="form-textarea" id="fileContent" rows="20" style="min-height:400px;font-size:13px"></textarea>
        <div style="margin-top:12px;display:flex;gap:8px;align-items:center">
          <button class="btn btn-primary" onclick="saveDataFile()">Save</button>
          <span style="font-size:11px;color:var(--muted)">After saving, run <code style="background:var(--bg3);padding:2px 6px;border-radius:4px">run.bat ingest</code> to update the vector store</span>
        </div>
      </div>
    </div>
  </div>

  <!-- Logs Page (original) -->
  <div class="page" id="page-logs">
    <div class="page-title" style="justify-content:space-between">
      <span>📋 Logs</span>
      <div>
        <select class="form-input" id="logLines" style="width:auto;display:inline-block" onchange="loadLogs()">
          <option value="50">Last 50</option><option value="100" selected>Last 100</option><option value="200">Last 200</option><option value="500">Last 500</option>
        </select>
        <button class="btn btn-ghost btn-sm" onclick="loadLogs()">↻ Refresh</button>
      </div>
    </div>
    <div class="log-viewer" id="logViewer">No logs loaded</div>
  </div>

</div>

<div class="toast" id="toast"></div>

<script>
(function(){
"use strict";

var KEY = '';
var BASE = window.location.origin + '/admin/api';

// ── Auth ──────────────────────────────────────────────────────────────────
window.tryLogin = async function(){
  var k = document.getElementById('keyInput').value.trim();
  if(!k){document.getElementById('authErr').textContent='Key required';document.getElementById('authErr').style.display='block';return}
  KEY = k;
  try{
    var r = await api('/overview');
    document.getElementById('auth').style.display='none';
    document.getElementById('sidebar').style.display='flex';
    document.getElementById('mainContent').style.display='block';
    loadOverview(r);
  }catch(e){
    document.getElementById('authErr').textContent=e.message||'Authentication failed';
    document.getElementById('authErr').style.display='block';
    KEY='';
  }
};

// No auto-restore from storage — key stays in memory only for XSS safety
document.getElementById('keyInput').addEventListener('keydown',function(e){if(e.key==='Enter')tryLogin()});

// ── API helper ────────────────────────────────────────────────────────────
async function api(path, opts){
  opts = opts||{};
  var headers = {'X-Admin-Key':KEY};
  if(opts.body){headers['Content-Type']='application/json';}
  var r = await fetch(BASE+path,{method:opts.method||'GET',headers:headers,body:opts.body?JSON.stringify(opts.body):undefined});
  if(!r.ok){var e=await r.json().catch(function(){return{detail:'Request failed'}});throw new Error(e.detail||'Error '+r.status)}
  return r.json();
}

// ── Navigation ────────────────────────────────────────────────────────────
window.showPage = function(id, btn){
  document.querySelectorAll('.page').forEach(function(p){p.classList.remove('active')});
  document.querySelectorAll('.nav-item').forEach(function(n){n.classList.remove('active')});
  document.getElementById('page-'+id).classList.add('active');
  if(btn)btn.classList.add('active');
  if(id==='overview')loadOverviewData();
  if(id==='sessions')loadSessions();
  if(id==='budget')loadBudget();
  if(id==='config')loadConfig();
  if(id==='line')loadLine();
  if(id==='data')loadDataFiles();
  if(id==='logs')loadLogs();
};

// ── Overview ──────────────────────────────────────────────────────────────
async function loadOverviewData(){try{loadOverview(await api('/overview'))}catch(e){toast(e.message,'err')}}

function loadOverview(d){
  var html='';
  html+= card('Status', d.status==='running'?'🟢 Running':'🔴 Down', '');
  html+= card('Uptime', d.uptime, '');
  html+= card('Model', d.model, d.provider);
  html+= card('Active Sessions', d.sessions.active, d.sessions.backend+' backend');
  html+= card('Tokens Used', d.budget.tokens_used.toLocaleString(), 'of '+d.budget.daily_token_cap.toLocaleString()+' cap');
  html+= card('USD Spent', '$'+d.budget.usd_used.toFixed(4), 'of $'+d.budget.daily_usd_cap.toFixed(2)+' cap');
  html+= card('IP Buckets', d.rate_limiting.active_ip_buckets, d.rate_limiting.ip_per_minute+'/min');
  html+= card('Spam Trackers', d.spam_detection.active_trackers, d.spam_detection.max_strikes+' strikes');
  document.getElementById('overviewCards').innerHTML=html;

  // Channels
  var ch = d.channels;
  var cr='';
  ['web','whatsapp','telegram','line'].forEach(function(c){
    cr+='<tr><td style="text-transform:capitalize">'+c+'</td><td>'+(ch[c]?'<span class="tag tag-on">ON</span>':'<span class="tag tag-off">OFF</span>')+'</td></tr>';
  });
  document.getElementById('channelRows').innerHTML=cr;

  // Security
  var sec = d.security;
  var sr='';
  sr+='<tr><td>Rate Limiting</td><td>'+(d.rate_limiting.enabled?'<span class="tag tag-on">ON</span>':'<span class="tag tag-off">OFF</span>')+'</td></tr>';
  sr+='<tr><td>Spam Detection</td><td>'+(d.spam_detection.enabled?'<span class="tag tag-on">ON</span>':'<span class="tag tag-off">OFF</span>')+'</td></tr>';
  sr+='<tr><td>Budget Guard</td><td>'+(d.budget.enabled?'<span class="tag tag-on">ON</span>':'<span class="tag tag-off">OFF</span>')+'</td></tr>';
  sr+='<tr><td>HSTS</td><td>'+(sec.hsts_enabled?'<span class="tag tag-on">ON</span>':'<span class="tag tag-off">OFF</span>')+'</td></tr>';
  sr+='<tr><td>Strict CORS</td><td>'+(sec.strict_cors?'<span class="tag tag-on">ON</span>':'<span class="tag tag-off">OFF</span>')+'</td></tr>';
  sr+='<tr><td>API Key</td><td>'+(sec.api_key_set?'<span class="tag tag-on">SET</span>':'<span class="tag tag-off">NOT SET</span>')+'</td></tr>';
  document.getElementById('securityRows').innerHTML=sr;
}

function card(label,val,sub){
  return '<div class="card"><div class="card-label">'+label+'</div><div class="card-value">'+val+'</div>'+(sub?'<div class="card-sub">'+sub+'</div>':'')+'</div>';
}

// ── Sessions ──────────────────────────────────────────────────────────────
window.loadSessions = async function(){
  try{
    var d = await api('/sessions');
    var html='';
    if(!d.sessions.length){html='<tr><td colspan="4" style="text-align:center;color:var(--muted)">No sessions</td></tr>';}
    d.sessions.forEach(function(s){
      var ts = s.last_activity ? new Date(s.last_activity).toLocaleString() : '—';
      html+='<tr><td style="font-family:monospace;font-size:12px">'+esc(s.session_id)+'</td><td>'+s.message_count+'</td><td>'+ts+'</td><td><button class="btn btn-ghost btn-sm" onclick="viewSession(\''+esc(s.session_id)+'\')">View</button> <button class="btn btn-danger btn-sm" onclick="deleteSession(\''+esc(s.session_id)+'\')">Delete</button></td></tr>';
    });
    document.getElementById('sessionRows').innerHTML=html;
  }catch(e){toast(e.message,'err')}
};

window.viewSession = async function(id){
  try{
    var d = await api('/sessions/'+encodeURIComponent(id));
    var html='<div class="modal-bg" onclick="if(event.target===this)this.remove()"><div class="modal"><div class="modal-head"><h3>Session: '+esc(id.slice(0,20))+(id.length>20?'…':'')+'</h3><button class="btn btn-ghost btn-sm" onclick="this.closest(\'.modal-bg\').remove()">&times;</button></div><div class="modal-body">';
    if(!d.messages.length){html+='<p style="color:var(--muted)">No messages</p>';}
    d.messages.forEach(function(m){
      var role = m.role || m.type || 'unknown';
      var cls = role==='human'?'human':'ai';
      html+='<div class="msg-row '+cls+'"><div class="msg-role">'+role+'</div><div class="msg-text">'+esc(m.content||m.text||'')+'</div></div>';
    });
    html+='</div></div></div>';
    document.body.insertAdjacentHTML('beforeend',html);
  }catch(e){toast(e.message,'err')}
};

window.deleteSession = async function(id){
  if(!confirm('Delete session '+id+'?'))return;
  try{await api('/sessions/'+encodeURIComponent(id),{method:'DELETE'});toast('Session deleted','ok');loadSessions()}catch(e){toast(e.message,'err')}
};

window.clearAllSessions = async function(){
  if(!confirm('Clear ALL sessions? This cannot be undone.'))return;
  try{var d=await api('/sessions',{method:'DELETE'});toast('Cleared '+d.cleared+' sessions','ok');loadSessions()}catch(e){toast(e.message,'err')}
};

// ── Budget ────────────────────────────────────────────────────────────────
async function loadBudget(){
  try{
    var d = await api('/budget');
    var tc = d.daily_token_cap||1;var uc = d.daily_usd_cap||1;
    var tp = Math.min(100,Math.round(d.tokens_used/tc*100));
    var up = Math.min(100,Math.round(d.usd_used/uc*100));

    document.getElementById('budgetCards').innerHTML=
      card('Today','📅 '+d.day,'')+
      card('Model',d.model,'')+
      card('Tokens Used',d.tokens_used.toLocaleString(),'/ '+tc.toLocaleString())+
      card('USD Spent','$'+d.usd_used.toFixed(4),'/ $'+d.daily_usd_cap.toFixed(2))+
      card('Status',d.enabled?'🛡️ Enabled':'⚠️ Disabled','');

    var bars='';
    bars+='<div class="card" style="margin-bottom:16px"><div class="card-label">Token Usage ('+tp+'%)</div><div class="progress"><div class="progress-fill" style="width:'+tp+'%;background:'+(tp>80?'var(--danger)':tp>50?'var(--warn)':'var(--success)')+'"></div></div></div>';
    bars+='<div class="card"><div class="card-label">USD Usage ('+up+'%)</div><div class="progress"><div class="progress-fill" style="width:'+up+'%;background:'+(up>80?'var(--danger)':up>50?'var(--warn)':'var(--success)')+'"></div></div></div>';
    document.getElementById('budgetBars').innerHTML=bars;
  }catch(e){toast(e.message,'err')}
}

window.resetBudget = async function(){
  if(!confirm('Reset today\'s budget counters?'))return;
  try{await api('/budget/reset',{method:'POST'});toast('Budget reset','ok');loadBudget()}catch(e){toast(e.message,'err')}
};

// ── Config ────────────────────────────────────────────────────────────────
var configCache={};

async function loadConfig(){
  try{
    var d = await api('/config');
    configCache = d;
    buildEnvForm(d.env);
    document.getElementById('clientFile').textContent=d.client_file;
    document.getElementById('personalityFile').textContent=d.personality_file;
    document.getElementById('clientYaml').value = yamlStringify(d.client);
    document.getElementById('personalityYaml').value = yamlStringify(d.personality);
  }catch(e){toast(e.message,'err')}
}

// Editable env keys grouped
var ENV_GROUPS = [
  {label:'LLM', keys:['LLM_PROVIDER','LLM_MODEL','LLM_TEMPERATURE']},
  {label:'RAG', keys:['EMBEDDING_MODEL','CHUNK_SIZE','CHUNK_OVERLAP','RETRIEVAL_K']},
  {label:'Conversation', keys:['MAX_HISTORY_TURNS','MAX_MESSAGE_CHARS']},
  {label:'Rate Limiting', keys:['RATE_LIMIT_ENABLED','RATE_LIMIT_IP_PER_MINUTE','RATE_LIMIT_IP_BURST','RATE_LIMIT_SESSION_PER_MINUTE','RATE_LIMIT_SESSION_BURST']},
  {label:'Spam Detection', keys:['SPAM_DETECTION_ENABLED','SPAM_MAX_STRIKES','SPAM_COOLDOWN_SECONDS']},
  {label:'Budget', keys:['DAILY_TOKEN_CAP','DAILY_USD_CAP']},
  {label:'Security', keys:['API_CORS_ORIGINS','API_STRICT_CORS','API_HSTS_ENABLED']},
  {label:'General', keys:['ACTIVE_CLIENT','LOG_LEVEL','DEBUG']},
];

function buildEnvForm(env){
  var html='';
  ENV_GROUPS.forEach(function(g){
    html+='<h3 style="font-size:13px;color:var(--accent);margin:16px 0 8px;text-transform:uppercase;letter-spacing:.04em">'+g.label+'</h3>';
    html+='<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px">';
    g.keys.forEach(function(k){
      var v = env[k];
      if(v===undefined)return;
      var t = typeof v==='boolean'?'checkbox':'text';
      if(t==='checkbox'){
        html+='<div class="form-group"><label class="form-label">'+k+'</label><label style="display:flex;align-items:center;gap:8px;cursor:pointer"><input type="checkbox" data-env="'+k+'" '+(v?'checked':'')+' style="width:18px;height:18px;accent-color:var(--accent)"><span style="font-size:13px">'+(v?'Enabled':'Disabled')+'</span></label></div>';
      }else{
        html+='<div class="form-group"><label class="form-label">'+k+'</label><input class="form-input" data-env="'+k+'" value="'+esc(String(v))+'"></div>';
      }
    });
    html+='</div>';
  });

  // Secret indicators
  var secrets = Object.keys(env).filter(function(k){return k.startsWith('_')&&k.endsWith('_SET')});
  if(secrets.length){
    html+='<h3 style="font-size:13px;color:var(--accent);margin:16px 0 8px;text-transform:uppercase;letter-spacing:.04em">Secrets (read-only)</h3>';
    html+='<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px">';
    secrets.forEach(function(k){
      var label=k.replace(/^_/,'').replace(/_SET$/,'');
      html+='<div class="form-group"><label class="form-label">'+label+'</label>'+(env[k]?'<span class="tag tag-on">SET</span>':'<span class="tag tag-off">NOT SET</span>')+'</div>';
    });
    html+='</div>';
  }
  document.getElementById('envForm').innerHTML=html;
}

window.saveEnv = async function(){
  var body={};
  document.querySelectorAll('[data-env]').forEach(function(el){
    var k=el.dataset.env;
    if(el.type==='checkbox'){body[k]=el.checked}
    else{body[k]=el.value}
  });
  try{
    var r=await api('/config/env',{method:'PUT',body:body});
    var msg='Settings saved.';
    if(r.rejected&&Object.keys(r.rejected).length){msg+=' Rejected: '+Object.keys(r.rejected).join(', ')}
    toast(msg,'ok');
  }catch(e){toast(e.message,'err')}
};

window.showConfigTab = function(tab, btn){
  document.querySelectorAll('.config-panel').forEach(function(p){p.style.display='none'});
  document.querySelectorAll('.config-tab').forEach(function(b){b.classList.remove('active')});
  document.getElementById('cfg-'+tab).style.display='block';
  btn.classList.add('active');
};

window.saveYaml = async function(type){
  var text = document.getElementById(type==='client'?'clientYaml':'personalityYaml').value;
  var body;
  try{body=yamlParse(text)}catch(e){toast('Invalid YAML: '+e.message,'err');return}
  try{
    await api('/config/'+type,{method:'PUT',body:body});
    toast(type+' config saved','ok');
  }catch(e){toast(e.message,'err')}
};

// Simple YAML stringify (good enough for config display)
function yamlStringify(obj, indent){
  if(!obj)return '';
  indent=indent||0;
  var pad='  '.repeat(indent);
  var lines=[];
  Object.keys(obj).forEach(function(k){
    var v=obj[k];
    if(v&&typeof v==='object'&&!Array.isArray(v)){
      lines.push(pad+k+':');
      lines.push(yamlStringify(v,indent+1));
    }else if(Array.isArray(v)){
      lines.push(pad+k+':');
      v.forEach(function(item){
        if(typeof item==='object'){lines.push(pad+'  - '+JSON.stringify(item))}
        else{lines.push(pad+'  - '+item)}
      });
    }else{
      lines.push(pad+k+': '+JSON.stringify(v));
    }
  });
  return lines.join('\n');
}

// Simple YAML parse (sends as JSON anyway, so just parse the key: value lines)
function yamlParse(text){
  // Try JSON first (in case they pasted JSON)
  try{return JSON.parse(text)}catch(e){}
  // Basic YAML parse
  var result={};var stack=[{obj:result,indent:-1}];
  text.split('\n').forEach(function(line){
    var stripped=line.replace(/\s+$/,'');
    if(!stripped||stripped.match(/^\s*#/))return;
    var indent=line.match(/^(\s*)/)[1].length;
    var m=stripped.match(/^(\s*)([^:]+):\s*(.*)?$/);
    if(!m)return;
    var key=m[2].trim();var val=(m[3]||'').trim();
    while(stack.length>1&&stack[stack.length-1].indent>=indent)stack.pop();
    var parent=stack[stack.length-1].obj;
    if(!val){
      parent[key]={};
      stack.push({obj:parent[key],indent:indent});
    }else if(val.startsWith('[')){
      try{parent[key]=JSON.parse(val)}catch(e2){parent[key]=val}
    }else if(val==='true')parent[key]=true;
    else if(val==='false')parent[key]=false;
    else if(val==='null')parent[key]=null;
    else if(!isNaN(Number(val))&&val!=='')parent[key]=Number(val);
    else parent[key]=val.replace(/^["']|["']$/g,'');
  });
  return result;
}

// ── Logs ──────────────────────────────────────────────────────────────────
window.loadLogs = async function(){
  try{
    var n=document.getElementById('logLines').value;
    var d=await api('/logs?lines='+n);
    if(d.lines&&d.lines.length){
      document.getElementById('logViewer').textContent=d.lines.join('');
      document.getElementById('logViewer').scrollTop=999999;
    }else{
      document.getElementById('logViewer').textContent=d.note||d.error||'No logs';
    }
  }catch(e){toast(e.message,'err')}
};

// ── Toast ─────────────────────────────────────────────────────────────────
function toast(msg, type){
  var t=document.getElementById('toast');
  t.textContent=msg;
  t.className='toast toast-'+(type||'ok')+' show';
  clearTimeout(t._tid);
  t._tid=setTimeout(function(){t.classList.remove('show')},3500);
}

function esc(s){
  var d=document.createElement('div');d.textContent=s;return d.innerHTML;
}

// ── LINE ──────────────────────────────────────────────────────────────────
async function loadLine(){
  try{
    var s=await api('/line/status');
    var html='';
    html+=card('LINE Status',s.configured?'🟢 Configured':'🔴 Not configured','');
    html+=card('Channel Secret',s.channel_secret_set?'✅ Set':'❌ Missing','');
    html+=card('Access Token',s.access_token_set?'✅ Set':'❌ Missing','');
    html+=card('Webhook URL',esc(s.webhook_url),'');
    document.getElementById('lineStatusCards').innerHTML=html;
    if(s.configured)loadLineMenus();
    else document.getElementById('richMenuList').innerHTML='<p style="color:var(--muted);font-size:13px">Configure LINE_CHANNEL_ACCESS_TOKEN in .env to enable</p>';
  }catch(e){toast(e.message,'err')}
  updateFlexForm();
}

window.loadLineMenus=async function(){
  try{
    var d=await api('/line/rich-menus');
    if(!d.menus||!d.menus.length){
      document.getElementById('richMenuList').innerHTML='<div class="card" style="padding:16px;text-align:center;color:var(--muted)">No rich menus created yet</div>';
      return;
    }
    var html='<div class="tbl-wrap"><table><thead><tr><th>Name</th><th>Chat Bar</th><th>Areas</th><th>Default</th><th>Actions</th></tr></thead><tbody>';
    d.menus.forEach(function(m){
      var isDefault=m.richMenuId===d.default_id;
      html+='<tr><td>'+esc(m.name)+'</td><td>'+esc(m.chatBarText||'')+'</td><td>'+((m.areas||[]).length)+'</td>';
      html+='<td>'+(isDefault?'<span class="tag tag-on">DEFAULT</span>':'<button class="btn btn-ghost btn-sm" onclick="setDefaultMenu(\''+m.richMenuId+'\')">Set Default</button>')+'</td>';
      html+='<td><button class="btn btn-danger btn-sm" onclick="deleteRichMenu(\''+m.richMenuId+'\')">Delete</button></td></tr>';
    });
    html+='</tbody></table></div>';
    document.getElementById('richMenuList').innerHTML=html;
  }catch(e){
    document.getElementById('richMenuList').innerHTML='<div class="card" style="padding:16px;color:var(--danger)">'+esc(e.message)+'</div>';
  }
};

window.showRichMenuCreator=function(){
  document.getElementById('richMenuCreator').style.display='block';
  updateRMFields();
};

window.updateRMFields=function(){
  var layout=document.getElementById('rmLayout').value;
  var count=layout==='2col'?2:layout==='3col'?3:6;
  var defaults2=['Products','Contact Us'];var dt2=['Show products','Contact details'];
  var defaults3=['Products','Hours','Contact'];var dt3=['Show products','Opening hours','Contact details'];
  var defaults6=['Curtains','Sofas','Wallpapers','Poufs','Hours','Contact'];
  var dt6=['Tell me about curtains','Tell me about sofas','Tell me about wallpapers','Tell me about poufs','Opening hours','Contact details'];
  var labels=count===2?defaults2:count===3?defaults3:defaults6;
  var texts=count===2?dt2:count===3?dt3:dt6;
  var html='<div style="margin-top:12px"><div class="form-label">Areas ('+count+')</div>';
  html+='<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px">';
  for(var i=0;i<count;i++){
    html+='<div class="card" style="padding:10px"><div class="form-group" style="margin-bottom:6px"><label class="form-label">Label '+(i+1)+'</label><input class="form-input rm-label" value="'+esc(labels[i])+'"></div>';
    html+='<div class="form-group" style="margin-bottom:0"><label class="form-label">Message Text</label><input class="form-input rm-text" value="'+esc(texts[i])+'"></div></div>';
  }
  html+='</div></div>';
  document.getElementById('rmAreasForm').innerHTML=html;
};

window.createRichMenu=async function(){
  var labels=[];var texts=[];
  document.querySelectorAll('.rm-label').forEach(function(el){labels.push(el.value)});
  document.querySelectorAll('.rm-text').forEach(function(el){texts.push(el.value)});
  try{
    var r=await api('/line/rich-menus',{method:'POST',body:{
      layout:document.getElementById('rmLayout').value,
      name:document.getElementById('rmName').value,
      chat_bar_text:document.getElementById('rmChatBar').value,
      labels:labels,texts:texts
    }});
    toast('Rich Menu created: '+r.menu_id,'ok');
    document.getElementById('richMenuCreator').style.display='none';
    loadLineMenus();
  }catch(e){toast(e.message,'err')}
};

window.setDefaultMenu=async function(id){
  try{await api('/line/rich-menus/'+id+'/default',{method:'POST'});toast('Set as default','ok');loadLineMenus()}catch(e){toast(e.message,'err')}
};

window.deleteRichMenu=async function(id){
  if(!confirm('Delete this rich menu?'))return;
  try{await api('/line/rich-menus/'+id,{method:'DELETE'});toast('Deleted','ok');loadLineMenus()}catch(e){toast(e.message,'err')}
};

// Flex Message builder
window.updateFlexForm=function(){
  var type=document.getElementById('flexType').value;
  var html='';
  if(type==='product'){
    html+='<div class="form-group"><label class="form-label">Title</label><input class="form-input" id="fxTitle" value="Roman Curtain"></div>';
    html+='<div class="form-group"><label class="form-label">Description</label><input class="form-input" id="fxDesc" value="Custom made, premium fabric"></div>';
    html+='<div class="form-group"><label class="form-label">Price</label><input class="form-input" id="fxPrice" value="₪440 – ₪550"></div>';
    html+='<div class="form-group"><label class="form-label">Image URL (https)</label><input class="form-input" id="fxImage" placeholder="https://..."></div>';
    html+='<div class="form-group"><label class="form-label">Button Label</label><input class="form-input" id="fxBtnLabel" value="Learn more"></div>';
    html+='<div class="form-group"><label class="form-label">Button URL (optional)</label><input class="form-input" id="fxBtnUri" placeholder="https://..."></div>';
  }else{
    html+='<div class="form-group"><label class="form-label">Business Name</label><input class="form-input" id="fxBizName" value="Limmes Studio"></div>';
    html+='<div class="form-group"><label class="form-label">Phone</label><input class="form-input" id="fxPhone" value="+972-54-123-4567"></div>';
    html+='<div class="form-group"><label class="form-label">WhatsApp</label><input class="form-input" id="fxWhatsApp" value="+972-54-123-4567"></div>';
    html+='<div class="form-group"><label class="form-label">Email</label><input class="form-input" id="fxEmail" value="info@limmes.co.il"></div>';
    html+='<div class="form-group"><label class="form-label">Address</label><input class="form-input" id="fxAddress" value="Nes Ziona, Israel"></div>';
  }
  document.getElementById('flexForm').innerHTML=html;
};

window.previewFlex=async function(){
  var type=document.getElementById('flexType').value;
  var body={type:type};
  if(type==='product'){
    body.title=document.getElementById('fxTitle').value;
    body.description=document.getElementById('fxDesc').value;
    body.price=document.getElementById('fxPrice').value;
    body.image_url=document.getElementById('fxImage').value||undefined;
    body.action_label=document.getElementById('fxBtnLabel').value;
    body.action_uri=document.getElementById('fxBtnUri').value||undefined;
  }else{
    body.business_name=document.getElementById('fxBizName').value;
    body.phone=document.getElementById('fxPhone').value;
    body.whatsapp=document.getElementById('fxWhatsApp').value;
    body.email=document.getElementById('fxEmail').value;
    body.address=document.getElementById('fxAddress').value;
  }
  try{
    var r=await api('/line/flex-preview',{method:'POST',body:body});
    document.getElementById('flexPreview').textContent=JSON.stringify(r.flex,null,2);
  }catch(e){toast(e.message,'err')}
};

// ── Data Files ────────────────────────────────────────────────────────────
var _editingFile='';

window.loadDataFiles=async function(){
  try{
    var d=await api('/data');
    var html='';
    if(!d.files.length){html='<tr><td colspan="4" style="text-align:center;color:var(--muted)">No data files. Create one or add markdown files under data/</td></tr>';}
    d.files.forEach(function(f){
      html+='<tr><td style="font-family:monospace;font-size:12px">'+esc(f.name)+'</td>';
      html+='<td>'+esc(f.folder||'—')+'</td>';
      html+='<td>'+(f.size>1024?(f.size/1024).toFixed(1)+' KB':f.size+' B')+'</td>';
      html+='<td><button class="btn btn-ghost btn-sm" onclick="editDataFile(\''+esc(f.path)+'\')">Edit</button> <button class="btn btn-danger btn-sm" onclick="removeDataFile(\''+esc(f.path)+'\')">Delete</button></td></tr>';
    });
    document.getElementById('dataFileRows').innerHTML=html;
  }catch(e){toast(e.message,'err')}
};

window.editDataFile=async function(path){
  try{
    var d=await api('/data/'+encodeURIComponent(path));
    _editingFile=path;
    document.getElementById('editingFileName').textContent='Editing: '+path;
    document.getElementById('fileContent').value=d.content;
    document.getElementById('fileEditor').style.display='block';
    document.getElementById('fileEditor').scrollIntoView({behavior:'smooth'});
  }catch(e){toast(e.message,'err')}
};

window.closeEditor=function(){
  document.getElementById('fileEditor').style.display='none';
  _editingFile='';
};

window.saveDataFile=async function(){
  if(!_editingFile)return;
  try{
    var r=await api('/data/'+encodeURIComponent(_editingFile),{method:'PUT',body:{content:document.getElementById('fileContent').value}});
    toast('Saved! '+r.note,'ok');
    loadDataFiles();
  }catch(e){toast(e.message,'err')}
};

window.showNewFileForm=function(){
  document.getElementById('newFileForm').style.display='block';
};

window.createDataFile=async function(){
  var folder=document.getElementById('newFileFolder').value.trim();
  var name=document.getElementById('newFileName').value.trim();
  if(!name){toast('Filename required','err');return}
  var path=folder?(folder+'/'+name):name;
  var content=document.getElementById('newFileContent').value;
  try{
    await api('/data',{method:'POST',body:{path:path,content:content}});
    toast('File created: '+path,'ok');
    document.getElementById('newFileForm').style.display='none';
    document.getElementById('newFileFolder').value='';
    document.getElementById('newFileName').value='';
    document.getElementById('newFileContent').value='';
    loadDataFiles();
  }catch(e){toast(e.message,'err')}
};

window.removeDataFile=async function(path){
  if(!confirm('Delete data file: '+path+'?'))return;
  try{await api('/data/'+encodeURIComponent(path),{method:'DELETE'});toast('Deleted','ok');closeEditor();loadDataFiles()}catch(e){toast(e.message,'err')}
};

})();
</script>
</body>
</html>"""
