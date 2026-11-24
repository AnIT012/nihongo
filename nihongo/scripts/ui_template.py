"""nihongo 全AI共通ルール管理 UI テンプレート（静かなドキュメント・ワークスペース設計・外部通信ゼロ）。"""
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
<title>nihongo — 私の書き方</title>
<style>
:root {{
  --rail: #F7F8FA;
  --desk: #F3F4F6;
  --surface: #FFFFFF;
  --active-fill: #F3F4F6;
  --hover-fill: #F5F6F8;
  --ink: #111827;
  --body: #1F2937;
  --muted: #6B7280;
  --faint: #9CA3AF;
  --line: #E5E7EB;
  --line-strong: #D1D5DB;
  --rule-dark: #374151;
  --brand-red: #D7261E;
  --accent-bg: #EEF6F5;
  --accent-ink: #276762;
  --warn-bg: #FEF7DC;
  --warn-ink: #854D0E;
  --ok-bg: #ECFDF3;
  --ok-ink: #166534;
}}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
html, body {{ height: 100%; }}
body {{
  background: var(--desk);
  color: var(--ink);
  font-family: -apple-system, BlinkMacSystemFont, "Hiragino Sans", "Hiragino Kaku Gothic ProN", "Yu Gothic UI", "Meiryo", sans-serif;
  font-size: 13.5px;
  line-height: 1.6;
  -webkit-font-smoothing: antialiased;
}}

.app {{
  display: grid;
  grid-template-columns: 54px minmax(0, 1fr);
  min-height: 100vh;
}}

/* Slim Left Icon Rail (TeaMy style) */
.rail {{
  background: var(--rail);
  border-right: 1px solid var(--line);
  padding: 12px 0 14px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: space-between;
  position: sticky;
  top: 0;
  height: 100vh;
  z-index: 30;
}}
.rail-top {{
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  width: 100%;
}}
.rail-mark {{
  width: 34px;
  height: 34px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 6px;
}}
.rail-dot-brand {{
  width: 11px;
  height: 11px;
  border-radius: 50%;
  background: var(--brand-red);
}}
.rail-btn {{
  appearance: none;
  border: 0;
  background: transparent;
  color: var(--muted);
  width: 36px;
  height: 36px;
  border-radius: 8px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  position: relative;
  transition: background 0.12s ease, color 0.12s ease;
}}
.rail-btn:hover {{ background: #EAECEF; color: var(--ink); }}
.rail-btn.active {{ background: #E5E7EB; color: var(--ink); }}
.rail-btn svg {{ width: 18px; height: 18px; }}
.rail-pip {{
  position: absolute;
  top: 6px;
  right: 6px;
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--accent-ink);
  display: none;
}}
.rail-pip.show {{ display: block; }}
.rail-avatar {{
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--accent-bg);
  color: var(--accent-ink);
  font-size: 11px;
  font-weight: 700;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  user-select: none;
}}

/* Workspace Container */
.workspace {{
  min-width: 0;
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}}
.panel {{ display: none; flex: 1; min-height: 100vh; }}
.panel.active {{ display: flex; }}

/* Floating Subtle Toast */
.toast {{
  position: fixed;
  bottom: 18px;
  right: 22px;
  z-index: 60;
  display: none;
  padding: 9px 14px;
  border-radius: 8px;
  font-size: 12.5px;
  font-weight: 500;
  border: 1px solid var(--line-strong);
  background: var(--surface);
  color: var(--ink);
  box-shadow: 0 4px 16px rgba(17, 24, 39, 0.08);
}}
.toast.show {{ display: block; }}
.toast.ok {{ border-color: #BBF7D0; background: var(--ok-bg); color: var(--ok-ink); }}
.toast.error {{ border-color: #FECACA; background: #FEF2F2; color: #991B1B; }}

/* 1. Split-Pane Layout for Personal Rules (TeaMy Signature) */
.split-pane {{
  display: grid;
  grid-template-columns: 316px minmax(0, 1fr);
  width: 100%;
  min-height: 100vh;
}}
.left-pane {{
  background: var(--surface);
  border-right: 1px solid var(--line);
  display: flex;
  flex-direction: column;
  height: 100vh;
  position: sticky;
  top: 0;
}}
.pane-head {{
  height: 48px;
  padding: 0 16px;
  border-bottom: 1px solid var(--line);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  flex-shrink: 0;
}}
.pane-head-left {{
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}}
.brand-word {{
  font-family: ui-sans-serif, system-ui, sans-serif;
  font-weight: 800;
  font-size: 15px;
  letter-spacing: -0.025em;
  color: var(--ink);
}}
.brand-word i {{
  display: inline-block;
  width: 0.44em;
  height: 0.44em;
  border-radius: 50%;
  background: var(--brand-red);
  margin: 0 0.04em;
}}
.mode-tag {{
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  border-radius: 5px;
  font-size: 11px;
  font-weight: 600;
  background: var(--accent-bg);
  color: var(--accent-ink);
}}
.quiet-meta {{
  font-size: 11.5px;
  color: var(--muted);
}}

.left-scroll {{
  flex: 1;
  overflow-y: auto;
  padding: 14px 14px 18px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}}
.left-note {{
  font-size: 12.5px;
  color: var(--body);
  line-height: 1.65;
  padding: 2px 2px 6px;
}}

/* TeaMy-style Artifact Selector Cards */
.doc-card {{
  appearance: none;
  width: 100%;
  text-align: left;
  font: inherit;
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: 10px;
  padding: 11px 12px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  cursor: pointer;
  transition: background 0.12s ease, border-color 0.12s ease;
}}
.doc-card:hover {{ background: var(--hover-fill); }}
.doc-card.active {{
  background: var(--active-fill);
  border-color: var(--line);
}}
.doc-card-left {{
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}}
.doc-ico {{
  width: 30px;
  height: 30px;
  border-radius: 7px;
  background: var(--surface);
  border: 1px solid var(--line);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: var(--muted);
  flex-shrink: 0;
}}
.doc-card.active .doc-ico {{ background: var(--surface); color: var(--ink); }}
.doc-ico svg {{ width: 15px; height: 15px; }}
.doc-title {{
  font-size: 13px;
  font-weight: 600;
  color: var(--ink);
  line-height: 1.35;
}}
.doc-sub {{
  font-size: 11.5px;
  color: var(--muted);
  margin-top: 1px;
}}
.doc-state {{
  font-size: 11px;
  color: var(--muted);
  flex-shrink: 0;
}}

/* Bottom Pinned Composer (TeaMy "+ 直したい所を書く ↑") */
.composer-wrap {{
  padding: 10px 14px 14px;
  border-top: 1px solid var(--line);
  background: var(--surface);
  flex-shrink: 0;
}}
.composer-opts {{
  display: flex;
  gap: 6px;
  margin-bottom: 7px;
}}
.mini-select {{
  font: inherit;
  font-size: 11.5px;
  color: var(--body);
  background: var(--rail);
  border: 1px solid var(--line);
  border-radius: 6px;
  padding: 3px 7px;
  cursor: pointer;
}}
.mini-select:focus {{ outline: none; border-color: var(--line-strong); }}
.composer-box {{
  display: flex;
  align-items: center;
  gap: 8px;
  border: 1px solid var(--line);
  border-radius: 10px;
  padding: 6px 8px 6px 11px;
  background: var(--surface);
}}
.composer-box:focus-within {{ border-color: var(--line-strong); }}
.composer-plus {{
  color: var(--muted);
  font-size: 16px;
  line-height: 1;
  user-select: none;
}}
.composer-input {{
  flex: 1;
  min-width: 0;
  border: 0;
  background: transparent;
  font: inherit;
  font-size: 13px;
  color: var(--ink);
  outline: none;
}}
.composer-input::placeholder {{ color: var(--faint); }}
.composer-send {{
  appearance: none;
  border: 0;
  width: 26px;
  height: 26px;
  border-radius: 7px;
  background: var(--active-fill);
  color: var(--muted);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  flex-shrink: 0;
  transition: background 0.12s ease, color 0.12s ease;
}}
.composer-send:hover, .composer-send.ready {{
  background: var(--ink);
  color: #FFFFFF;
}}

/* Right Document Pane (TeaMy Artifact Viewer) */
.right-pane {{
  display: flex;
  flex-direction: column;
  min-width: 0;
  background: var(--desk);
}}
.doc-toolbar {{
  height: 48px;
  background: var(--surface);
  border-bottom: 1px solid var(--line);
  padding: 0 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  position: sticky;
  top: 0;
  z-index: 20;
}}
.tb-left {{
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}}
.tb-title {{
  font-size: 13px;
  font-weight: 600;
  color: var(--ink);
  display: inline-flex;
  align-items: center;
  gap: 7px;
  white-space: nowrap;
}}
.tb-title svg {{ width: 15px; height: 15px; color: var(--muted); }}
.tb-pill {{
  font-size: 11.5px;
  color: var(--muted);
  background: var(--rail);
  border: 1px solid var(--line);
  border-radius: 6px;
  padding: 2px 8px;
  white-space: nowrap;
}}
.seg {{
  display: inline-flex;
  background: var(--rail);
  border: 1px solid var(--line);
  border-radius: 7px;
  padding: 2px;
  gap: 2px;
}}
.seg-btn {{
  appearance: none;
  border: 0;
  background: transparent;
  color: var(--muted);
  font: inherit;
  font-size: 12px;
  font-weight: 500;
  padding: 3px 10px;
  border-radius: 5px;
  cursor: pointer;
}}
.seg-btn.active {{
  background: var(--surface);
  color: var(--ink);
  font-weight: 600;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}}

.tb-right {{
  display: flex;
  align-items: center;
  gap: 4px;
}}
.ico-btn {{
  appearance: none;
  border: 0;
  background: transparent;
  color: var(--muted);
  width: 30px;
  height: 30px;
  border-radius: 6px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}}
.ico-btn:hover {{ background: var(--hover-fill); color: var(--ink); }}
.ico-btn svg {{ width: 15px; height: 15px; }}

/* Quiet Buttons */
.btn {{
  appearance: none;
  border: 1px solid var(--line-strong);
  background: var(--surface);
  color: var(--ink);
  font: inherit;
  font-size: 12.5px;
  font-weight: 500;
  padding: 5px 11px;
  border-radius: 7px;
  cursor: pointer;
  white-space: nowrap;
  transition: background 0.12s ease, border-color 0.12s ease;
}}
.btn:hover {{ background: var(--hover-fill); }}
.btn.solid {{
  background: var(--ink);
  border-color: var(--ink);
  color: #FFFFFF;
  font-weight: 600;
}}
.btn.solid:hover {{ background: #27272A; }}
.btn.text-only {{
  border-color: transparent;
  background: transparent;
  color: var(--muted);
  padding: 4px 8px;
}}
.btn.text-only:hover {{ color: var(--ink); background: var(--hover-fill); }}
.btn.sm {{ padding: 4px 9px; font-size: 12px; }}
.btn:disabled {{ opacity: 0.4; cursor: not-allowed; }}

/* Desk Area + White A4-like Sheet + Optional Right Margin Cards */
.desk-scroll {{
  flex: 1;
  padding: 24px 28px 56px;
  overflow-y: auto;
}}
.sheet-stage {{
  display: flex;
  align-items: flex-start;
  justify-content: center;
  gap: 18px;
  max-width: 1060px;
  margin: 0 auto;
}}
.paper-sheet {{
  flex: 1;
  max-width: 760px;
  min-width: 0;
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: 3px;
  padding: 36px 44px 44px;
  box-shadow: 0 1px 3px rgba(17, 24, 39, 0.04);
}}
.paper-meta-top {{
  display: flex;
  justify-content: flex-end;
  gap: 14px;
  font-size: 11.5px;
  color: var(--muted);
  margin-bottom: 18px;
}}
.paper-title {{
  text-align: center;
  font-size: 20px;
  font-weight: 700;
  color: var(--ink);
  letter-spacing: 0.01em;
  margin-bottom: 28px;
}}
.paper-sec {{
  margin-bottom: 26px;
}}
.paper-sec:last-child {{ margin-bottom: 0; }}
.paper-sec-h {{
  font-size: 14px;
  font-weight: 700;
  color: var(--ink);
  margin-bottom: 10px;
  display: flex;
  align-items: baseline;
  gap: 8px;
}}
.paper-sec-sub {{
  font-size: 11.5px;
  font-weight: 400;
  color: var(--muted);
}}

/* TeaMy Horizontal-Rule-Only Table */
table.doc-table {{
  width: 100%;
  border-collapse: collapse;
  border-top: 1.5px solid var(--rule-dark);
  border-bottom: 1.5px solid var(--rule-dark);
  font-size: 13.5px;
}}
table.doc-table thead th {{
  background: #F4F5F7;
  color: var(--ink);
  font-size: 12px;
  font-weight: 600;
  text-align: left;
  padding: 8px 12px;
  border-bottom: 1px solid var(--line-strong);
  white-space: nowrap;
}}
table.doc-table tbody td {{
  padding: 10px 12px;
  border-bottom: 1px solid var(--line);
  color: var(--body);
  vertical-align: middle;
}}
table.doc-table tbody tr:last-child td {{ border-bottom: 0; }}
table.doc-table tbody tr:hover td {{ background: #FAFBFD; }}
.td-strong {{ font-weight: 500; color: var(--ink); }}
.td-muted {{ font-size: 12px; color: var(--muted); }}
.td-act {{ text-align: right; white-space: nowrap; }}
.link-del {{
  appearance: none;
  border: 0;
  background: transparent;
  color: var(--faint);
  font: inherit;
  font-size: 12px;
  cursor: pointer;
  padding: 2px 5px;
  border-radius: 4px;
}}
.link-del:hover {{ color: #991B1B; background: #FEF2F2; }}
.proj-mark {{
  font-size: 11px;
  color: var(--muted);
  background: var(--rail);
  border: 1px solid var(--line);
  padding: 1px 6px;
  border-radius: 4px;
  margin-left: 6px;
}}

/* Right Margin Review Cards (TeaMy Frame 2 "審査結果" Margin Column!) */
.margin-col {{
  width: 248px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
}}
.margin-head {{
  font-size: 11.5px;
  font-weight: 600;
  color: var(--muted);
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 2px 2px 4px;
}}
.review-card {{
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: 10px;
  padding: 12px 13px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}}
.review-card.warn {{
  border-color: #FDE68A;
}}
.rc-meta {{
  font-size: 11.5px;
  color: var(--muted);
  display: flex;
  align-items: center;
  gap: 6px;
}}
.rc-meta strong {{ color: var(--ink); font-weight: 600; }}
.rc-val {{
  font-size: 13px;
  font-weight: 600;
  color: var(--ink);
  word-break: break-word;
}}
.rc-reason {{
  font-size: 12px;
  color: var(--muted);
  line-height: 1.5;
}}
.rc-warn {{
  font-size: 11.5px;
  color: var(--warn-ink);
  background: var(--warn-bg);
  padding: 4px 7px;
  border-radius: 5px;
  line-height: 1.5;
}}
.rc-actions {{
  display: flex;
  justify-content: flex-end;
  gap: 6px;
  margin-top: 2px;
}}

/* Single-Column Document Panels (Inbox / Connect / Check) */
.doc-page {{
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  background: var(--desk);
}}
.paper-sheet.wide {{
  max-width: 820px;
  margin: 0 auto;
  width: 100%;
}}

/* Inputs & Textareas */
input[type="text"], select, textarea {{
  width: 100%;
  font: inherit;
  font-size: 13px;
  padding: 7px 10px;
  border: 1px solid var(--line-strong);
  border-radius: 7px;
  background: var(--surface);
  color: var(--ink);
}}
input[type="text"]:focus, select:focus, textarea:focus {{
  outline: none;
  border-color: var(--ink);
}}
textarea.mono {{
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 12.5px;
  line-height: 1.7;
  min-height: 360px;
  border: 1px solid var(--line);
  border-radius: 6px;
  padding: 14px 16px;
  resize: vertical;
  background: #FAFAFB;
}}
.grid-2 {{
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
  margin-bottom: 14px;
}}
label.fld {{
  display: block;
  font-size: 12px;
  font-weight: 600;
  color: var(--muted);
  margin-bottom: 5px;
}}
.form-drawer {{
  display: none;
  margin-bottom: 20px;
  padding: 14px 16px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--rail);
}}
.form-drawer.open {{ display: block; }}

.warn-hl {{
  background: var(--warn-bg);
  color: var(--warn-ink);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 12px;
  display: inline-block;
  margin-top: 5px;
}}
.force-check {{
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--body);
  margin-top: 6px;
}}

.findings-box {{
  margin-top: 18px;
  border-top: 1.5px solid var(--rule-dark);
  border-bottom: 1.5px solid var(--rule-dark);
  padding: 14px 4px;
}}
.findings-box.has-issue {{
  background: #FFFDF7;
  padding: 14px 14px;
}}
.findings-box ul {{ margin-top: 8px; padding-left: 18px; }}
.findings-box li {{ margin: 4px 0; font-size: 13px; }}

details.skill-box {{
  border-bottom: 1px solid var(--line);
  padding: 10px 0;
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
  background: var(--rail);
  border-radius: 6px;
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 12px;
  line-height: 1.65;
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 240px;
  overflow-y: auto;
}}

@media (max-width: 1180px) {{
  .sheet-stage {{ flex-direction: column; align-items: stretch; }}
  .paper-sheet {{ max-width: none; }}
  .margin-col {{ width: 100%; }}
}}
@media (max-width: 860px) {{
  .app {{ grid-template-columns: 1fr; }}
  .rail {{
    position: static;
    height: auto;
    flex-direction: row;
    padding: 8px 14px;
    border-right: 0;
    border-bottom: 1px solid var(--line);
  }}
  .rail-top {{ flex-direction: row; width: auto; gap: 6px; }}
  .rail-mark {{ margin-bottom: 0; }}
  .split-pane {{ grid-template-columns: 1fr; }}
  .left-pane {{ position: static; height: auto; border-right: 0; border-bottom: 1px solid var(--line); }}
  .desk-scroll {{ padding: 16px 14px 48px; }}
  .paper-sheet {{ padding: 22px 18px 28px; }}
  .grid-2 {{ grid-template-columns: 1fr; }}
  .doc-toolbar {{ padding: 0 12px; }}
}}
</style>
</head>
<body>
<div class="app">
  <!-- Slim Left Icon Rail -->
  <aside class="rail" aria-label="ナビゲーション">
    <div class="rail-top">
      <div class="rail-mark" title="nihongo"><span class="rail-dot-brand"></span></div>
      <button class="rail-btn active" data-tab="profile" type="button" title="自分のルール（profile.md）">
        <svg viewBox="0 0 18 18" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M4.5 2.5H11L14 5.5V15.5H4.5V2.5Z"/><path d="M11 2.5V5.5H14"/><line x1="7" y1="9" x2="11.5" y2="9"/><line x1="7" y1="12" x2="10" y2="12"/></svg>
      </button>
      <button class="rail-btn" data-tab="inbox" type="button" title="承認待ち（受信箱）">
        <svg viewBox="0 0 18 18" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="9" cy="9" r="6.5"/><path d="M9 5.5V9.2L11.5 10.7"/></svg>
        <span class="rail-pip" id="rail-pip"></span>
      </button>
      <button class="rail-btn" data-tab="connect" type="button" title="AI接続・同期">
        <svg viewBox="0 0 18 18" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M7.3 10.7L10.7 7.3"/><path d="M10.1 12.2L8.3 14A3 3 0 1 1 4 9.7L5.8 7.9"/><path d="M7.9 5.8L9.7 4A3 3 0 1 1 14 8.3L12.2 10.1"/></svg>
      </button>
      <button class="rail-btn" data-tab="check" type="button" title="動作テスト（0トークン検査）">
        <svg viewBox="0 0 18 18" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M9 2.3L14.5 4.5V8.7C14.5 12.2 12.2 14.7 9 15.7C5.8 14.7 3.5 12.2 3.5 8.7V4.5L9 2.3Z"/><path d="M6.5 9.2L8.2 10.9L11.7 7.4"/></svg>
      </button>
    </div>
    <div class="rail-avatar" id="rail-status" title="ローカル稼働中（127.0.0.1・外部送信なし）">地</div>
  </aside>

  <div class="workspace">
    <div class="toast" id="toast" role="status" aria-live="polite"></div>

    <!-- 1. Personal Rules Split-Pane Workspace (DEFAULT) -->
    <section class="panel active" id="panel-profile">
      <div class="split-pane">
        <!-- Left Pane: Scene Selector Cards + Bottom Composer -->
        <div class="left-pane">
          <div class="pane-head">
            <div class="pane-head-left">
              <span class="brand-word">nih<i></i>ngo</span>
              <span class="mode-tag">個人ルール</span>
            </div>
            <span class="quiet-meta" id="left-layer-badge">ローカル</span>
          </div>

          <div class="left-scroll">
            <div class="left-note">全AIが共通で参照する書き方です。場面を選ぶと右のページで中身を確認できます。</div>
            <div id="scene-nav-cards" style="display:flex;flex-direction:column;gap:8px;"></div>
          </div>

          <!-- TeaMy-style Pinned Bottom Composer -->
          <div class="composer-wrap">
            <div class="composer-opts">
              <select class="mini-select" id="qa-scene" aria-label="場面">
                <option value="common">共通</option>
                <option value="work">社内・同僚</option>
                <option value="formal">社外・目上</option>
                <option value="casual">普段・雑談</option>
              </select>
              <select class="mini-select" id="qa-kind" aria-label="種類">
                <option value="forbidden">避ける表現</option>
                <option value="rule">書く時の考え方</option>
                <option value="tone">口調・記号</option>
                <option value="first_person">一人称</option>
              </select>
            </div>
            <div class="composer-box">
              <span class="composer-plus">+</span>
              <input class="composer-input" type="text" id="qa-value" placeholder="避ける表現やルールを追加">
              <button class="composer-send" id="btn-qa-add" type="button" title="追加">
                <svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M8 12.5V3.5"/><path d="M4.2 7.2L8 3.5L11.8 7.2"/></svg>
              </button>
            </div>
          </div>
        </div>

        <!-- Right Pane: Crisp Document Sheet + Optional Right Margin Approval Cards -->
        <div class="right-pane">
          <div class="doc-toolbar">
            <div class="tb-left">
              <span class="tb-title">
                <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M4 2H10L13 5V14H4V2Z"/><path d="M10 2V5H13"/></svg>
                <span id="doc-tb-title">私の書き方</span>
              </span>
              <span class="tb-pill" id="doc-tb-count">0件</span>
              <div class="seg" role="tablist" aria-label="表示切替">
                <button class="seg-btn active" id="mode-cards" type="button">ページ</button>
                <button class="seg-btn" id="mode-raw" type="button">Markdown</button>
              </div>
            </div>
            <div class="tb-right">
              <button class="btn solid sm" id="btn-save-profile" type="button" style="display:none;">保存</button>
              <button class="ico-btn" id="btn-tb-export" type="button" title="AI接続・持ち運びを開く">
                <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M8 2.5V10"/><path d="M5 7L8 10L11 7"/><path d="M3 12.5H13"/></svg>
              </button>
              <button class="ico-btn" id="btn-reload" type="button" title="再読み込み">
                <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M13 8A5 5 0 1 1 11.5 4.5"/><path d="M11.5 2V4.8H8.7"/></svg>
              </button>
            </div>
          </div>

          <div class="desk-scroll">
            <div class="sheet-stage">
              <div class="paper-sheet" id="view-cards">
                <div class="paper-meta-top">
                  <span id="sheet-first-person"></span>
                  <span id="sheet-layer-note">profile.md</span>
                </div>
                <h1 class="paper-title" id="sheet-title">私の書き方</h1>
                <div id="sheet-body"></div>
              </div>

              <div class="paper-sheet" id="view-raw" style="display:none;">
                <div class="paper-meta-top">
                  <span id="editor-path">profile.md</span>
                </div>
                <textarea class="mono" id="profile-editor" spellcheck="false"></textarea>
                <div id="project-raw-card" style="display:none;margin-top:22px;">
                  <div class="paper-sec-h">案件別ルール<span class="paper-sec-sub" id="project-raw-path">読み取り専用</span></div>
                  <textarea class="mono" id="project-raw-editor" readonly style="min-height:140px;"></textarea>
                </div>
              </div>

              <!-- Right Margin Approval Cards (TeaMy Frame 2 style!) -->
              <aside class="margin-col" id="margin-inbox-col" style="display:none;">
                <div class="margin-head">
                  <span id="margin-inbox-title">承認待ち</span>
                  <button class="btn text-only sm" id="btn-open-inbox-all" type="button">すべて見る</button>
                </div>
                <div id="margin-inbox-list" style="display:flex;flex-direction:column;gap:10px;"></div>
              </aside>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- 2. Pending Inbox Panel -->
    <section class="panel" id="panel-inbox">
      <div class="doc-page">
        <div class="doc-toolbar">
          <div class="tb-left">
            <span class="tb-title">承認待ち（受信箱）</span>
            <span class="tb-pill" id="pending-count">0</span>
          </div>
          <div class="tb-right" style="gap:6px;">
            <button class="btn sm" id="btn-toggle-add" type="button">＋ 追加</button>
            <button class="btn solid sm" id="btn-approve-all" type="button">警告なしを一括承認</button>
            <button class="btn text-only sm" id="btn-toggle-history" type="button">履歴</button>
          </div>
        </div>

        <div class="desk-scroll">
          <div class="paper-sheet wide">
            <div class="form-drawer" id="add-form-box">
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
                <button class="btn solid sm" id="btn-propose" type="button">受信箱に追加</button>
                <button class="btn text-only sm" id="btn-cancel-add" type="button">閉じる</button>
              </div>
            </div>

            <div class="paper-sec">
              <div class="paper-sec-h">承認待ちの候補</div>
              <table class="doc-table">
                <thead>
                  <tr>
                    <th style="width:104px;">場面</th>
                    <th style="width:110px;">種別</th>
                    <th>内容・理由</th>
                    <th style="width:128px;text-align:right;">操作</th>
                  </tr>
                </thead>
                <tbody id="inbox-list"></tbody>
              </table>
            </div>

            <div class="paper-sec" id="history-wrap" style="display:none;">
              <div class="paper-sec-h">処理済みの履歴</div>
              <table class="doc-table">
                <thead>
                  <tr>
                    <th style="width:104px;">場面</th>
                    <th style="width:90px;">結果</th>
                    <th>内容</th>
                    <th style="width:110px;">経由</th>
                  </tr>
                </thead>
                <tbody id="history-list"></tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- 3. Connect & Sync Panel -->
    <section class="panel" id="panel-connect">
      <div class="doc-page">
        <div class="doc-toolbar">
          <div class="tb-left">
            <span class="tb-title">AI接続・同期</span>
          </div>
        </div>

        <div class="desk-scroll">
          <div class="paper-sheet wide">
            <div class="paper-sec">
              <div class="paper-sec-h">AIアプリ（MCP）</div>
              <table class="doc-table">
                <thead>
                  <tr>
                    <th>アプリ</th>
                    <th style="width:100px;">状態</th>
                    <th style="width:160px;text-align:right;">設定</th>
                  </tr>
                </thead>
                <tbody id="mcp-list"></tbody>
              </table>
            </div>

            <div class="paper-sec">
              <div class="paper-sec-h">同期フォルダ</div>
              <table class="doc-table">
                <thead>
                  <tr>
                    <th>サービス</th>
                    <th style="width:170px;text-align:right;">設定</th>
                  </tr>
                </thead>
                <tbody id="sync-list-card"></tbody>
              </table>
            </div>

            <div class="paper-sec">
              <div class="paper-sec-h">他端末へ持ち運ぶ<span class="paper-sec-sub">nihongo-setup.md</span></div>
              <div style="display:grid;grid-template-columns:1fr 1fr auto;gap:10px;align-items:end;">
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
                <button class="btn solid" id="btn-export-dl" type="button">ダウンロード</button>
              </div>
              <details style="margin-top:12px;">
                <summary style="cursor:pointer;font-size:12px;color:var(--muted);">中身を確認</summary>
                <textarea class="mono" id="export-preview" readonly style="margin-top:8px;min-height:170px;"></textarea>
              </details>
            </div>

            <div class="paper-sec" id="skills-section">
              <div class="paper-sec-h">組み込みルール</div>
              <div id="skills-wrap"></div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- 4. Utility: 0-Token Check Panel -->
    <section class="panel" id="panel-check">
      <div class="doc-page">
        <div class="doc-toolbar">
          <div class="tb-left">
            <span class="tb-title">動作テスト（0トークン検査）</span>
          </div>
          <div class="tb-right" style="gap:8px;">
            <select id="check-scene" style="width:auto;padding:4px 8px;font-size:12px;">
              <option value="">場面指定なし</option>
              <option value="formal">社外・目上</option>
              <option value="work">社内・同僚</option>
              <option value="casual">普段・雑談</option>
            </select>
            <button class="btn solid sm" id="btn-run-check" type="button">検査する</button>
          </div>
        </div>

        <div class="desk-scroll">
          <div class="paper-sheet wide">
            <div class="grid-2">
              <div>
                <label class="fld" for="check-orig">元の文章（新規なら空欄）</label>
                <textarea id="check-orig" rows="7" placeholder="例：資料は明日15時までに必ず送ってください。"></textarea>
              </div>
              <div>
                <label class="fld" for="check-draft">AIの文章</label>
                <textarea id="check-draft" rows="7" placeholder="例：恐れ入りますが、資料は明日15時頃までにご送付いただけますと幸いです。"></textarea>
              </div>
            </div>
            <div id="check-result"></div>
          </div>
        </div>
      </div>
    </section>
  </div>
</div>

<script>
const CSRF = {token_json};
let STATE = null;
let SELECTED_SCENE = 'all';

const SCENE_DEFS = [
  {{ key: 'all', title: 'すべてのルール', sub: '4場面まとめ' }},
  {{ key: 'common', title: '共通ルール', sub: '全場面で適用' }},
  {{ key: 'work', title: '社内・同僚', sub: 'Slack・PR' }},
  {{ key: 'formal', title: '社外・目上', sub: '社外メール・公式' }},
  {{ key: 'casual', title: '普段・雑談', sub: '友達・メモ' }},
];
const SCENE_LABELS = {{ common: '共通', work: '社内・同僚', formal: '社外・目上', casual: '普段・雑談' }};
const SCENE_KEYS = ['common', 'work', 'formal', 'casual'];

let toastTimer = null;
function showToast(msg, kind) {{
  const el = document.getElementById('toast');
  el.textContent = msg;
  el.className = 'toast show ' + (kind || '');
  if (toastTimer) clearTimeout(toastTimer);
  if (kind !== 'error') {{
    toastTimer = setTimeout(() => {{ el.className = 'toast'; }}, 4000);
  }}
}}

function switchTab(tabKey) {{
  document.querySelectorAll('.rail-btn').forEach(b => b.classList.toggle('active', b.dataset.tab === tabKey));
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
    showToast('コピーしました', 'ok');
  }} catch (_) {{
    const ta = document.createElement('textarea');
    ta.value = text;
    document.body.appendChild(ta);
    ta.select();
    document.execCommand('copy');
    ta.remove();
    showToast('コピーしました', 'ok');
  }}
}}

function collectSceneItems(state, sc) {{
  const g = (state.structured_global || {{}})[sc] || {{ first_person: '', forbidden: [], rules: [] }};
  const p = state.structured_project ? (state.structured_project[sc] || {{ forbidden: [], rules: [] }}) : {{ forbidden: [], rules: [] }};
  const items = [];
  (g.forbidden || []).forEach(w => items.push({{ scene: sc, kind: 'forbidden', kindLabel: '避ける表現', value: w, source: 'global' }}));
  (p.forbidden || []).forEach(w => {{
    if (!(g.forbidden || []).includes(w)) items.push({{ scene: sc, kind: 'forbidden', kindLabel: '避ける表現', value: w, source: 'project' }});
  }});
  (g.rules || []).forEach(r => items.push({{ scene: sc, kind: 'rule', kindLabel: sc === 'common' ? '基本方針' : '口調・ルール', value: r, source: 'global' }}));
  (p.rules || []).forEach(r => items.push({{ scene: sc, kind: 'rule', kindLabel: sc === 'common' ? '基本方針' : '口調・ルール', value: r, source: 'project' }}));
  return items;
}}

function renderLeftNavCards(state) {{
  const wrap = document.getElementById('scene-nav-cards');
  wrap.textContent = '';
  const allItems = SCENE_KEYS.flatMap(k => collectSceneItems(state, k));

  SCENE_DEFS.forEach(def => {{
    const list = def.key === 'all' ? allItems : collectSceneItems(state, def.key);
    const ngCnt = list.filter(x => x.kind === 'forbidden').length;
    const rCnt = list.filter(x => x.kind !== 'forbidden').length;

    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'doc-card' + (SELECTED_SCENE === def.key ? ' active' : '');

    const left = document.createElement('div');
    left.className = 'doc-card-left';
    const ico = document.createElement('span');
    ico.className = 'doc-ico';
    const ns = 'http://www.w3.org/2000/svg';
    const svg = document.createElementNS(ns, 'svg');
    svg.setAttribute('viewBox', '0 0 16 16');
    svg.setAttribute('fill', 'none');
    svg.setAttribute('stroke', 'currentColor');
    svg.setAttribute('stroke-width', '1.4');
    svg.setAttribute('stroke-linecap', 'round');
    svg.setAttribute('stroke-linejoin', 'round');
    const p1 = document.createElementNS(ns, 'path');
    p1.setAttribute('d', 'M4 2.2H9.8L12.5 4.9V13.8H4V2.2Z');
    const p2 = document.createElementNS(ns, 'path');
    p2.setAttribute('d', 'M9.8 2.2V4.9H12.5');
    svg.appendChild(p1);
    svg.appendChild(p2);
    ico.appendChild(svg);
    const txt = document.createElement('div');
    const title = document.createElement('div');
    title.className = 'doc-title';
    title.textContent = def.title;
    const sub = document.createElement('div');
    sub.className = 'doc-sub';
    sub.textContent = def.sub + ' · ' + (ngCnt + rCnt) + '件';
    txt.appendChild(title);
    txt.appendChild(sub);
    left.appendChild(ico);
    left.appendChild(txt);
    btn.appendChild(left);

    if (SELECTED_SCENE === def.key) {{
      const st = document.createElement('span');
      st.className = 'doc-state';
      st.textContent = '表示中';
      btn.appendChild(st);
    }}

    btn.addEventListener('click', () => {{
      SELECTED_SCENE = def.key;
      if (def.key !== 'all') document.getElementById('qa-scene').value = def.key;
      renderLeftNavCards(STATE);
      renderDocumentSheet(STATE);
    }});
    wrap.appendChild(btn);
  }});
}}

function renderDocumentSheet(state) {{
  const allItems = SCENE_KEYS.flatMap(k => collectSceneItems(state, k));
  const items = SELECTED_SCENE === 'all' ? allItems : collectSceneItems(state, SELECTED_SCENE);
  const def = SCENE_DEFS.find(d => d.key === SELECTED_SCENE) || SCENE_DEFS[0];

  document.getElementById('doc-tb-title').textContent = SELECTED_SCENE === 'all' ? '私の書き方' : def.title;
  document.getElementById('doc-tb-count').textContent = items.length + '件';
  document.getElementById('sheet-title').textContent = SELECTED_SCENE === 'all' ? '私の書き方' : def.title;

  const fp = ((state.structured_global || {{}}).common || {{}}).first_person || '';
  document.getElementById('sheet-first-person').textContent = fp ? ('一人称：' + fp) : '';
  document.getElementById('sheet-layer-note').textContent = state.profile.project_profile_path ? 'profile.md ＋ 案件別' : 'profile.md';
  document.getElementById('left-layer-badge').textContent = state.profile.project_profile_path ? '2層適用中' : 'ローカル';

  const body = document.getElementById('sheet-body');
  body.textContent = '';

  const ngItems = items.filter(x => x.kind === 'forbidden');
  const ruleItems = items.filter(x => x.kind !== 'forbidden');

  const buildTableSection = (heading, subText, rows, showDelete) => {{
    const sec = document.createElement('div');
    sec.className = 'paper-sec';
    const h = document.createElement('div');
    h.className = 'paper-sec-h';
    h.textContent = heading;
    if (subText) {{
      const sp = document.createElement('span');
      sp.className = 'paper-sec-sub';
      sp.textContent = subText;
      h.appendChild(sp);
    }}
    sec.appendChild(h);

    const tbl = document.createElement('table');
    tbl.className = 'doc-table';
    const thead = document.createElement('thead');
    const htr = document.createElement('tr');
    const cols = SELECTED_SCENE === 'all' ? ['場面', '内容', ''] : ['内容', ''];
    cols.forEach((c, i) => {{
      const th = document.createElement('th');
      if (SELECTED_SCENE === 'all' && i === 0) th.style.width = '104px';
      if (i === cols.length - 1) th.style.width = '68px';
      th.textContent = c;
      htr.appendChild(th);
    }});
    thead.appendChild(htr);
    tbl.appendChild(thead);

    const tbody = document.createElement('tbody');
    if (rows.length === 0) {{
      const tr = document.createElement('tr');
      const td = document.createElement('td');
      td.colSpan = cols.length;
      td.className = 'td-muted';
      td.textContent = '登録なし';
      tr.appendChild(td);
      tbody.appendChild(tr);
    }} else {{
      rows.forEach(row => {{
        const tr = document.createElement('tr');
        tr.className = 'rule-row' + (row.source === 'project' ? ' project-row' : '');
        if (SELECTED_SCENE === 'all') {{
          const tdSc = document.createElement('td');
          tdSc.className = 'td-muted';
          tdSc.textContent = SCENE_LABELS[row.scene] || row.scene;
          tr.appendChild(tdSc);
        }}
        const tdVal = document.createElement('td');
        tdVal.className = 'td-strong';
        tdVal.textContent = row.kind === 'forbidden' ? ('「' + row.value + '」') : row.value;
        if (row.source === 'project') {{
          const pm = document.createElement('span');
          pm.className = 'proj-mark';
          pm.textContent = '案件';
          tdVal.appendChild(pm);
        }}
        tr.appendChild(tdVal);

        const tdAct = document.createElement('td');
        tdAct.className = 'td-act';
        if (showDelete && row.source === 'global') {{
          const btn = document.createElement('button');
          btn.type = 'button';
          btn.className = 'link-del btn-del-ng';
          btn.textContent = '削除';
          btn.addEventListener('click', async () => {{
            try {{
              await apiPost('/api/profile/remove-forbidden', {{ scene: row.scene, value: row.value }});
              showToast('「' + row.value + '」を削除しました', 'ok');
              await loadState();
            }} catch (err) {{
              showToast('削除できませんでした: ' + err.message, 'error');
            }}
          }});
          tdAct.appendChild(btn);
        }}
        tr.appendChild(tdAct);
        tbody.appendChild(tr);
      }});
    }}
    tbl.appendChild(tbody);
    sec.appendChild(tbl);
    return sec;
  }};

  body.appendChild(buildTableSection('1. 避ける表現', '0トークン検査で自動検出', ngItems, true));
  body.appendChild(buildTableSection('2. 書く時の考え方・口調', '', ruleItems, false));
}}

function renderMarginInbox(state) {{
  const pending = state.pending_inbox || [];
  const col = document.getElementById('margin-inbox-col');
  const list = document.getElementById('margin-inbox-list');
  list.textContent = '';

  if (pending.length === 0) {{
    col.style.display = 'none';
    return;
  }}
  col.style.display = 'flex';
  document.getElementById('margin-inbox-title').textContent = '承認待ち · ' + pending.length + '件';

  pending.slice(0, 3).forEach(item => {{
    const card = document.createElement('div');
    card.className = 'review-card' + (item.warning ? ' warn' : '');

    const meta = document.createElement('div');
    meta.className = 'rc-meta';
    const strong = document.createElement('strong');
    strong.textContent = item.scene_label || item.scene;
    meta.appendChild(strong);
    meta.appendChild(document.createTextNode(item.kind_label || item.kind));
    card.appendChild(meta);

    const val = document.createElement('div');
    val.className = 'rc-val';
    val.textContent = item.value || '';
    card.appendChild(val);

    if (item.reason) {{
      const r = document.createElement('div');
      r.className = 'rc-reason';
      r.textContent = item.reason;
      card.appendChild(r);
    }}
    if (item.warning) {{
      const w = document.createElement('div');
      w.className = 'rc-warn';
      w.textContent = '場面ガード警告あり（承認待ちタブで確認）';
      card.appendChild(w);
    }}

    const acts = document.createElement('div');
    acts.className = 'rc-actions';
    if (!item.warning) {{
      const bOk = document.createElement('button');
      bOk.type = 'button';
      bOk.className = 'btn sm';
      bOk.textContent = '承認';
      bOk.addEventListener('click', async () => {{
        try {{
          await apiPost('/api/inbox/approve', {{ ids: [item.id], force: false }});
          showToast('承認して反映しました', 'ok');
          await loadState();
        }} catch (err) {{
          showToast(err.message, 'error');
        }}
      }});
      acts.appendChild(bOk);
    }} else {{
      const bSee = document.createElement('button');
      bSee.type = 'button';
      bSee.className = 'btn sm';
      bSee.textContent = '確認する';
      bSee.addEventListener('click', () => switchTab('inbox'));
      acts.appendChild(bSee);
    }}
    const bRej = document.createElement('button');
    bRej.type = 'button';
    bRej.className = 'btn text-only sm';
    bRej.textContent = '却下';
    bRej.addEventListener('click', async () => {{
      try {{
        await apiPost('/api/inbox/reject', {{ ids: [item.id] }});
        showToast('却下しました', 'ok');
        await loadState();
      }} catch (err) {{
        showToast(err.message, 'error');
      }}
    }});
    acts.appendChild(bRej);
    card.appendChild(acts);
    list.appendChild(card);
  }});
}}

function renderInboxPage(state) {{
  const pending = state.pending_inbox || [];
  document.getElementById('pending-count').textContent = String(pending.length);
  document.getElementById('rail-pip').classList.toggle('show', pending.length > 0);
  document.getElementById('btn-approve-all').disabled = pending.length === 0;

  const tbody = document.getElementById('inbox-list');
  tbody.textContent = '';
  if (pending.length === 0) {{
    const tr = document.createElement('tr');
    const td = document.createElement('td');
    td.colSpan = 4;
    td.className = 'td-muted';
    td.textContent = '承認待ちの候補はありません。';
    tr.appendChild(td);
    tbody.appendChild(tr);
  }} else {{
    pending.forEach(item => {{
      const tr = document.createElement('tr');
      tr.className = 'inbox-row';

      const tdSc = document.createElement('td');
      tdSc.className = 'td-muted';
      tdSc.textContent = item.scene_label || item.scene;
      tr.appendChild(tdSc);

      const tdKind = document.createElement('td');
      tdKind.className = 'td-muted';
      tdKind.textContent = item.kind_label || item.kind;
      tr.appendChild(tdKind);

      const tdVal = document.createElement('td');
      const v = document.createElement('div');
      v.className = 'td-strong';
      v.textContent = item.value || '';
      tdVal.appendChild(v);
      if (item.reason) {{
        const r = document.createElement('div');
        r.className = 'td-muted';
        r.textContent = item.reason;
        tdVal.appendChild(r);
      }}
      let forceBox = null;
      if (item.warning) {{
        const w = document.createElement('div');
        w.className = 'warn-hl';
        w.textContent = item.warning;
        tdVal.appendChild(w);
        const lbl = document.createElement('label');
        lbl.className = 'force-check';
        forceBox = document.createElement('input');
        forceBox.type = 'checkbox';
        lbl.appendChild(forceBox);
        lbl.appendChild(document.createTextNode('確認した上で反映する'));
        tdVal.appendChild(lbl);
      }}
      tr.appendChild(tdVal);

      const tdAct = document.createElement('td');
      tdAct.className = 'td-act';
      const bOk = document.createElement('button');
      bOk.type = 'button';
      bOk.className = 'btn solid sm btn-approve-item';
      bOk.textContent = '承認';
      bOk.addEventListener('click', async () => {{
        try {{
          const force = forceBox ? forceBox.checked : false;
          const res = await apiPost('/api/inbox/approve', {{ ids: [item.id], force }});
          if (res.blocked_by_guard && res.blocked_by_guard.length > 0) {{
            showToast('確認チェックを入れてから承認してください', 'error');
            return;
          }}
          showToast('承認して反映しました', 'ok');
          await loadState();
        }} catch (err) {{
          showToast(err.message, 'error');
        }}
      }});
      const bRej = document.createElement('button');
      bRej.type = 'button';
      bRej.className = 'btn text-only sm';
      bRej.textContent = '却下';
      bRej.style.marginLeft = '4px';
      bRej.addEventListener('click', async () => {{
        try {{
          await apiPost('/api/inbox/reject', {{ ids: [item.id] }});
          showToast('却下しました', 'ok');
          await loadState();
        }} catch (err) {{
          showToast(err.message, 'error');
        }}
      }});
      tdAct.appendChild(bOk);
      tdAct.appendChild(bRej);
      tr.appendChild(tdAct);
      tbody.appendChild(tr);
    }});
  }}

  const histBody = document.getElementById('history-list');
  histBody.textContent = '';
  const hist = state.history_inbox || [];
  if (hist.length === 0) {{
    const tr = document.createElement('tr');
    const td = document.createElement('td');
    td.colSpan = 4;
    td.className = 'td-muted';
    td.textContent = '履歴はまだありません。';
    tr.appendChild(td);
    histBody.appendChild(tr);
  }} else {{
    hist.forEach(item => {{
      const tr = document.createElement('tr');
      const t1 = document.createElement('td');
      t1.className = 'td-muted';
      t1.textContent = item.scene_label || item.scene;
      const t2 = document.createElement('td');
      t2.className = 'td-muted';
      t2.textContent = item.status === 'approved' ? '承認' : '却下';
      const t3 = document.createElement('td');
      t3.textContent = item.value || '';
      const t4 = document.createElement('td');
      t4.className = 'td-muted';
      t4.textContent = item.source || '-';
      tr.appendChild(t1); tr.appendChild(t2); tr.appendChild(t3); tr.appendChild(t4);
      histBody.appendChild(tr);
    }});
  }}
}}

function renderConnectPage(state) {{
  const mcpEl = document.getElementById('mcp-list');
  mcpEl.textContent = '';
  (state.mcp_clients || []).forEach(c => {{
    const tr = document.createElement('tr');
    tr.className = 'app-row';
    const t1 = document.createElement('td');
    t1.className = 'td-strong';
    t1.title = c.config_path;
    t1.textContent = c.label;
    const t2 = document.createElement('td');
    t2.className = 'td-muted';
    t2.textContent = c.configured ? '接続済み' : (c.error ? 'エラー' : '未接続');
    const t3 = document.createElement('td');
    t3.className = 'td-act';
    if (!c.configured) {{
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'btn sm';
      btn.textContent = '登録コマンドをコピー';
      btn.addEventListener('click', () => copyCmd(c.init_cmd));
      t3.appendChild(btn);
    }}
    tr.appendChild(t1); tr.appendChild(t2); tr.appendChild(t3);
    mcpEl.appendChild(tr);
  }});

  const syncEl = document.getElementById('sync-list-card');
  syncEl.textContent = '';
  const folders = state.sync_folders || [];
  if (folders.length === 0) {{
    const tr = document.createElement('tr');
    const td = document.createElement('td');
    td.colSpan = 2;
    td.className = 'td-muted';
    td.textContent = '未検出（ローカル保存）';
    tr.appendChild(td);
    syncEl.appendChild(tr);
  }} else {{
    folders.forEach(f => {{
      const tr = document.createElement('tr');
      const t1 = document.createElement('td');
      t1.className = 'td-strong';
      t1.title = f.suggested_home;
      t1.textContent = f.provider;
      const t2 = document.createElement('td');
      t2.className = 'td-act';
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'btn sm';
      btn.textContent = '同期コマンドをコピー';
      btn.addEventListener('click', () => copyCmd('nihongo-mcp init --target all --home "' + f.suggested_home + '"'));
      t2.appendChild(btn);
      tr.appendChild(t1); tr.appendChild(t2);
      syncEl.appendChild(tr);
    }});
  }}

  const skillsWrap = document.getElementById('skills-wrap');
  skillsWrap.textContent = '';
  const previews = state.skills_preview || {{}};
  const defs = [['lite', 'Lite（nihongo/ALWAYS.md）'], ['web', 'Web・スマホ版（nihongo/WEB.md）']];
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
    det.appendChild(sum); det.appendChild(pre);
    skillsWrap.appendChild(det);
  }});
  document.getElementById('skills-section').style.display = shown > 0 ? 'block' : 'none';
}}

async function loadState() {{
  try {{
    STATE = await apiGet('/api/state');
    renderLeftNavCards(STATE);
    renderDocumentSheet(STATE);
    renderMarginInbox(STATE);
    renderInboxPage(STATE);
    renderConnectPage(STATE);

    document.getElementById('editor-path').textContent = STATE.profile.profile_path || 'profile.md';
    document.getElementById('profile-editor').value = STATE.profile.global_raw || STATE.default_template || '';
    const projCard = document.getElementById('project-raw-card');
    if (STATE.profile.project_profile_path) {{
      projCard.style.display = 'block';
      document.getElementById('project-raw-path').textContent = STATE.profile.project_profile_path;
      document.getElementById('project-raw-editor').value = STATE.project_raw || '';
    }} else {{
      projCard.style.display = 'none';
    }}
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

document.querySelectorAll('.rail-btn').forEach(btn => {{
  btn.addEventListener('click', () => switchTab(btn.dataset.tab));
}});
document.getElementById('btn-open-inbox-all').addEventListener('click', () => switchTab('inbox'));
document.getElementById('btn-tb-export').addEventListener('click', () => switchTab('connect'));
document.getElementById('btn-reload').addEventListener('click', loadState);

document.getElementById('mode-cards').addEventListener('click', () => {{
  document.getElementById('mode-cards').classList.add('active');
  document.getElementById('mode-raw').classList.remove('active');
  document.getElementById('view-cards').style.display = 'block';
  document.getElementById('view-raw').style.display = 'none';
  document.getElementById('btn-save-profile').style.display = 'none';
  if (STATE) renderMarginInbox(STATE);
}});
document.getElementById('mode-raw').addEventListener('click', () => {{
  document.getElementById('mode-raw').classList.add('active');
  document.getElementById('mode-cards').classList.remove('active');
  document.getElementById('view-raw').style.display = 'block';
  document.getElementById('view-cards').style.display = 'none';
  document.getElementById('btn-save-profile').style.display = 'inline-block';
  document.getElementById('margin-inbox-col').style.display = 'none';
}});

document.getElementById('qa-value').addEventListener('input', (e) => {{
  document.getElementById('btn-qa-add').classList.toggle('ready', e.target.value.trim().length > 0);
}});
document.getElementById('btn-qa-add').addEventListener('click', async () => {{
  const scene = document.getElementById('qa-scene').value;
  const kind = document.getElementById('qa-kind').value;
  const inp = document.getElementById('qa-value');
  const value = inp.value.trim();
  if (!value) return;
  try {{
    const res = await apiPost('/api/profile/add-item', {{ scene, kind, value }});
    inp.value = '';
    document.getElementById('btn-qa-add').classList.remove('ready');
    showToast(res.message || '追加しました', 'ok');
    await loadState();
  }} catch (err) {{
    showToast(err.message, 'error');
  }}
}});
document.getElementById('qa-value').addEventListener('keydown', (e) => {{
  if (e.key === 'Enter') {{ e.preventDefault(); document.getElementById('btn-qa-add').click(); }}
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
    showToast(res.approved_count + '件を承認しました' + (blocked ? '（警告付き ' + blocked + ' 件は個別確認）' : ''), 'ok');
    await loadState();
  }} catch (err) {{
    showToast(err.message, 'error');
  }}
}});
document.getElementById('btn-propose').addEventListener('click', async () => {{
  const scene = document.getElementById('prop-scene').value;
  const kind = document.getElementById('prop-kind').value;
  const value = document.getElementById('prop-value').value.trim();
  const reason = document.getElementById('prop-reason').value.trim();
  if (!value) {{ showToast('内容を入力してください', 'error'); return; }}
  try {{
    const res = await apiPost('/api/inbox/propose', {{ scene, kind, value, reason }});
    document.getElementById('prop-value').value = '';
    document.getElementById('prop-reason').value = '';
    document.getElementById('add-form-box').classList.remove('open');
    showToast(res.message || '受信箱に追加しました', 'ok');
    await loadState();
  }} catch (err) {{
    showToast(err.message, 'error');
  }}
}});
document.getElementById('btn-save-profile').addEventListener('click', async () => {{
  try {{
    await apiPost('/api/profile/save', {{ content: document.getElementById('profile-editor').value }});
    showToast('保存しました', 'ok');
    await loadState();
  }} catch (err) {{
    showToast(err.message, 'error');
  }}
}});
document.getElementById('btn-run-check').addEventListener('click', async () => {{
  const orig = document.getElementById('check-orig').value;
  const draft = document.getElementById('check-draft').value;
  const scene = document.getElementById('check-scene').value || null;
  if (!draft.trim()) {{ showToast('検査対象の文章を入力してください', 'error'); return; }}
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
      res.findings.forEach(f => {{ const li = document.createElement('li'); li.textContent = f; ul.appendChild(li); }});
      card.appendChild(ul);
    }}
    box.appendChild(card);
  }} catch (err) {{
    showToast(err.message, 'error');
  }}
}});
document.getElementById('exp-scene').addEventListener('change', refreshExportPreview);
document.getElementById('exp-sync').addEventListener('change', refreshExportPreview);
document.getElementById('btn-export-dl').addEventListener('click', () => {{
  const md = document.getElementById('export-preview').value;
  const blob = new Blob([md], {{ type: 'text/markdown;charset=utf-8' }});
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = 'nihongo-setup.md';
  document.body.appendChild(a); a.click(); a.remove();
  URL.revokeObjectURL(url);
  showToast('nihongo-setup.md をダウンロードしました', 'ok');
}});

loadState();
</script>
</body>
</html>
"""
