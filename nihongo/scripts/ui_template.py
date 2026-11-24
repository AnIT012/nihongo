"""nihongo 全AI共通ルール管理 UI テンプレート（3色・4場面カード・最小情報設計・外部通信ゼロ）。"""
from __future__ import annotations

import json


def render_ui_html(csrf_token: str) -> str:
    """127.0.0.1 専用ローカル管理画面の単一 HTML を返す（外部リソース・外部通信ゼロ）。"""
    token_json = json.dumps(csrf_token)
    return f"""<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Ccircle cx='16' cy='16' r='12' fill='%23D7261E'/%3E%3C/svg%3E">
<title>nihongo — ルール管理</title>
<style>
:root {{
  --bg: #F7F7F8;
  --surface: #FFFFFF;
  --ink: #111113;
  --body: #2C2C30;
  --muted: #6E6E77;
  --line: #E6E6EA;
  --line-strong: #D0D0D7;
  --red: #D7261E;
  --red-hover: #B61E17;
  --red-soft: #FEF2F2;
  --ok: #15803D;
  --ok-soft: #ECFDF3;
  --shadow-sm: 0 1px 2px rgba(17, 17, 19, 0.04);
  --radius: 10px;
}}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
html, body {{ height: 100%; }}
body {{
  background: var(--bg);
  color: var(--ink);
  font-family: -apple-system, BlinkMacSystemFont, "Hiragino Sans", "Hiragino Kaku Gothic ProN", "Yu Gothic UI", "Meiryo", sans-serif;
  font-size: 14px;
  line-height: 1.6;
  -webkit-font-smoothing: antialiased;
}}

.app {{
  display: grid;
  grid-template-columns: 224px 1fr;
  min-height: 100vh;
}}

/* Sidebar */
.sidebar {{
  background: var(--surface);
  border-right: 1px solid var(--line);
  padding: 20px 12px 16px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  position: sticky;
  top: 0;
  height: 100vh;
}}
.brand-block {{
  padding: 2px 10px 16px;
  margin-bottom: 10px;
  border-bottom: 1px solid var(--line);
}}
.logo {{
  font-family: ui-sans-serif, system-ui, sans-serif;
  font-weight: 800;
  font-size: 22px;
  letter-spacing: -0.03em;
  line-height: 1;
}}
.logo i {{
  display: inline-block;
  width: 0.44em;
  height: 0.44em;
  border-radius: 50%;
  background: var(--red);
  margin: 0 0.04em;
}}

.nav-list {{
  display: flex;
  flex-direction: column;
  gap: 2px;
}}
.nav-sep {{
  height: 1px;
  background: var(--line);
  margin: 10px 8px;
}}
.tab-btn {{
  appearance: none;
  border: 0;
  background: transparent;
  color: var(--body);
  font: inherit;
  font-size: 13.5px;
  font-weight: 600;
  padding: 9px 10px;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: space-between;
  text-align: left;
  transition: background 0.12s ease, color 0.12s ease;
}}
.tab-btn:hover {{ background: var(--bg); color: var(--ink); }}
.tab-btn.active {{
  background: #EFEFF3;
  color: var(--ink);
  font-weight: 700;
}}
.tab-btn.muted-nav {{
  color: var(--muted);
  font-weight: 500;
  font-size: 13px;
}}
.tab-btn.muted-nav.active {{ color: var(--ink); font-weight: 600; }}
.tab-left {{
  display: inline-flex;
  align-items: center;
  gap: 9px;
}}
.tab-ico {{
  width: 16px;
  height: 16px;
  flex-shrink: 0;
  color: var(--muted);
}}
.tab-btn.active .tab-ico {{ color: var(--ink); }}

.count-dot {{
  background: var(--red);
  color: #FFFFFF;
  font-size: 11px;
  font-weight: 700;
  padding: 1px 7px;
  border-radius: 999px;
  min-width: 20px;
  text-align: center;
}}
.count-dot.zero {{
  background: var(--line);
  color: var(--muted);
}}

.side-foot {{
  border-top: 1px solid var(--line);
  padding: 12px 10px 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}}
.local-status {{
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--muted);
  font-weight: 500;
}}
.local-status::before {{
  content: "";
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #16A34A;
}}
.layer-badge {{
  display: inline-flex;
  align-items: center;
  padding: 1px 6px;
  border-radius: 4px;
  font-size: 10.5px;
  font-weight: 700;
  background: var(--bg);
  border: 1px solid var(--line-strong);
  color: var(--ink);
}}
.btn-reload-mini {{
  appearance: none;
  border: 0;
  background: transparent;
  color: var(--muted);
  font: inherit;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  padding: 3px 6px;
  border-radius: 6px;
}}
.btn-reload-mini:hover {{ background: var(--bg); color: var(--ink); }}

/* Main Workspace */
.main {{
  padding: 30px 36px 72px;
  max-width: 1020px;
  width: 100%;
}}
.panel {{ display: none; }}
.panel.active {{ display: block; }}

.toast {{
  display: none;
  margin-bottom: 16px;
  padding: 10px 14px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  border: 1px solid var(--line-strong);
  background: var(--surface);
  box-shadow: var(--shadow-sm);
}}
.toast.show {{ display: block; }}
.toast.error {{
  border-color: #FECACA;
  background: var(--red-soft);
  color: var(--red-hover);
}}
.toast.ok {{
  border-color: #BBF7D0;
  background: var(--ok-soft);
  color: var(--ok);
}}

.page-head {{
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 18px;
}}
.page-head h1 {{
  font-size: 20px;
  font-weight: 800;
  letter-spacing: -0.015em;
  line-height: 1.3;
}}
.head-actions {{
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}}

/* Segmented Mode Switch */
.seg {{
  display: inline-flex;
  background: #ECECF0;
  padding: 3px;
  border-radius: 8px;
  gap: 2px;
}}
.seg-btn {{
  appearance: none;
  border: 0;
  background: transparent;
  color: var(--muted);
  font: inherit;
  font-size: 12.5px;
  font-weight: 700;
  padding: 5px 12px;
  border-radius: 6px;
  cursor: pointer;
}}
.seg-btn.active {{
  background: var(--surface);
  color: var(--ink);
  box-shadow: var(--shadow-sm);
}}

/* Buttons */
.btn {{
  appearance: none;
  border: 1px solid var(--line-strong);
  background: var(--surface);
  color: var(--ink);
  font: inherit;
  font-size: 13px;
  font-weight: 600;
  padding: 7px 13px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.12s ease, border-color 0.12s ease;
}}
.btn:hover {{ background: var(--bg); border-color: #B4B4BE; }}
.btn.primary {{
  background: var(--red);
  border-color: var(--red);
  color: #FFFFFF;
}}
.btn.primary:hover {{ background: var(--red-hover); border-color: var(--red-hover); }}
.btn.dark {{
  background: var(--ink);
  border-color: var(--ink);
  color: #FFFFFF;
}}
.btn.dark:hover {{ background: #2A2A2E; }}
.btn.subtle {{
  border-color: transparent;
  background: transparent;
  color: var(--muted);
}}
.btn.subtle:hover {{ color: var(--ink); background: #ECECF0; }}
.btn.sm {{ padding: 5px 10px; font-size: 12px; }}
.btn:disabled {{ opacity: 0.4; cursor: not-allowed; }}

/* Quick Add Strip */
.quick-add {{
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  padding: 10px 12px;
  margin-bottom: 16px;
  box-shadow: var(--shadow-sm);
  display: grid;
  grid-template-columns: 126px 146px 1fr auto;
  gap: 8px;
  align-items: center;
}}

/* 4-Scene Personal Grid */
.scene-grid {{
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
}}
.scene-card {{
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  padding: 18px 20px;
  box-shadow: var(--shadow-sm);
  display: flex;
  flex-direction: column;
  gap: 12px;
}}
.scene-card.common-card {{
  grid-column: 1 / -1;
}}
.sc-head {{
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
  padding-bottom: 10px;
  border-bottom: 1px solid var(--line);
}}
.sc-title-wrap {{
  display: flex;
  align-items: baseline;
  gap: 8px;
  flex-wrap: wrap;
}}
.sc-head h2 {{
  font-size: 15px;
  font-weight: 800;
}}
.sc-hint {{
  font-size: 12px;
  color: var(--muted);
}}
.sc-lbl {{
  font-size: 11.5px;
  font-weight: 700;
  color: var(--muted);
  margin-bottom: 6px;
}}

.chip-wrap {{
  display: flex;
  flex-wrap: wrap;
  gap: 7px;
}}
.ng-chip {{
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: 999px;
  background: var(--red-soft);
  border: 1px solid #FECACA;
  color: var(--red-hover);
  font-size: 13px;
  font-weight: 700;
}}
.ng-chip.project-chip {{
  background: #F4F4F6;
  border-color: var(--line-strong);
  color: var(--ink);
}}
.chip-x {{
  appearance: none;
  border: 0;
  background: transparent;
  color: var(--red-hover);
  font-size: 14px;
  line-height: 1;
  cursor: pointer;
  padding: 0 2px;
  border-radius: 4px;
}}
.chip-x:hover {{ background: rgba(215, 38, 30, 0.14); }}
.mini-tag {{
  font-size: 10.5px;
  font-weight: 700;
  padding: 1px 6px;
  border-radius: 4px;
  background: #ECECF0;
  color: var(--body);
}}

.rule-list {{
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 6px;
}}
.rule-list li {{
  font-size: 13.5px;
  color: var(--body);
  padding: 7px 11px;
  background: var(--bg);
  border-radius: 7px;
  display: flex;
  align-items: baseline;
  gap: 7px;
}}
.muted-empty {{
  font-size: 12.5px;
  color: var(--muted);
}}

/* Surface Card */
.surface-card {{
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  box-shadow: var(--shadow-sm);
  overflow: hidden;
}}
.editor-bar {{
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 16px;
  border-bottom: 1px solid var(--line);
  background: #FAFAFB;
  font-size: 12px;
  color: var(--muted);
  gap: 10px;
  flex-wrap: wrap;
}}

/* Inbox Cards */
.card-list {{
  display: flex;
  flex-direction: column;
  gap: 10px;
}}
.item-card {{
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  padding: 15px 18px;
  box-shadow: var(--shadow-sm);
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
}}
.item-card.warn {{
  border-color: #FECACA;
  border-left: 4px solid var(--red);
  background: #FFFBFB;
}}
.item-main {{ flex: 1; min-width: 0; }}
.item-meta {{
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
  margin-bottom: 6px;
  font-size: 12px;
  color: var(--muted);
}}
.pill {{
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  border-radius: 6px;
  font-size: 11.5px;
  font-weight: 600;
  background: var(--bg);
  color: var(--body);
  border: 1px solid var(--line);
}}
.pill.ok {{ background: var(--ok-soft); color: var(--ok); border-color: #BBF7D0; }}
.pill.rej {{ background: var(--bg); color: var(--muted); border-color: var(--line); }}
.item-val {{
  font-size: 15px;
  font-weight: 700;
  color: var(--ink);
  word-break: break-word;
}}
.item-note {{ font-size: 13px; color: var(--muted); margin-top: 3px; }}
.diff-line {{
  display: inline-block;
  margin-top: 6px;
  font-size: 12.5px;
  color: var(--body);
  background: var(--bg);
  border: 1px solid var(--line);
  border-radius: 6px;
  padding: 4px 9px;
}}
.warn-msg {{ margin-top: 8px; font-size: 12.5px; font-weight: 600; color: var(--red-hover); }}
.item-side {{ display: flex; flex-shrink: 0; gap: 6px; align-items: center; }}
.force-check {{
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 600;
  color: var(--red-hover);
  margin-top: 8px;
}}

.empty-box {{
  background: var(--surface);
  border: 1px dashed var(--line-strong);
  border-radius: var(--radius);
  padding: 32px 24px;
  text-align: center;
  color: var(--muted);
  font-size: 13.5px;
}}

/* Collapsible Form */
.form-box {{
  display: none;
  margin-bottom: 14px;
  background: var(--surface);
  border: 1px solid var(--line-strong);
  border-radius: var(--radius);
  padding: 16px 18px;
}}
.form-box.open {{ display: block; }}

/* Apps & Sync */
.block-title {{
  font-size: 13.5px;
  font-weight: 800;
  margin: 22px 0 8px;
  color: var(--ink);
}}
.block-title:first-of-type {{ margin-top: 0; }}
.app-row {{
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-top: 1px solid var(--line);
  flex-wrap: wrap;
}}
.app-row:first-child {{ border-top: 0; }}
.app-name {{ font-weight: 700; font-size: 14px; }}
.app-right {{ display: flex; align-items: center; gap: 8px; }}

.export-row {{
  display: grid;
  grid-template-columns: 1fr 1fr auto;
  gap: 10px;
  align-items: end;
}}

.grid-2 {{
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-bottom: 12px;
}}
label.fld {{
  display: block;
  font-size: 12px;
  font-weight: 600;
  color: var(--muted);
  margin-bottom: 5px;
}}
input[type="text"], select, textarea {{
  width: 100%;
  font: inherit;
  font-size: 13.5px;
  padding: 8px 11px;
  border: 1px solid var(--line-strong);
  border-radius: 8px;
  background: var(--surface);
  color: var(--ink);
}}
input[type="text"]:focus, select:focus, textarea:focus {{
  outline: none;
  border-color: var(--ink);
}}
textarea.mono {{
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 13px;
  line-height: 1.65;
  min-height: 300px;
  border: 0;
  border-radius: 0;
  padding: 16px 18px;
  resize: vertical;
}}

.findings-box {{
  margin-top: 14px;
  border: 1px solid var(--line-strong);
  border-radius: var(--radius);
  padding: 15px 18px;
  background: var(--surface);
}}
.findings-box.has-issue {{
  border-color: #FECACA;
  border-left: 4px solid var(--red);
  background: #FFFBFB;
}}
.findings-box ul {{ margin-top: 8px; padding-left: 20px; }}
.findings-box li {{ margin: 4px 0; font-size: 13.5px; }}

details.skill-box {{
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  padding: 11px 16px;
  margin-top: 8px;
}}
details.skill-box summary {{
  cursor: pointer;
  font-weight: 700;
  font-size: 13px;
}}
pre.skill-pre {{
  margin-top: 10px;
  padding: 12px 14px;
  background: var(--bg);
  border-radius: 8px;
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 12px;
  line-height: 1.65;
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 260px;
  overflow-y: auto;
}}

.history-head {{
  font-size: 12.5px;
  font-weight: 700;
  color: var(--muted);
  margin: 22px 0 10px;
}}

@media (max-width: 980px) {{
  .scene-grid {{ grid-template-columns: 1fr; }}
  .export-row {{ grid-template-columns: 1fr; }}
}}
@media (max-width: 820px) {{
  .app {{ grid-template-columns: 1fr; }}
  .sidebar {{
    position: static;
    height: auto;
    border-right: 0;
    border-bottom: 1px solid var(--line);
    padding: 14px 16px;
  }}
  .brand-block {{ padding: 0 0 10px; margin-bottom: 10px; }}
  .nav-list {{ flex-direction: row; flex-wrap: wrap; gap: 4px; }}
  .nav-sep {{ display: none; }}
  .tab-btn {{ padding: 7px 10px; font-size: 12.5px; }}
  .side-foot {{ margin-top: 10px; padding: 10px 0 0; }}
  .main {{ padding: 20px 16px 56px; }}
  .quick-add, .grid-2 {{ grid-template-columns: 1fr; }}
  .item-card {{ flex-direction: column; gap: 12px; }}
}}
</style>
</head>
<body>
<div class="app">
  <aside class="sidebar">
    <div>
      <div class="brand-block">
        <div class="logo">nih<i></i>ngo</div>
      </div>
      <nav class="nav-list" aria-label="メニュー">
        <button class="tab-btn active" data-tab="profile" type="button">
          <span class="tab-left"><svg class="tab-ico" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><line x1="2.5" y1="4" x2="13.5" y2="4"/><circle cx="6" cy="4" r="1.4" fill="currentColor"/><line x1="2.5" y1="8" x2="13.5" y2="8"/><circle cx="10.5" cy="8" r="1.4" fill="currentColor"/><line x1="2.5" y1="12" x2="13.5" y2="12"/><circle cx="5.5" cy="12" r="1.4" fill="currentColor"/></svg>自分のルール</span>
        </button>
        <button class="tab-btn" data-tab="inbox" type="button">
          <span class="tab-left"><svg class="tab-ico" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M2.5 9.5V12.5A1 1 0 0 0 3.5 13.5H12.5A1 1 0 0 0 13.5 12.5V9.5"/><path d="M2.5 9.5L4.3 3.5H11.7L13.5 9.5H10.3L9.3 11H6.7L5.7 9.5H2.5Z"/></svg>承認待ち</span>
          <span class="count-dot zero" id="pending-count">0</span>
        </button>
        <button class="tab-btn" data-tab="connect" type="button">
          <span class="tab-left"><svg class="tab-ico" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6.5 9.5L9.5 6.5"/><path d="M9 11L7.3 12.7A2.6 2.6 0 1 1 3.6 9L5.3 7.3"/><path d="M7 5L8.7 3.3A2.6 2.6 0 1 1 12.4 7L10.7 8.7"/></svg>AI接続・同期</span>
        </button>
        <div class="nav-sep"></div>
        <button class="tab-btn muted-nav" data-tab="check" type="button">
          <span class="tab-left"><svg class="tab-ico" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M8 2L13 4V7.8C13 10.9 10.9 13.1 8 14C5.1 13.1 3 10.9 3 7.8V4L8 2Z"/><path d="M5.8 8.2L7.3 9.7L10.4 6.6"/></svg>動作テスト</span>
        </button>
      </nav>
    </div>

    <div class="side-foot">
      <div style="display:flex;align-items:center;gap:6px;" id="meta-bar">
        <span class="local-status">ローカル</span>
      </div>
      <button class="btn-reload-mini" id="btn-reload" type="button">更新</button>
    </div>
  </aside>

  <main class="main">
    <div class="toast" id="toast" role="status" aria-live="polite"></div>

    <!-- 1. Personal Rules Panel -->
    <section class="panel active" id="panel-profile">
      <div class="page-head">
        <h1>自分のルール</h1>
        <div class="head-actions">
          <div class="seg" role="tablist" aria-label="表示切替">
            <button class="seg-btn active" id="mode-cards" type="button">カード</button>
            <button class="seg-btn" id="mode-raw" type="button">Markdown</button>
          </div>
        </div>
      </div>

      <div id="view-cards">
        <div class="quick-add">
          <select id="qa-scene" aria-label="場面">
            <option value="common">共通</option>
            <option value="work">社内・同僚</option>
            <option value="formal">社外・目上</option>
            <option value="casual">普段・雑談</option>
          </select>
          <select id="qa-kind" aria-label="種類">
            <option value="forbidden">避ける表現</option>
            <option value="rule">書く時の考え方</option>
            <option value="tone">口調・記号</option>
            <option value="first_person">一人称</option>
          </select>
          <input type="text" id="qa-value" placeholder="追加する表現やルールを入力">
          <button class="btn dark" id="btn-qa-add" type="button">追加</button>
        </div>

        <div class="scene-grid" id="scene-grid"></div>
      </div>

      <div id="view-raw" style="display:none;">
        <div class="surface-card">
          <div class="editor-bar">
            <span id="editor-path">profile.md</span>
            <button class="btn primary sm" id="btn-save-profile" type="button">保存</button>
          </div>
          <textarea class="mono" id="profile-editor" spellcheck="false"></textarea>
        </div>
        <div class="surface-card" id="project-raw-card" style="display:none;margin-top:14px;">
          <div class="editor-bar">
            <span id="project-raw-path">案件別（.nihongo/profile.md）</span>
            <span>読み取り専用</span>
          </div>
          <textarea class="mono" id="project-raw-editor" readonly style="min-height:130px;background:#FAFAFB;"></textarea>
        </div>
      </div>
    </section>

    <!-- 2. Pending Inbox Panel -->
    <section class="panel" id="panel-inbox">
      <div class="page-head">
        <h1>承認待ち</h1>
        <div class="head-actions">
          <button class="btn" id="btn-toggle-add" type="button">＋ 追加</button>
          <button class="btn primary" id="btn-approve-all" type="button">一括承認</button>
          <button class="btn subtle" id="btn-toggle-history" type="button">履歴</button>
        </div>
      </div>

      <div class="form-box" id="add-form-box">
        <div class="grid-2">
          <div>
            <label class="fld" for="prop-scene">場面</label>
            <select id="prop-scene">
              <option value="common">共通</option>
              <option value="work">社内・同僚</option>
              <option value="formal">社外・目上</option>
              <option value="casual">普段・雑談</option>
            </select>
          </div>
          <div>
            <label class="fld" for="prop-kind">種類</label>
            <select id="prop-kind">
              <option value="forbidden">避ける表現</option>
              <option value="rule">書く時の考え方</option>
              <option value="tone">口調・記号</option>
              <option value="first_person">一人称</option>
            </select>
          </div>
        </div>
        <div class="grid-2">
          <div>
            <label class="fld" for="prop-value">内容</label>
            <input type="text" id="prop-value" placeholder="例：いただけますと幸いです">
          </div>
          <div>
            <label class="fld" for="prop-reason">理由（任意）</label>
            <input type="text" id="prop-reason" placeholder="例：結びが硬すぎるため">
          </div>
        </div>
        <div style="display:flex;gap:8px;">
          <button class="btn dark sm" id="btn-propose" type="button">追加</button>
          <button class="btn subtle sm" id="btn-cancel-add" type="button">閉じる</button>
        </div>
      </div>

      <div class="card-list" id="inbox-list"></div>

      <div id="history-wrap" style="display:none;">
        <div class="history-head">処理済みの履歴</div>
        <div class="card-list" id="history-list"></div>
      </div>
    </section>

    <!-- 3. Connect & Sync Panel -->
    <section class="panel" id="panel-connect">
      <div class="page-head">
        <h1>AI接続・同期</h1>
      </div>

      <div class="block-title">AIアプリ（MCP）</div>
      <div class="surface-card" id="mcp-list"></div>

      <div class="block-title">同期フォルダ</div>
      <div class="surface-card" id="sync-list-card"></div>

      <div class="block-title">他端末へ持ち運ぶ（nihongo-setup.md）</div>
      <div class="surface-card" style="padding:16px;">
        <div class="export-row">
          <div>
            <label class="fld" for="exp-scene">既定の場面</label>
            <select id="exp-scene">
              <option value="work">社内・同僚</option>
              <option value="formal">社外・目上</option>
              <option value="casual">普段・雑談</option>
            </select>
          </div>
          <div>
            <label class="fld" for="exp-sync">保存先</label>
            <select id="exp-sync">
              <option value="local">ローカル</option>
              <option value="gdrive">Google Drive</option>
            </select>
          </div>
          <button class="btn primary" id="btn-export-dl" type="button">ダウンロード ↓</button>
        </div>
        <details style="margin-top:12px;">
          <summary style="cursor:pointer;font-size:12.5px;font-weight:600;color:var(--muted);">中身を確認</summary>
          <textarea class="mono" id="export-preview" readonly style="margin-top:8px;min-height:170px;border:1px solid var(--line);border-radius:8px;background:#FAFAFB;"></textarea>
        </details>
      </div>

      <div id="skills-section">
        <div class="block-title">組み込みルール</div>
        <div id="skills-wrap"></div>
      </div>
    </section>

    <!-- 4. Utility: 0-Token Check Panel -->
    <section class="panel" id="panel-check">
      <div class="page-head">
        <h1>動作テスト</h1>
        <div class="head-actions">
          <select id="check-scene" style="width:auto;">
            <option value="">場面指定なし</option>
            <option value="formal">社外・目上</option>
            <option value="work">社内・同僚</option>
            <option value="casual">普段・雑談</option>
          </select>
          <button class="btn primary" id="btn-run-check" type="button">検査する</button>
        </div>
      </div>

      <div class="grid-2">
        <div class="surface-card" style="padding:14px 16px;">
          <label class="fld" for="check-orig">元の文章（新規なら空欄）</label>
          <textarea id="check-orig" rows="7" placeholder="例：資料は明日15時までに必ず送ってください。"></textarea>
        </div>
        <div class="surface-card" style="padding:14px 16px;">
          <label class="fld" for="check-draft">AIの文章</label>
          <textarea id="check-draft" rows="7" placeholder="例：恐れ入りますが、資料は明日15時頃までにご送付いただけますと幸いです。"></textarea>
        </div>
      </div>
      <div id="check-result"></div>
    </section>
  </main>
</div>

<script>
const CSRF = {token_json};
let STATE = null;

const SCENE_META = [
  {{ key: 'common', title: '共通ルール', hint: '全場面' }},
  {{ key: 'work', title: '社内・同僚', hint: 'Slack・PR' }},
  {{ key: 'formal', title: '社外・目上', hint: '社外メール・公式' }},
  {{ key: 'casual', title: '普段・雑談', hint: '友達・メモ' }},
];

let toastTimer = null;
function showToast(msg, kind) {{
  const el = document.getElementById('toast');
  el.textContent = msg;
  el.className = 'toast show ' + (kind || '');
  if (toastTimer) clearTimeout(toastTimer);
  if (kind !== 'error') {{
    toastTimer = setTimeout(() => {{ el.className = 'toast'; }}, 4500);
  }}
}}

function switchTab(tabKey) {{
  const toastEl = document.getElementById('toast');
  if (toastEl && !toastEl.classList.contains('error')) {{
    toastEl.className = 'toast';
  }}
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.toggle('active', b.dataset.tab === tabKey));
  document.querySelectorAll('.panel').forEach(p => p.classList.toggle('active', p.id === 'panel-' + tabKey));
}}

async function apiGet(path) {{
  const res = await fetch(path, {{ credentials: 'same-origin' }});
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || ('HTTP ' + res.status));
  return data;
}}

async function apiPost(path, payload) {{
  const res = await fetch(path, {{
    method: 'POST',
    credentials: 'same-origin',
    headers: {{
      'Content-Type': 'application/json',
      'X-Nihongo-CSRF': CSRF,
    }},
    body: JSON.stringify(payload || {{}}),
  }});
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || ('HTTP ' + res.status));
  return data;
}}

async function copyCmd(text) {{
  try {{
    await navigator.clipboard.writeText(text);
    showToast('コピーしました: ' + text, 'ok');
  }} catch (_) {{
    const ta = document.createElement('textarea');
    ta.value = text;
    document.body.appendChild(ta);
    ta.select();
    document.execCommand('copy');
    ta.remove();
    showToast('コピーしました: ' + text, 'ok');
  }}
}}

function renderMeta(state) {{
  const bar = document.getElementById('meta-bar');
  bar.textContent = '';
  const st = document.createElement('span');
  st.className = 'local-status';
  st.title = state.profile.profile_path || '';
  st.textContent = 'ローカル';
  bar.appendChild(st);

  document.getElementById('editor-path').textContent = state.profile.profile_path || 'profile.md';
  const projCard = document.getElementById('project-raw-card');
  if (state.profile.project_profile_path) {{
    const b = document.createElement('span');
    b.className = 'layer-badge';
    b.title = state.profile.project_profile_path;
    b.textContent = '2層';
    bar.appendChild(b);
    projCard.style.display = 'block';
    document.getElementById('project-raw-path').textContent = state.profile.project_profile_path;
    document.getElementById('project-raw-editor').value = state.project_raw || '';
  }} else {{
    projCard.style.display = 'none';
  }}
}}

function renderSceneCards(state) {{
  const grid = document.getElementById('scene-grid');
  grid.textContent = '';
  const gStruct = state.structured_global || {{}};
  const pStruct = state.structured_project || null;

  SCENE_META.forEach(meta => {{
    const card = document.createElement('div');
    card.className = 'scene-card' + (meta.key === 'common' ? ' common-card' : '');

    const gSec = gStruct[meta.key] || {{ first_person: '', forbidden: [], rules: [] }};
    const pSec = pStruct ? (pStruct[meta.key] || {{ forbidden: [], rules: [] }}) : {{ forbidden: [], rules: [] }};

    const head = document.createElement('div');
    head.className = 'sc-head';
    const titleWrap = document.createElement('div');
    titleWrap.className = 'sc-title-wrap';
    const h2 = document.createElement('h2');
    h2.textContent = meta.title;
    const hint = document.createElement('span');
    hint.className = 'sc-hint';
    hint.textContent = meta.hint;
    titleWrap.appendChild(h2);
    titleWrap.appendChild(hint);
    head.appendChild(titleWrap);

    if (meta.key === 'common' && gSec.first_person) {{
      const fp = document.createElement('span');
      fp.className = 'pill';
      fp.textContent = '一人称：' + gSec.first_person;
      head.appendChild(fp);
    }}
    card.appendChild(head);

    const gForb = gSec.forbidden || [];
    const pForb = (pSec.forbidden || []).filter(w => !gForb.includes(w));
    const gRules = gSec.rules || [];
    const pRules = pSec.rules || [];

    if (gForb.length > 0 || pForb.length > 0) {{
      const ngSec = document.createElement('div');
      const ngLbl = document.createElement('div');
      ngLbl.className = 'sc-lbl';
      ngLbl.textContent = '避ける表現';
      ngSec.appendChild(ngLbl);

      const chips = document.createElement('div');
      chips.className = 'chip-wrap';
      gForb.forEach(word => {{
        const chip = document.createElement('span');
        chip.className = 'ng-chip';
        chip.appendChild(document.createTextNode(word));
        const xBtn = document.createElement('button');
        xBtn.type = 'button';
        xBtn.className = 'chip-x';
        xBtn.title = '「' + word + '」を削除';
        xBtn.textContent = '×';
        xBtn.addEventListener('click', async () => {{
          try {{
            await apiPost('/api/profile/remove-forbidden', {{ scene: meta.key, value: word }});
            showToast('「' + word + '」を削除しました。', 'ok');
            await loadState();
          }} catch (err) {{
            showToast('削除できませんでした: ' + err.message, 'error');
          }}
        }});
        chip.appendChild(xBtn);
        chips.appendChild(chip);
      }});
      pForb.forEach(word => {{
        const chip = document.createElement('span');
        chip.className = 'ng-chip project-chip';
        chip.appendChild(document.createTextNode(word));
        const pm = document.createElement('span');
        pm.className = 'mini-tag';
        pm.textContent = '案件';
        chip.appendChild(pm);
        chips.appendChild(chip);
      }});
      ngSec.appendChild(chips);
      card.appendChild(ngSec);
    }}

    if (gRules.length > 0 || pRules.length > 0) {{
      const rSec = document.createElement('div');
      if (gForb.length > 0 || pForb.length > 0) {{
        const rLbl = document.createElement('div');
        rLbl.className = 'sc-lbl';
        rLbl.textContent = meta.key === 'common' ? '書く時の考え方' : '口調・ルール';
        rSec.appendChild(rLbl);
      }}
      const ul = document.createElement('ul');
      ul.className = 'rule-list';
      gRules.forEach(r => {{
        const li = document.createElement('li');
        li.textContent = r;
        ul.appendChild(li);
      }});
      pRules.forEach(r => {{
        const li = document.createElement('li');
        const tag = document.createElement('span');
        tag.className = 'mini-tag';
        tag.textContent = '案件';
        li.appendChild(tag);
        li.appendChild(document.createTextNode(r));
        ul.appendChild(li);
      }});
      rSec.appendChild(ul);
      card.appendChild(rSec);
    }}

    if (gForb.length === 0 && pForb.length === 0 && gRules.length === 0 && pRules.length === 0) {{
      const empty = document.createElement('div');
      empty.className = 'muted-empty';
      empty.textContent = '未登録';
      card.appendChild(empty);
    }}
    grid.appendChild(card);
  }});
}}

function buildItemCard(item, isHistory) {{
  const card = document.createElement('div');
  card.className = 'item-card' + (item.warning && !isHistory ? ' warn' : '');

  const main = document.createElement('div');
  main.className = 'item-main';

  const meta = document.createElement('div');
  meta.className = 'item-meta';

  const p1 = document.createElement('span');
  p1.className = 'pill';
  p1.textContent = item.scene_label || item.scene;
  meta.appendChild(p1);

  const p2 = document.createElement('span');
  p2.className = 'pill';
  p2.textContent = item.kind_label || item.kind;
  meta.appendChild(p2);

  if (item.source) {{
    const src = document.createElement('span');
    src.textContent = item.source;
    meta.appendChild(src);
  }}
  if (isHistory) {{
    const st = document.createElement('span');
    st.className = 'pill ' + (item.status === 'approved' ? 'ok' : 'rej');
    st.textContent = item.status === 'approved' ? '承認' : '却下';
    meta.appendChild(st);
  }}
  main.appendChild(meta);

  const val = document.createElement('div');
  val.className = 'item-val';
  val.textContent = item.value || '';
  main.appendChild(val);

  if (item.reason) {{
    const r = document.createElement('div');
    r.className = 'item-note';
    r.textContent = item.reason;
    main.appendChild(r);
  }}
  if (item.example_before || item.example_after) {{
    const ex = document.createElement('div');
    ex.className = 'diff-line';
    ex.textContent = (item.example_before || '') + ' → ' + (item.example_after || '');
    main.appendChild(ex);
  }}

  let forceBox = null;
  if (!isHistory && item.warning) {{
    const w = document.createElement('div');
    w.className = 'warn-msg';
    w.textContent = item.warning;
    main.appendChild(w);

    const lbl = document.createElement('label');
    lbl.className = 'force-check';
    forceBox = document.createElement('input');
    forceBox.type = 'checkbox';
    lbl.appendChild(forceBox);
    lbl.appendChild(document.createTextNode('警告を確認した上で反映する'));
    main.appendChild(lbl);
  }}
  card.appendChild(main);

  if (!isHistory) {{
    const side = document.createElement('div');
    side.className = 'item-side';

    const btnOk = document.createElement('button');
    btnOk.type = 'button';
    btnOk.className = 'btn primary sm';
    btnOk.textContent = '承認';
    btnOk.addEventListener('click', async () => {{
      try {{
        const force = forceBox ? forceBox.checked : false;
        const res = await apiPost('/api/inbox/approve', {{ ids: [item.id], force }});
        if (res.blocked_by_guard && res.blocked_by_guard.length > 0) {{
          showToast('警告確認のチェックを入れてから承認してください。', 'error');
          return;
        }}
        showToast('承認して反映しました。', 'ok');
        await loadState();
      }} catch (err) {{
        showToast('承認できませんでした: ' + err.message, 'error');
      }}
    }});

    const btnRej = document.createElement('button');
    btnRej.type = 'button';
    btnRej.className = 'btn subtle sm';
    btnRej.textContent = '却下';
    btnRej.addEventListener('click', async () => {{
      try {{
        await apiPost('/api/inbox/reject', {{ ids: [item.id] }});
        showToast('却下しました。', 'ok');
        await loadState();
      }} catch (err) {{
        showToast('却下できませんでした: ' + err.message, 'error');
      }}
    }});

    side.appendChild(btnOk);
    side.appendChild(btnRej);
    card.appendChild(side);
  }}
  return card;
}}

function renderConnectPanel(state) {{
  const mcpEl = document.getElementById('mcp-list');
  mcpEl.textContent = '';
  (state.mcp_clients || []).forEach(c => {{
    const row = document.createElement('div');
    row.className = 'app-row';
    const name = document.createElement('div');
    name.className = 'app-name';
    name.title = c.config_path;
    name.textContent = c.label;

    const right = document.createElement('div');
    right.className = 'app-right';
    const badge = document.createElement('span');
    badge.className = 'pill ' + (c.configured ? 'ok' : 'rej');
    badge.textContent = c.configured ? '接続済み' : (c.error ? 'エラー' : '未接続');
    right.appendChild(badge);
    if (!c.configured) {{
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'btn sm';
      btn.textContent = '登録コマンドをコピー';
      btn.addEventListener('click', () => copyCmd(c.init_cmd));
      right.appendChild(btn);
    }}
    row.appendChild(name);
    row.appendChild(right);
    mcpEl.appendChild(row);
  }});

  const syncEl = document.getElementById('sync-list-card');
  syncEl.textContent = '';
  const folders = state.sync_folders || [];
  if (folders.length === 0) {{
    const r = document.createElement('div');
    r.className = 'app-row';
    r.textContent = '未検出（ローカル保存）';
    r.style.color = '#6E6E77';
    syncEl.appendChild(r);
  }} else {{
    folders.forEach(f => {{
      const row = document.createElement('div');
      row.className = 'app-row';
      const name = document.createElement('div');
      name.className = 'app-name';
      name.title = f.suggested_home;
      name.textContent = f.provider;

      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'btn sm';
      btn.textContent = '同期コマンドをコピー';
      btn.addEventListener('click', () => copyCmd('nihongo-mcp init --target all --home "' + f.suggested_home + '"'));
      row.appendChild(name);
      row.appendChild(btn);
      syncEl.appendChild(row);
    }});
  }}

  const skillsWrap = document.getElementById('skills-wrap');
  skillsWrap.textContent = '';
  const previews = state.skills_preview || {{}};
  const defs = [
    ['lite', 'Lite（nihongo/ALWAYS.md）'],
    ['web', 'Web・スマホ版（nihongo/WEB.md）'],
  ];
  let shown = 0;
  defs.forEach(([k, label]) => {{
    if (!previews[k]) return;
    shown++;
    const det = document.createElement('details');
    det.className = 'skill-box';
    const sum = document.createElement('summary');
    sum.textContent = label;
    const pre = document.createElement('pre');
    pre.className = 'skill-pre';
    pre.textContent = previews[k];
    det.appendChild(sum);
    det.appendChild(pre);
    skillsWrap.appendChild(det);
  }});
  document.getElementById('skills-section').style.display = shown > 0 ? 'block' : 'none';
}}

async function loadState() {{
  try {{
    STATE = await apiGet('/api/state');
    renderMeta(STATE);
    renderSceneCards(STATE);
    renderConnectPanel(STATE);

    const pending = STATE.pending_inbox || [];
    const cntEl = document.getElementById('pending-count');
    cntEl.textContent = String(pending.length);
    cntEl.className = 'count-dot' + (pending.length === 0 ? ' zero' : '');
    document.getElementById('btn-approve-all').disabled = pending.length === 0;

    const listEl = document.getElementById('inbox-list');
    listEl.textContent = '';
    if (pending.length === 0) {{
      const empty = document.createElement('div');
      empty.className = 'empty-box';
      empty.textContent = '承認待ちの候補はありません。';
      listEl.appendChild(empty);
    }} else {{
      pending.forEach(item => listEl.appendChild(buildItemCard(item, false)));
    }}

    const histEl = document.getElementById('history-list');
    histEl.textContent = '';
    const hist = STATE.history_inbox || [];
    if (hist.length === 0) {{
      const empty = document.createElement('div');
      empty.className = 'empty-box';
      empty.textContent = '履歴はまだありません。';
      histEl.appendChild(empty);
    }} else {{
      hist.forEach(item => histEl.appendChild(buildItemCard(item, true)));
    }}

    document.getElementById('profile-editor').value = STATE.profile.global_raw || STATE.default_template || '';
    await refreshExportPreview();
  }} catch (err) {{
    showToast('読み込みに失敗しました: ' + err.message, 'error');
  }}
}}

async function refreshExportPreview() {{
  try {{
    const scene = document.getElementById('exp-scene').value;
    const sync_preference = document.getElementById('exp-sync').value;
    const res = await apiPost('/api/setup/export', {{ scene, sync_preference }});
    document.getElementById('export-preview').value = res.markdown || '';
  }} catch (err) {{
    document.getElementById('export-preview').value = '生成エラー: ' + err.message;
  }}
}}

document.querySelectorAll('.tab-btn').forEach(btn => {{
  btn.addEventListener('click', () => switchTab(btn.dataset.tab));
}});
document.getElementById('btn-reload').addEventListener('click', loadState);

document.getElementById('mode-cards').addEventListener('click', () => {{
  document.getElementById('mode-cards').classList.add('active');
  document.getElementById('mode-raw').classList.remove('active');
  document.getElementById('view-cards').style.display = 'block';
  document.getElementById('view-raw').style.display = 'none';
}});
document.getElementById('mode-raw').addEventListener('click', () => {{
  document.getElementById('mode-raw').classList.add('active');
  document.getElementById('mode-cards').classList.remove('active');
  document.getElementById('view-raw').style.display = 'block';
  document.getElementById('view-cards').style.display = 'none';
}});

document.getElementById('btn-qa-add').addEventListener('click', async () => {{
  const scene = document.getElementById('qa-scene').value;
  const kind = document.getElementById('qa-kind').value;
  const inp = document.getElementById('qa-value');
  const value = inp.value.trim();
  if (!value) {{
    showToast('追加する内容を入力してください。', 'error');
    return;
  }}
  try {{
    const res = await apiPost('/api/profile/add-item', {{ scene, kind, value }});
    inp.value = '';
    showToast(res.message || '追加しました。', 'ok');
    await loadState();
  }} catch (err) {{
    showToast(err.message, 'error');
  }}
}});
document.getElementById('qa-value').addEventListener('keydown', (e) => {{
  if (e.key === 'Enter') {{
    e.preventDefault();
    document.getElementById('btn-qa-add').click();
  }}
}});

document.getElementById('btn-toggle-add').addEventListener('click', () => {{
  document.getElementById('add-form-box').classList.toggle('open');
}});
document.getElementById('btn-cancel-add').addEventListener('click', () => {{
  document.getElementById('add-form-box').classList.remove('open');
}});

document.getElementById('btn-toggle-history').addEventListener('click', () => {{
  const wrap = document.getElementById('history-wrap');
  const open = wrap.style.display === 'none';
  wrap.style.display = open ? 'block' : 'none';
  document.getElementById('btn-toggle-history').textContent = open ? '履歴を隠す' : '履歴';
}});

document.getElementById('btn-approve-all').addEventListener('click', async () => {{
  try {{
    const res = await apiPost('/api/inbox/approve', {{ approve_all: true, force: false }});
    const blocked = (res.blocked_by_guard || []).length;
    const msg = res.approved_count + '件を承認しました。' + (blocked ? '（警告付き ' + blocked + ' 件は個別確認）' : '');
    showToast(msg, 'ok');
    await loadState();
  }} catch (err) {{
    showToast('一括承認できませんでした: ' + err.message, 'error');
  }}
}});

document.getElementById('btn-propose').addEventListener('click', async () => {{
  const scene = document.getElementById('prop-scene').value;
  const kind = document.getElementById('prop-kind').value;
  const value = document.getElementById('prop-value').value.trim();
  const reason = document.getElementById('prop-reason').value.trim();
  if (!value) {{
    showToast('内容を入力してください。', 'error');
    return;
  }}
  try {{
    const res = await apiPost('/api/inbox/propose', {{ scene, kind, value, reason }});
    document.getElementById('prop-value').value = '';
    document.getElementById('prop-reason').value = '';
    document.getElementById('add-form-box').classList.remove('open');
    showToast(res.message || '受信箱に追加しました。', 'ok');
    await loadState();
  }} catch (err) {{
    showToast(err.message, 'error');
  }}
}});

document.getElementById('btn-save-profile').addEventListener('click', async () => {{
  const content = document.getElementById('profile-editor').value;
  try {{
    await apiPost('/api/profile/save', {{ content }});
    showToast('保存しました。', 'ok');
    await loadState();
  }} catch (err) {{
    showToast('保存できませんでした: ' + err.message, 'error');
  }}
}});

document.getElementById('btn-run-check').addEventListener('click', async () => {{
  const orig = document.getElementById('check-orig').value;
  const draft = document.getElementById('check-draft').value;
  const scene = document.getElementById('check-scene').value || null;
  if (!draft.trim()) {{
    showToast('検査対象の文章を入力してください。', 'error');
    return;
  }}
  try {{
    const res = await apiPost('/api/check', {{ orig, draft, scene }});
    const box = document.getElementById('check-result');
    box.textContent = '';
    const card = document.createElement('div');
    card.className = 'findings-box' + (res.count > 0 ? ' has-issue' : '');
    const title = document.createElement('div');
    title.style.fontWeight = '700';
    title.textContent = res.count === 0
      ? '見直す候補はありません（0トークン / ' + res.elapsed_ms + 'ms）'
      : '見直す候補が ' + res.count + ' 件あります（0トークン / ' + res.elapsed_ms + 'ms）';
    card.appendChild(title);
    if (res.findings && res.findings.length > 0) {{
      const ul = document.createElement('ul');
      res.findings.forEach(f => {{
        const li = document.createElement('li');
        li.textContent = f;
        ul.appendChild(li);
      }});
      card.appendChild(ul);
    }}
    box.appendChild(card);
  }} catch (err) {{
    showToast('検査に失敗しました: ' + err.message, 'error');
  }}
}});

document.getElementById('exp-scene').addEventListener('change', refreshExportPreview);
document.getElementById('exp-sync').addEventListener('change', refreshExportPreview);
document.getElementById('btn-export-dl').addEventListener('click', () => {{
  const md = document.getElementById('export-preview').value;
  const blob = new Blob([md], {{ type: 'text/markdown;charset=utf-8' }});
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'nihongo-setup.md';
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
  showToast('nihongo-setup.md をダウンロードしました。', 'ok');
}});

loadState();
</script>
</body>
</html>
"""
