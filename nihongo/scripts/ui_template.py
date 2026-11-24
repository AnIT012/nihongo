"""nihongo 全AI共通コントロールパネル UI テンプレート（白ベース・Linear/GitHub Settings系・外部通信ゼロ）。"""
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
<title>nihongo — ルール設定</title>
<style>
:root {{
  --bg: #FFFFFF;
  --sidebar: #FAFAFB;
  --subtle: #F6F6F8;
  --ink: #111113;
  --body: #27272A;
  --muted: #71717A;
  --line: #EAEAEE;
  --line-strong: #D4D4DC;
  --red: #D7261E;
  --red-soft: #FEF2F2;
  --red-ink: #B42318;
  --ok: #15803D;
  --ok-soft: #F0FDF4;
  --ok-line: #BBF7D0;
  --radius: 8px;
}}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
html, body {{ height: 100%; }}
body {{
  background: var(--bg);
  color: var(--ink);
  font-family: -apple-system, BlinkMacSystemFont, "Hiragino Sans", "Hiragino Kaku Gothic ProN", "Yu Gothic UI", "Meiryo", sans-serif;
  font-size: 14px;
  line-height: 1.65;
  -webkit-font-smoothing: antialiased;
  text-rendering: optimizeLegibility;
}}

.app {{
  display: grid;
  grid-template-columns: 236px minmax(0, 1fr);
  min-height: 100vh;
}}

/* Sidebar */
.sidebar {{
  background: var(--sidebar);
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
  padding: 2px 10px 18px;
}}
.logo {{
  font-family: ui-sans-serif, system-ui, -apple-system, sans-serif;
  font-weight: 800;
  font-size: 21px;
  letter-spacing: -0.03em;
  line-height: 1;
  color: var(--ink);
}}
.logo i {{
  display: inline-block;
  width: 0.44em;
  height: 0.44em;
  border-radius: 50%;
  background: var(--red);
  margin: 0 0.04em;
}}

.nav-section-lbl {{
  font-size: 11px;
  font-weight: 600;
  color: var(--muted);
  padding: 8px 10px 4px;
  letter-spacing: 0.02em;
}}
.nav-list {{
  display: flex;
  flex-direction: column;
  gap: 2px;
}}
.nav-sep {{
  height: 1px;
  background: var(--line);
  margin: 12px 10px;
}}
.tab-btn {{
  appearance: none;
  border: 0;
  background: transparent;
  color: var(--body);
  font: inherit;
  font-size: 13.5px;
  font-weight: 500;
  padding: 8px 10px;
  border-radius: 7px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: space-between;
  text-align: left;
  transition: background 0.12s ease, color 0.12s ease;
}}
.tab-btn:hover {{ background: #EFEFF3; color: var(--ink); }}
.tab-btn.active {{
  background: #EAEAEF;
  color: var(--ink);
  font-weight: 600;
}}
.tab-btn.muted-nav {{
  color: var(--muted);
  font-size: 13px;
}}
.tab-btn.muted-nav.active {{ color: var(--ink); }}
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

.nav-badge {{
  font-size: 11px;
  font-weight: 600;
  padding: 1px 7px;
  border-radius: 999px;
  min-width: 20px;
  text-align: center;
  background: var(--ink);
  color: #FFFFFF;
  line-height: 1.5;
}}
.nav-badge.zero {{
  background: transparent;
  color: var(--muted);
}}

.side-foot {{
  border-top: 1px solid var(--line);
  padding: 14px 10px 2px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}}
.status-row {{
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}}
.status-live {{
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 500;
  color: var(--body);
}}
.dot-ok {{
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #16A34A;
  flex-shrink: 0;
}}
.dot-red {{
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--red);
  flex-shrink: 0;
}}
.dot-muted {{
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #C4C4CE;
  flex-shrink: 0;
}}
.side-meta {{
  font-size: 11.5px;
  color: var(--muted);
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: center;
}}
.micro-tag {{
  display: inline-flex;
  align-items: center;
  padding: 1px 6px;
  border-radius: 4px;
  font-size: 10.5px;
  font-weight: 600;
  border: 1px solid var(--line-strong);
  color: var(--body);
  background: var(--bg);
}}
.btn-text {{
  appearance: none;
  border: 0;
  background: transparent;
  color: var(--muted);
  font: inherit;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  padding: 2px 4px;
  border-radius: 5px;
}}
.btn-text:hover {{ color: var(--ink); background: #EFEFF3; }}

/* Main Centered Settings Canvas */
.main-wrap {{
  background: var(--bg);
  min-width: 0;
}}
.main {{
  max-width: 820px;
  margin: 0 auto;
  padding: 36px 32px 84px;
  width: 100%;
}}
.panel {{ display: none; }}
.panel.active {{ display: block; }}

.toast {{
  display: none;
  margin-bottom: 18px;
  padding: 10px 14px;
  border-radius: var(--radius);
  font-size: 13px;
  font-weight: 500;
  border: 1px solid var(--line-strong);
  background: var(--subtle);
  color: var(--ink);
}}
.toast.show {{ display: block; }}
.toast.error {{
  border-color: #FECACA;
  background: var(--red-soft);
  color: var(--red-ink);
}}
.toast.ok {{
  border-color: var(--ok-line);
  background: var(--ok-soft);
  color: var(--ok);
}}

/* Page Header */
.page-head {{
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  flex-wrap: wrap;
  gap: 14px;
  padding-bottom: 20px;
  border-bottom: 1px solid var(--line);
  margin-bottom: 20px;
}}
.page-head h1 {{
  font-size: 20px;
  font-weight: 700;
  letter-spacing: -0.02em;
  line-height: 1.3;
  color: var(--ink);
}}
.page-sub {{
  font-size: 13px;
  color: var(--muted);
  margin-top: 4px;
}}
.head-actions {{
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}}

/* Quiet Pending Callout (below header, neutral tone) */
.pending-callout {{
  display: none;
  margin-bottom: 20px;
  padding: 10px 14px;
  border-radius: var(--radius);
  background: var(--sidebar);
  border: 1px solid var(--line);
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}}
.pending-callout.show {{ display: flex; }}
.pending-callout-left {{
  display: inline-flex;
  align-items: center;
  gap: 9px;
  font-size: 13px;
  color: var(--body);
  font-weight: 500;
}}

/* Segmented Control */
.seg {{
  display: inline-flex;
  background: var(--subtle);
  border: 1px solid var(--line);
  padding: 2px;
  border-radius: 7px;
  gap: 2px;
}}
.seg-btn {{
  appearance: none;
  border: 0;
  background: transparent;
  color: var(--muted);
  font: inherit;
  font-size: 12.5px;
  font-weight: 600;
  padding: 5px 11px;
  border-radius: 5px;
  cursor: pointer;
}}
.seg-btn.active {{
  background: var(--bg);
  color: var(--ink);
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.06);
}}

/* Buttons (Ink Black primary, crisp secondary) */
.btn {{
  appearance: none;
  border: 1px solid var(--line-strong);
  background: var(--bg);
  color: var(--ink);
  font: inherit;
  font-size: 13px;
  font-weight: 500;
  padding: 6px 12px;
  border-radius: 7px;
  cursor: pointer;
  transition: background 0.12s ease, border-color 0.12s ease;
  white-space: nowrap;
}}
.btn:hover {{ background: var(--subtle); border-color: #B8B8C4; }}
.btn.primary {{
  background: var(--ink);
  border-color: var(--ink);
  color: #FFFFFF;
  font-weight: 600;
}}
.btn.primary:hover {{ background: #27272A; border-color: #27272A; }}
.btn.subtle {{
  border-color: transparent;
  background: transparent;
  color: var(--muted);
}}
.btn.subtle:hover {{ color: var(--ink); background: var(--subtle); }}
.btn.sm {{ padding: 4px 10px; font-size: 12px; }}
.btn:disabled {{ opacity: 0.4; cursor: not-allowed; }}

/* Quick Add Strip */
.quick-add {{
  background: var(--sidebar);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  padding: 10px 12px;
  margin-bottom: 18px;
  display: grid;
  grid-template-columns: 136px 148px minmax(0, 1fr) auto;
  gap: 8px;
  align-items: center;
}}

/* Scene Filter Pills */
.filter-bar {{
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 6px;
}}
.filter-pill {{
  appearance: none;
  border: 1px solid transparent;
  background: transparent;
  color: var(--muted);
  font: inherit;
  font-size: 12.5px;
  font-weight: 500;
  padding: 4px 10px;
  border-radius: 6px;
  cursor: pointer;
}}
.filter-pill:hover {{ color: var(--ink); background: var(--subtle); }}
.filter-pill.active {{
  color: var(--ink);
  background: var(--subtle);
  border-color: var(--line);
  font-weight: 600;
}}

/* Hairline Settings Sections (Personal 4 Scenes) */
.scene-list {{
  display: flex;
  flex-direction: column;
}}
.scene-section {{
  padding: 20px 0;
  border-bottom: 1px solid var(--line);
  display: grid;
  grid-template-columns: 200px minmax(0, 1fr);
  gap: 24px;
  align-items: start;
}}
.scene-section:last-child {{ border-bottom: 0; }}
.sc-left h2 {{
  font-size: 14.5px;
  font-weight: 700;
  color: var(--ink);
  display: flex;
  align-items: center;
  gap: 7px;
}}
.sc-code {{
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 11px;
  font-weight: 500;
  color: var(--muted);
}}
.sc-sub {{
  font-size: 12px;
  color: var(--muted);
  margin-top: 3px;
  line-height: 1.5;
}}
.sc-right {{
  display: flex;
  flex-direction: column;
  gap: 14px;
  min-width: 0;
}}
.sc-group-lbl {{
  font-size: 11.5px;
  font-weight: 600;
  color: var(--muted);
  margin-bottom: 6px;
}}

/* Calm Neutral NG Tags */
.chip-wrap {{
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}}
.ng-chip {{
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 3px 9px;
  border-radius: 6px;
  background: var(--subtle);
  border: 1px solid var(--line);
  color: var(--ink);
  font-size: 12.5px;
  font-weight: 500;
}}
.ng-chip.project-chip {{
  background: var(--bg);
  border-color: var(--line-strong);
}}
.chip-x {{
  appearance: none;
  border: 0;
  background: transparent;
  color: var(--muted);
  font-size: 14px;
  line-height: 1;
  cursor: pointer;
  padding: 0 2px;
  border-radius: 3px;
}}
.chip-x:hover {{ color: var(--red-ink); background: var(--red-soft); }}

.rule-list {{
  list-style: none;
  display: flex;
  flex-direction: column;
}}
.rule-list li {{
  font-size: 13.5px;
  color: var(--body);
  padding: 6px 0;
  border-bottom: 1px solid #F3F3F6;
  display: flex;
  align-items: baseline;
  gap: 8px;
}}
.rule-list li:last-child {{ border-bottom: 0; padding-bottom: 0; }}
.rule-list li:first-child {{ padding-top: 0; }}
.muted-empty {{
  font-size: 12.5px;
  color: var(--muted);
}}

/* Clean Bordered Table / Editor Container */
.box-frame {{
  background: var(--bg);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  overflow: hidden;
}}
.editor-bar {{
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 9px 14px;
  border-bottom: 1px solid var(--line);
  background: var(--sidebar);
  font-size: 12px;
  color: var(--muted);
  gap: 10px;
  flex-wrap: wrap;
}}
.mono-path {{
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 11.5px;
  color: var(--muted);
  word-break: break-all;
}}

/* Inbox List (Clean Rows inside Hairline Frame) */
.card-list {{
  display: flex;
  flex-direction: column;
  gap: 10px;
}}
.item-card {{
  background: var(--bg);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  padding: 15px 16px;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
}}
.item-card.warn {{
  border-color: #FECACA;
  background: #FFFCFC;
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
  padding: 1px 7px;
  border-radius: 5px;
  font-size: 11.5px;
  font-weight: 500;
  background: var(--subtle);
  color: var(--body);
  border: 1px solid var(--line);
}}
.pill.ok {{ background: var(--ok-soft); color: var(--ok); border-color: var(--ok-line); }}
.pill.rej {{ background: var(--subtle); color: var(--muted); border-color: var(--line); }}
.item-val {{
  font-size: 15px;
  font-weight: 600;
  color: var(--ink);
  word-break: break-word;
  margin-bottom: 3px;
}}
.item-note {{ font-size: 13px; color: var(--muted); margin-top: 2px; }}
.diff-line {{
  display: inline-block;
  margin-top: 7px;
  font-size: 12.5px;
  color: var(--body);
  background: var(--sidebar);
  border: 1px solid var(--line);
  border-radius: 6px;
  padding: 4px 9px;
}}
.warn-msg {{
  margin-top: 8px;
  font-size: 12.5px;
  font-weight: 500;
  color: var(--red-ink);
}}
.item-side {{ display: flex; flex-direction: column; align-items: flex-end; gap: 8px; flex-shrink: 0; }}
.item-actions {{ display: flex; gap: 6px; align-items: center; }}
.force-check {{
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 500;
  color: var(--red-ink);
  margin-top: 8px;
}}

.empty-box {{
  border: 1px dashed var(--line-strong);
  border-radius: var(--radius);
  padding: 28px 20px;
  text-align: center;
  color: var(--muted);
  font-size: 13px;
}}

/* Collapsible Form */
.form-box {{
  display: none;
  margin-bottom: 16px;
  background: var(--sidebar);
  border: 1px solid var(--line-strong);
  border-radius: var(--radius);
  padding: 16px 18px;
}}
.form-box.open {{ display: block; }}
.form-box h3 {{ font-size: 14px; font-weight: 600; margin-bottom: 12px; }}

/* Settings Rows (Connect & Sync) */
.block-title {{
  font-size: 13px;
  font-weight: 600;
  color: var(--ink);
  margin: 24px 0 8px;
}}
.block-title:first-of-type {{ margin-top: 0; }}
.block-desc {{
  font-size: 12.5px;
  color: var(--muted);
  margin-bottom: 10px;
}}
.app-row {{
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  padding: 11px 14px;
  border-top: 1px solid var(--line);
  flex-wrap: wrap;
}}
.app-row:first-child {{ border-top: 0; }}
.app-name {{
  font-weight: 600;
  font-size: 13.5px;
  color: var(--ink);
  display: inline-flex;
  align-items: center;
  gap: 8px;
}}
.app-path {{
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 11px;
  color: var(--muted);
  margin-top: 2px;
  word-break: break-all;
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
  color: var(--body);
  margin-bottom: 5px;
}}
input[type="text"], select, textarea {{
  width: 100%;
  font: inherit;
  font-size: 13px;
  padding: 7px 10px;
  border: 1px solid var(--line-strong);
  border-radius: 7px;
  background: var(--bg);
  color: var(--ink);
}}
input[type="text"]:focus, select:focus, textarea:focus {{
  outline: none;
  border-color: var(--ink);
  box-shadow: 0 0 0 2px rgba(17, 17, 19, 0.08);
}}
textarea.mono {{
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 12.5px;
  line-height: 1.65;
  min-height: 300px;
  border: 0;
  border-radius: 0;
  padding: 14px 16px;
  resize: vertical;
}}
textarea.mono:focus {{ box-shadow: none; }}

.findings-box {{
  margin-top: 16px;
  border: 1px solid var(--line-strong);
  border-radius: var(--radius);
  padding: 14px 16px;
  background: var(--bg);
}}
.findings-box.has-issue {{
  border-color: #FECACA;
  background: #FFFCFC;
}}
.findings-box ul {{ margin-top: 8px; padding-left: 18px; }}
.findings-box li {{ margin: 4px 0; font-size: 13px; color: var(--body); }}

details.skill-box {{
  border: 1px solid var(--line);
  border-radius: var(--radius);
  padding: 10px 14px;
  margin-top: 8px;
  background: var(--bg);
}}
details.skill-box summary {{
  cursor: pointer;
  font-weight: 600;
  font-size: 13px;
  color: var(--ink);
}}
pre.skill-pre {{
  margin-top: 10px;
  padding: 12px 14px;
  background: var(--sidebar);
  border-radius: 6px;
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
  font-weight: 600;
  color: var(--muted);
  margin: 24px 0 10px;
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
  .brand-block {{ padding: 0 0 12px; }}
  .nav-section-lbl {{ display: none; }}
  .nav-list {{ flex-direction: row; flex-wrap: wrap; gap: 4px; }}
  .nav-sep {{ display: none; }}
  .tab-btn {{ padding: 6px 10px; font-size: 12.5px; }}
  .side-foot {{
    margin-top: 10px;
    padding: 10px 0 0;
  }}
  .main {{ padding: 22px 16px 56px; }}
  .quick-add {{ grid-template-columns: 1fr; }}
  .scene-section {{ grid-template-columns: 1fr; gap: 12px; }}
  .grid-2 {{ grid-template-columns: 1fr; }}
  .item-card {{ flex-direction: column; gap: 12px; }}
  .item-side {{ align-items: flex-start; width: 100%; }}
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
      <div class="nav-section-lbl">ルール管理</div>
      <nav class="nav-list" aria-label="メニュー">
        <button class="tab-btn active" data-tab="profile" type="button">
          <span class="tab-left">
            <svg class="tab-ico" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><line x1="2.5" y1="4" x2="13.5" y2="4"/><circle cx="6" cy="4" r="1.4" fill="currentColor"/><line x1="2.5" y1="8" x2="13.5" y2="8"/><circle cx="10.5" cy="8" r="1.4" fill="currentColor"/><line x1="2.5" y1="12" x2="13.5" y2="12"/><circle cx="5.5" cy="12" r="1.4" fill="currentColor"/></svg>
            自分のルール
          </span>
        </button>
        <button class="tab-btn" data-tab="inbox" type="button">
          <span class="tab-left">
            <svg class="tab-ico" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M2.5 9.5V12.5A1 1 0 0 0 3.5 13.5H12.5A1 1 0 0 0 13.5 12.5V9.5"/><path d="M2.5 9.5L4.3 3.5H11.7L13.5 9.5H10.3L9.3 11H6.7L5.7 9.5H2.5Z"/></svg>
            承認待ち
          </span>
          <span class="nav-badge zero" id="pending-count">0</span>
        </button>
        <button class="tab-btn" data-tab="connect" type="button">
          <span class="tab-left">
            <svg class="tab-ico" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6.5 9.5L9.5 6.5"/><path d="M9 11L7.3 12.7A2.6 2.6 0 1 1 3.6 9L5.3 7.3"/><path d="M7 5L8.7 3.3A2.6 2.6 0 1 1 12.4 7L10.7 8.7"/></svg>
            AI接続・同期
          </span>
        </button>
        <div class="nav-sep"></div>
        <button class="tab-btn muted-nav" data-tab="check" type="button">
          <span class="tab-left">
            <svg class="tab-ico" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M8 2L13 4V7.8C13 10.9 10.9 13.1 8 14C5.1 13.1 3 10.9 3 7.8V4L8 2Z"/><path d="M5.8 8.2L7.3 9.7L10.4 6.6"/></svg>
            動作テスト（0トークン）
          </span>
        </button>
      </nav>
    </div>

    <div class="side-foot">
      <div class="status-row">
        <span class="status-live"><span class="dot-ok"></span>ローカル稼働中</span>
        <button class="btn-text" id="btn-reload" type="button">更新</button>
      </div>
      <div class="side-meta" id="meta-bar"></div>
    </div>
  </aside>

  <div class="main-wrap">
    <main class="main">
      <div class="toast" id="toast" role="status" aria-live="polite"></div>

      <!-- 1. Personal Rules Panel -->
      <section class="panel active" id="panel-profile">
        <div class="page-head">
          <div>
            <h1>自分のルール</h1>
            <p class="page-sub">接続中の全AIが共通で参照する profile.md の内容です。外部サーバーへは送信されません。</p>
          </div>
          <div class="head-actions">
            <div class="seg" role="tablist" aria-label="表示形式">
              <button class="seg-btn active" id="mode-cards" type="button">一覧</button>
              <button class="seg-btn" id="mode-raw" type="button">Markdown</button>
            </div>
          </div>
        </div>

        <div class="pending-callout" id="pending-banner">
          <span class="pending-callout-left">
            <span class="dot-red"></span>
            <span id="pending-banner-txt">承認待ちの候補があります</span>
          </span>
          <button class="btn sm" id="btn-goto-inbox" type="button">確認する →</button>
        </div>

        <!-- Structured List View -->
        <div id="view-cards">
          <div class="quick-add">
            <select id="qa-scene" aria-label="場面">
              <option value="common">共通（全場面）</option>
              <option value="work">社内・同僚</option>
              <option value="formal">社外・目上</option>
              <option value="casual">普段・雑談</option>
            </select>
            <select id="qa-kind" aria-label="種類">
              <option value="forbidden">避ける表現（NG）</option>
              <option value="rule">書く時の考え方</option>
              <option value="tone">口調・記号</option>
              <option value="first_person">一人称</option>
            </select>
            <input type="text" id="qa-value" placeholder="追加する表現やルールを入力（例：ご査収のほど）">
            <button class="btn primary" id="btn-qa-add" type="button">追加</button>
          </div>

          <div class="filter-bar" id="scene-filter">
            <button class="filter-pill active" data-filter="all" type="button">すべて</button>
            <button class="filter-pill" data-filter="common" type="button">共通</button>
            <button class="filter-pill" data-filter="work" type="button">社内・同僚</button>
            <button class="filter-pill" data-filter="formal" type="button">社外・目上</button>
            <button class="filter-pill" data-filter="casual" type="button">普段・雑談</button>
          </div>

          <div class="scene-list" id="scene-grid"></div>
        </div>

        <!-- Raw Markdown Editor View -->
        <div id="view-raw" style="display:none;">
          <div class="box-frame">
            <div class="editor-bar">
              <span class="mono-path" id="editor-path">profile.md</span>
              <div style="display:flex;align-items:center;gap:10px;">
                <span>UTF-8 · PII自動ガード</span>
                <button class="btn primary sm" id="btn-save-profile" type="button">変更を保存</button>
              </div>
            </div>
            <textarea class="mono" id="profile-editor" spellcheck="false"></textarea>
          </div>
          <div class="box-frame" id="project-raw-card" style="display:none;margin-top:14px;">
            <div class="editor-bar">
              <span class="mono-path" id="project-raw-path">案件別（.nihongo/profile.md）</span>
              <span>読み取り専用 · 2層適用中</span>
            </div>
            <textarea class="mono" id="project-raw-editor" readonly style="min-height:140px;background:#FAFAFB;"></textarea>
          </div>
        </div>
      </section>

      <!-- 2. Pending Inbox Panel -->
      <section class="panel" id="panel-inbox">
        <div class="page-head">
          <div>
            <h1>承認待ち</h1>
            <p class="page-sub">会話から拾われた候補です。承認した項目だけを profile.md へ反映します。</p>
          </div>
          <div class="head-actions">
            <button class="btn" id="btn-toggle-add" type="button">候補を追加</button>
            <button class="btn primary" id="btn-approve-all" type="button">警告なしを一括承認</button>
            <button class="btn subtle" id="btn-toggle-history" type="button">履歴</button>
          </div>
        </div>

        <div class="form-box" id="add-form-box">
          <h3>候補を受信箱に追加</h3>
          <div class="grid-2">
            <div>
              <label class="fld" for="prop-scene">適用する場面</label>
              <select id="prop-scene">
                <option value="common">共通（全場面）</option>
                <option value="casual">普段・雑談</option>
                <option value="work">社内・同僚</option>
                <option value="formal">社外・目上</option>
              </select>
            </div>
            <div>
              <label class="fld" for="prop-kind">種類</label>
              <select id="prop-kind">
                <option value="forbidden">避ける表現（NG）</option>
                <option value="rule">書く時の考え方</option>
                <option value="tone">口調・記号</option>
                <option value="first_person">一人称</option>
              </select>
            </div>
          </div>
          <div style="margin-bottom:10px;">
            <label class="fld" for="prop-value">内容（1行・個人情報は含めない）</label>
            <input type="text" id="prop-value" placeholder="例：いただけますと幸いです">
          </div>
          <div style="margin-bottom:14px;">
            <label class="fld" for="prop-reason">理由メモ（任意）</label>
            <input type="text" id="prop-reason" placeholder="例：メールの結びが硬くなりすぎるため">
          </div>
          <div style="display:flex;gap:8px;">
            <button class="btn primary" id="btn-propose" type="button">受信箱に追加</button>
            <button class="btn subtle" id="btn-cancel-add" type="button">閉じる</button>
          </div>
        </div>

        <div class="card-list" id="inbox-list"></div>

        <div id="history-wrap" style="display:none;">
          <div class="history-head">処理済みの履歴（最新20件）</div>
          <div class="card-list" id="history-list"></div>
        </div>
      </section>

      <!-- 3. All-AI Connect & Sync Panel -->
      <section class="panel" id="panel-connect">
        <div class="page-head">
          <div>
            <h1>AI接続・同期</h1>
            <p class="page-sub">このPC内のAIアプリ接続、複数端末同期、他端末への持ち運び設定を確認できます。</p>
          </div>
        </div>

        <div class="block-title">この PC の AI アプリ（MCP）</div>
        <div class="box-frame" id="mcp-list"></div>

        <div class="block-title">複数 PC 同期フォルダ</div>
        <div class="box-frame" id="sync-list-card"></div>

        <div class="block-title">他 PC・スマホ AI へ持ち運ぶ（nihongo-setup.md）</div>
        <div class="box-frame" style="padding:16px;">
          <div class="grid-2" style="margin-bottom:12px;">
            <div>
              <label class="fld" for="exp-scene">既定の場面</label>
              <select id="exp-scene">
                <option value="work">仕事・社内チャット・ドキュメント</option>
                <option value="formal">社外メール・目上・公式お知らせ</option>
                <option value="casual">普段のチャット・雑談</option>
              </select>
            </div>
            <div>
              <label class="fld" for="exp-sync">他 PC 導入時の推奨保存先</label>
              <select id="exp-sync">
                <option value="local">ローカル（~/.nihongo/profile.md）</option>
                <option value="gdrive">自分の Google Drive 同期フォルダ</option>
              </select>
            </div>
          </div>
          <button class="btn primary" id="btn-export-dl" type="button">今のルール入り nihongo-setup.md をダウンロード</button>
          <details style="margin-top:12px;">
            <summary style="cursor:pointer;font-size:12.5px;font-weight:500;color:var(--muted);">生成ファイルの中身を見る</summary>
            <textarea class="mono" id="export-preview" readonly style="margin-top:8px;min-height:180px;border:1px solid var(--line);border-radius:6px;background:#FAFAFB;"></textarea>
          </details>
        </div>

        <div class="block-title">組み込みルールの中身（読み取り専用）</div>
        <div id="skills-wrap"></div>
      </section>

      <!-- 4. Utility: 0-Token Test Panel -->
      <section class="panel" id="panel-check">
        <div class="page-head">
          <div>
            <h1>動作テスト（0トークン検査）</h1>
            <p class="page-sub">普段はフックやMCPが裏で自動実行する検査エンジンを、送信前チェック用に試せます。</p>
          </div>
          <div class="head-actions">
            <select id="check-scene" style="width:auto;">
              <option value="">場面指定なし</option>
              <option value="formal">社外・目上（formal）</option>
              <option value="work">社内・同僚（work）</option>
              <option value="casual">普段・雑談（casual）</option>
            </select>
            <button class="btn primary" id="btn-run-check" type="button">検査する</button>
          </div>
        </div>

        <div class="grid-2">
          <div>
            <label class="fld" for="check-orig">元の文章（新規作成の文なら空欄）</label>
            <textarea id="check-orig" rows="7" placeholder="例：資料は明日15時までに必ず送ってください。"></textarea>
          </div>
          <div>
            <label class="fld" for="check-draft">AIが書いた・直した文章</label>
            <textarea id="check-draft" rows="7" placeholder="例：恐れ入りますが、資料は明日15時頃までにご送付いただけますと幸いです。"></textarea>
          </div>
        </div>
        <div id="check-result"></div>
      </section>
    </main>
  </div>
</div>

<script>
const CSRF = {token_json};
let STATE = null;
let ACTIVE_FILTER = 'all';

const SCENE_META = [
  {{ key: 'common', title: '共通ルール', sub: '全場面で適用する一人称・NG表現・基本方針' }},
  {{ key: 'work', title: '社内・同僚', sub: 'Slack・PR・社内ドキュメント' }},
  {{ key: 'formal', title: '社外・目上', sub: '取引先メール・公式お知らせ（崩しガード対象）' }},
  {{ key: 'casual', title: '普段・雑談', sub: '友達・メモ・カジュアルな連絡' }},
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
    showToast('コマンドをコピーしました: ' + text, 'ok');
  }} catch (_) {{
    const ta = document.createElement('textarea');
    ta.value = text;
    document.body.appendChild(ta);
    ta.select();
    document.execCommand('copy');
    ta.remove();
    showToast('コマンドをコピーしました: ' + text, 'ok');
  }}
}}

function renderMeta(state) {{
  const bar = document.getElementById('meta-bar');
  bar.textContent = '';

  const p = document.createElement('span');
  p.title = state.profile.profile_path || '';
  p.textContent = 'profile.md';
  bar.appendChild(p);

  const projCard = document.getElementById('project-raw-card');
  if (state.profile.project_profile_path) {{
    const l = document.createElement('span');
    l.className = 'micro-tag';
    l.title = state.profile.project_profile_path;
    l.textContent = '2層適用中';
    bar.appendChild(l);
    projCard.style.display = 'block';
    document.getElementById('project-raw-path').textContent = state.profile.project_profile_path;
    document.getElementById('project-raw-editor').value = state.project_raw || '';
  }} else {{
    projCard.style.display = 'none';
  }}
  document.getElementById('editor-path').textContent = state.profile.profile_path || 'profile.md';
}}

function renderSceneCards(state) {{
  const list = document.getElementById('scene-grid');
  list.textContent = '';
  const gStruct = state.structured_global || {{}};
  const pStruct = state.structured_project || null;

  SCENE_META.forEach(meta => {{
    if (ACTIVE_FILTER !== 'all' && ACTIVE_FILTER !== meta.key) return;

    const sec = document.createElement('div');
    sec.className = 'scene-section scene-card';

    const left = document.createElement('div');
    left.className = 'sc-left';
    const h2 = document.createElement('h2');
    h2.textContent = meta.title;
    const code = document.createElement('span');
    code.className = 'sc-code';
    code.textContent = '[' + meta.key + ']';
    h2.appendChild(code);
    const sub = document.createElement('div');
    sub.className = 'sc-sub';
    sub.textContent = meta.sub;
    left.appendChild(h2);
    left.appendChild(sub);
    sec.appendChild(left);

    const right = document.createElement('div');
    right.className = 'sc-right';

    const gSec = gStruct[meta.key] || {{ first_person: '', forbidden: [], rules: [] }};
    const pSec = pStruct ? (pStruct[meta.key] || {{ forbidden: [], rules: [] }}) : {{ forbidden: [], rules: [] }};

    if (meta.key === 'common' && gSec.first_person) {{
      const fpWrap = document.createElement('div');
      const fpLbl = document.createElement('div');
      fpLbl.className = 'sc-group-lbl';
      fpLbl.textContent = '一人称';
      const fpVal = document.createElement('span');
      fpVal.className = 'pill';
      fpVal.textContent = gSec.first_person;
      fpWrap.appendChild(fpLbl);
      fpWrap.appendChild(fpVal);
      right.appendChild(fpWrap);
    }}

    // Forbidden chips (calm neutral style)
    const gForb = gSec.forbidden || [];
    const pForb = (pSec.forbidden || []).filter(w => !gForb.includes(w));
    const gRules = gSec.rules || [];
    const pRules = pSec.rules || [];

    if (gForb.length > 0 || pForb.length > 0 || meta.key === 'common') {{
      const ngSec = document.createElement('div');
      const ngLbl = document.createElement('div');
      ngLbl.className = 'sc-group-lbl';
      ngLbl.textContent = '避ける表現（NG）';
      ngSec.appendChild(ngLbl);

      const chips = document.createElement('div');
      chips.className = 'chip-wrap';
      if (gForb.length === 0 && pForb.length === 0) {{
        const empty = document.createElement('span');
        empty.className = 'muted-empty';
        empty.textContent = '未登録';
        chips.appendChild(empty);
      }} else {{
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
          pm.className = 'micro-tag';
          pm.textContent = '案件';
          chip.appendChild(pm);
          chips.appendChild(chip);
        }});
      }}
      ngSec.appendChild(chips);
      right.appendChild(ngSec);
    }}

    // Style rules
    const rSec = document.createElement('div');
    const rLbl = document.createElement('div');
    rLbl.className = 'sc-group-lbl';
    rLbl.textContent = meta.key === 'common' ? '書く時の考え方' : '口調・ルール';
    rSec.appendChild(rLbl);

    if (gRules.length === 0 && pRules.length === 0) {{
      const empty = document.createElement('span');
      empty.className = 'muted-empty';
      empty.textContent = 'まだ登録がありません';
      rSec.appendChild(empty);
    }} else {{
      const ul = document.createElement('ul');
      ul.className = 'rule-list';
      gRules.forEach(r => {{
        const li = document.createElement('li');
        li.textContent = r;
        ul.appendChild(li);
      }});
      pRules.forEach(r => {{
        const li = document.createElement('li');
        const badge = document.createElement('span');
        badge.className = 'micro-tag';
        badge.textContent = '案件';
        li.appendChild(badge);
        li.appendChild(document.createTextNode(r));
        ul.appendChild(li);
      }});
      rSec.appendChild(ul);
    }}
    right.appendChild(rSec);

    sec.appendChild(right);
    list.appendChild(sec);
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
    src.textContent = 'via ' + item.source;
    meta.appendChild(src);
  }}
  if (isHistory) {{
    const st = document.createElement('span');
    st.className = 'pill ' + (item.status === 'approved' ? 'ok' : 'rej');
    st.textContent = item.status === 'approved' ? '承認済み' : '却下済み';
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
    const actions = document.createElement('div');
    actions.className = 'item-actions';

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
        showToast('承認して profile.md に反映しました。', 'ok');
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
        showToast('候補を却下しました（profile.md は変更していません）。', 'ok');
        await loadState();
      }} catch (err) {{
        showToast('却下できませんでした: ' + err.message, 'error');
      }}
    }});

    actions.appendChild(btnOk);
    actions.appendChild(btnRej);
    side.appendChild(actions);
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
    const left = document.createElement('div');
    const name = document.createElement('div');
    name.className = 'app-name';
    const dot = document.createElement('span');
    dot.className = c.configured ? 'dot-ok' : 'dot-muted';
    name.appendChild(dot);
    name.appendChild(document.createTextNode(c.label));
    const p = document.createElement('div');
    p.className = 'app-path';
    p.textContent = c.config_path;
    left.appendChild(name);
    left.appendChild(p);

    const right = document.createElement('div');
    right.style.display = 'flex';
    right.style.alignItems = 'center';
    right.style.gap = '8px';
    const badge = document.createElement('span');
    badge.className = 'pill ' + (c.configured ? 'ok' : 'rej');
    badge.textContent = c.configured ? '接続済み' : (c.error ? 'JSONエラー' : '未設定');
    right.appendChild(badge);
    if (!c.configured) {{
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'btn sm';
      btn.textContent = 'コマンドをコピー';
      btn.addEventListener('click', () => copyCmd(c.init_cmd));
      right.appendChild(btn);
    }}
    row.appendChild(left);
    row.appendChild(right);
    mcpEl.appendChild(row);
  }});

  const syncEl = document.getElementById('sync-list-card');
  syncEl.textContent = '';
  const folders = state.sync_folders || [];
  if (folders.length === 0) {{
    const r = document.createElement('div');
    r.className = 'app-row';
    r.textContent = 'クラウド同期フォルダは未検出です（このPCのローカル設定を使用中）。';
    r.style.color = '#71717A';
    syncEl.appendChild(r);
  }} else {{
    folders.forEach(f => {{
      const row = document.createElement('div');
      row.className = 'app-row';
      const left = document.createElement('div');
      const name = document.createElement('div');
      name.className = 'app-name';
      name.textContent = f.provider;
      const p = document.createElement('div');
      p.className = 'app-path';
      p.textContent = f.suggested_home;
      left.appendChild(name);
      left.appendChild(p);

      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'btn sm';
      btn.textContent = '同期コマンドをコピー';
      btn.addEventListener('click', () => copyCmd('nihongo-mcp init --target all --home "' + f.suggested_home + '"'));
      row.appendChild(left);
      row.appendChild(btn);
      syncEl.appendChild(row);
    }});
  }}

  const skillsWrap = document.getElementById('skills-wrap');
  skillsWrap.textContent = '';
  const previews = state.skills_preview || {{}};
  const defs = [
    ['lite', 'Lite 常駐ルール（nihongo/ALWAYS.md）'],
    ['web', 'Web・スマホ版（nihongo/WEB.md）'],
  ];
  defs.forEach(([k, label]) => {{
    if (!previews[k]) return;
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
    cntEl.className = 'nav-badge' + (pending.length === 0 ? ' zero' : '');
    document.getElementById('btn-approve-all').disabled = pending.length === 0;

    const banner = document.getElementById('pending-banner');
    if (pending.length > 0) {{
      document.getElementById('pending-banner-txt').textContent =
        '承認待ちの候補が ' + pending.length + ' 件あります';
      banner.classList.add('show');
    }} else {{
      banner.classList.remove('show');
    }}

    const listEl = document.getElementById('inbox-list');
    listEl.textContent = '';
    if (pending.length === 0) {{
      const empty = document.createElement('div');
      empty.className = 'empty-box';
      empty.textContent = '承認待ちの候補はありません。普段のチャットで言い回しを直すとここに候補が溜まります。';
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
      empty.textContent = '処理済みの履歴はまだありません。';
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
document.getElementById('btn-goto-inbox').addEventListener('click', () => switchTab('inbox'));
document.getElementById('btn-reload').addEventListener('click', loadState);

document.querySelectorAll('#scene-filter .filter-pill').forEach(pill => {{
  pill.addEventListener('click', () => {{
    ACTIVE_FILTER = pill.dataset.filter || 'all';
    document.querySelectorAll('#scene-filter .filter-pill').forEach(p => p.classList.toggle('active', p === pill));
    if (STATE) renderSceneCards(STATE);
  }});
}});

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
    showToast(res.message || 'profile.md に追加しました。', 'ok');
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
    const msg = res.approved_count + '件を承認して profile.md に反映しました。'
      + (blocked ? '（警告付きの ' + blocked + ' 件は個別に確認してください）' : '');
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
    showToast('profile.md を保存しました。', 'ok');
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
    title.style.fontWeight = '600';
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
