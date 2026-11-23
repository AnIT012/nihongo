"""nihongo ローカル承認 UI の HTML/CSS/JS テンプレート（Clean SaaS ワークスペース型・外部通信ゼロ）。"""
from __future__ import annotations

import json


def render_ui_html(csrf_token: str) -> str:
    """127.0.0.1 専用ローカル承認ワークスペースの単一 HTML を返す（外部リソース・外部通信ゼロ）。"""
    token_json = json.dumps(csrf_token)
    return f"""<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Ccircle cx='16' cy='16' r='12' fill='%23D7261E'/%3E%3C/svg%3E">
<title>nihongo — ローカル承認・ルール管理</title>
<style>
:root {{
  --bg: #F7F7F8;
  --surface: #FFFFFF;
  --ink: #111113;
  --body: #2C2C30;
  --muted: #63636B;
  --line: #E6E6EA;
  --line-strong: #D0D0D7;
  --red: #D7261E;
  --red-hover: #B61E17;
  --red-soft: #FEF2F2;
  --ok: #137333;
  --ok-soft: #ECFDF3;
  --shadow-sm: 0 1px 2px rgba(17, 17, 19, 0.04);
  --shadow-md: 0 4px 12px rgba(17, 17, 19, 0.06);
  --radius: 12px;
}}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
html, body {{ height: 100%; }}
body {{
  background: var(--bg);
  color: var(--ink);
  font-family: -apple-system, BlinkMacSystemFont, "Hiragino Kaku Gothic ProN", "Yu Gothic UI", "Meiryo", sans-serif;
  font-size: 14px;
  line-height: 1.6;
  -webkit-font-smoothing: antialiased;
}}

/* App Shell */
.app {{
  display: grid;
  grid-template-columns: 248px 1fr;
  min-height: 100vh;
}}

/* Sidebar */
.sidebar {{
  background: var(--surface);
  border-right: 1px solid var(--line);
  padding: 20px 14px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  position: sticky;
  top: 0;
  height: 100vh;
}}
.brand-block {{
  padding: 4px 10px 18px;
  border-bottom: 1px solid var(--line);
  margin-bottom: 14px;
}}
.logo {{
  font-family: ui-sans-serif, system-ui, sans-serif;
  font-weight: 800;
  font-size: 24px;
  letter-spacing: -0.03em;
  line-height: 1;
  margin-bottom: 8px;
}}
.logo i {{
  display: inline-block;
  width: 0.45em;
  height: 0.45em;
  border-radius: 50%;
  background: var(--red);
  margin: 0 0.04em;
}}
.local-pill {{
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 11.5px;
  font-weight: 600;
  color: var(--muted);
}}
.local-pill::before {{
  content: "";
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #16A34A;
}}

.nav-list {{
  display: flex;
  flex-direction: column;
  gap: 3px;
}}
.tab-btn {{
  appearance: none;
  border: 1px solid transparent;
  background: transparent;
  color: var(--body);
  font: inherit;
  font-size: 13.5px;
  font-weight: 600;
  padding: 9px 11px;
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
  background: #F1F1F4;
  color: var(--ink);
  font-weight: 700;
}}
.tab-left {{
  display: inline-flex;
  align-items: center;
  gap: 9px;
}}
.tab-ico {{
  width: 16px;
  height: 16px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: var(--muted);
  font-size: 13px;
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
  padding: 14px 8px 2px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}}
.meta-bar {{
  display: flex;
  flex-direction: column;
  gap: 5px;
}}
.meta-item {{
  font-size: 11.5px;
  color: var(--muted);
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}}
.meta-item.layer {{
  color: var(--ink);
  background: var(--bg);
  border: 1px solid var(--line);
  border-radius: 6px;
  padding: 4px 8px;
}}
.btn-side {{
  appearance: none;
  border: 1px solid var(--line-strong);
  background: var(--surface);
  color: var(--body);
  font: inherit;
  font-size: 12.5px;
  font-weight: 600;
  padding: 7px 10px;
  border-radius: 8px;
  cursor: pointer;
  width: 100%;
}}
.btn-side:hover {{ background: var(--bg); color: var(--ink); }}

/* Main Content */
.main {{
  padding: 28px 36px 72px;
  max-width: 960px;
  width: 100%;
}}
.panel {{ display: none; }}
.panel.active {{ display: block; }}

.toast {{
  display: none;
  margin-bottom: 18px;
  padding: 10px 14px;
  border-radius: 10px;
  font-size: 13.5px;
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
  align-items: flex-start;
  flex-wrap: wrap;
  gap: 14px;
  margin-bottom: 20px;
}}
.page-head h1 {{
  font-size: 20px;
  font-weight: 800;
  letter-spacing: -0.01em;
  line-height: 1.3;
}}
.page-sub {{
  font-size: 13px;
  color: var(--muted);
  margin-top: 3px;
}}
.head-actions {{
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
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
  box-shadow: var(--shadow-sm);
  transition: background 0.12s ease, border-color 0.12s ease;
}}
.btn:hover {{ background: var(--bg); border-color: #B4B4BE; }}
.btn.primary {{
  background: var(--red);
  border-color: var(--red);
  color: #FFFFFF;
  box-shadow: none;
}}
.btn.primary:hover {{ background: var(--red-hover); border-color: var(--red-hover); }}
.btn.dark {{
  background: var(--ink);
  border-color: var(--ink);
  color: #FFFFFF;
  box-shadow: none;
}}
.btn.dark:hover {{ background: #2A2A2E; }}
.btn.subtle {{
  border-color: var(--line);
  color: var(--muted);
  box-shadow: none;
}}
.btn.subtle:hover {{ color: var(--ink); background: var(--surface); }}
.btn:disabled {{ opacity: 0.45; cursor: not-allowed; }}

/* Surface Card */
.surface-card {{
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  box-shadow: var(--shadow-sm);
  overflow: hidden;
}}

/* Inbox List */
.card-list {{
  display: flex;
  flex-direction: column;
  gap: 10px;
}}
.item-card {{
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  padding: 16px 18px;
  box-shadow: var(--shadow-sm);
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 18px;
}}
.item-card.warn {{
  border-color: #FECACA;
  border-left: 4px solid var(--red);
  background: #FFFBFB;
}}
.item-main {{
  flex: 1;
  min-width: 0;
}}
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
.pill.kind {{
  background: #F4F4F6;
  color: var(--ink);
}}
.pill.status {{
  background: var(--ok-soft);
  color: var(--ok);
  border-color: #BBF7D0;
}}
.pill.status.rej {{
  background: var(--bg);
  color: var(--muted);
  border-color: var(--line);
}}
.item-val {{
  font-size: 15.5px;
  font-weight: 700;
  color: var(--ink);
  word-break: break-word;
  margin-bottom: 4px;
}}
.item-note {{
  font-size: 13px;
  color: var(--muted);
  margin-top: 3px;
}}
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
.warn-msg {{
  margin-top: 8px;
  font-size: 12.5px;
  font-weight: 600;
  color: var(--red-hover);
}}
.item-side {{
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 8px;
  flex-shrink: 0;
}}
.item-actions {{
  display: flex;
  gap: 7px;
  align-items: center;
}}
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
  padding: 36px 24px;
  text-align: center;
  color: var(--muted);
  font-size: 13.5px;
}}

/* Collapsible Add Form */
.form-box {{
  display: none;
  margin-bottom: 18px;
  background: var(--surface);
  border: 1px solid var(--line-strong);
  border-radius: var(--radius);
  padding: 18px 20px;
  box-shadow: var(--shadow-md);
}}
.form-box.open {{ display: block; }}
.form-box h3 {{
  font-size: 14.5px;
  font-weight: 700;
  margin-bottom: 12px;
}}
.grid-2 {{
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-bottom: 12px;
}}
label.fld {{
  display: block;
  font-size: 12.5px;
  font-weight: 600;
  color: var(--body);
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
  box-shadow: 0 0 0 2px rgba(17, 17, 19, 0.08);
}}
textarea.mono {{
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 13px;
  line-height: 1.65;
  min-height: 320px;
  border: 0;
  border-radius: 0;
  padding: 16px 18px;
  resize: vertical;
}}
textarea.mono:focus {{ box-shadow: none; }}

.editor-bar {{
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 16px;
  border-bottom: 1px solid var(--line);
  background: #FAFAFB;
  font-size: 12.5px;
  color: var(--muted);
}}

.findings-box {{
  margin-top: 16px;
  border: 1px solid var(--line-strong);
  border-radius: var(--radius);
  padding: 15px 18px;
  background: var(--surface);
  box-shadow: var(--shadow-sm);
}}
.findings-box.has-issue {{
  border-color: #FECACA;
  border-left: 4px solid var(--red);
  background: #FFFBFB;
}}
.findings-box ul {{
  margin-top: 8px;
  padding-left: 20px;
}}
.findings-box li {{
  margin: 4px 0;
  font-size: 13.5px;
}}

.sync-list {{
  margin-top: 18px;
  border: 1px solid var(--line);
  border-radius: var(--radius);
  padding: 16px 18px;
  background: var(--surface);
  box-shadow: var(--shadow-sm);
}}
.sync-list h3 {{
  font-size: 14px;
  font-weight: 700;
  margin-bottom: 6px;
}}
.sync-row {{
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 12.5px;
  padding: 7px 0;
  border-top: 1px solid var(--line);
  word-break: break-all;
  color: var(--body);
}}

.history-head {{
  font-size: 13px;
  font-weight: 700;
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
  .brand-block {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 0 12px;
    margin-bottom: 10px;
  }}
  .logo {{ margin-bottom: 0; font-size: 22px; }}
  .nav-list {{
    flex-direction: row;
    flex-wrap: wrap;
    gap: 6px;
  }}
  .tab-btn {{ padding: 7px 11px; font-size: 12.5px; }}
  .side-foot {{
    margin-top: 10px;
    padding: 10px 0 0;
    flex-direction: row;
    align-items: center;
    justify-content: space-between;
  }}
  .meta-bar {{ max-width: 65%; }}
  .btn-side {{ width: auto; }}
  .main {{ padding: 20px 16px 56px; }}
  .item-card {{ flex-direction: column; gap: 12px; }}
  .item-side {{ align-items: flex-start; width: 100%; }}
  .grid-2 {{ grid-template-columns: 1fr; }}
}}
</style>
</head>
<body>
<div class="app">
  <aside class="sidebar">
    <div>
      <div class="brand-block">
        <div class="logo">nih<i></i>ngo</div>
        <span class="local-pill">Local · 外部通信なし</span>
      </div>
      <nav class="nav-list" aria-label="メニュー">
        <button class="tab-btn active" data-tab="inbox" type="button">
          <span class="tab-left"><span class="tab-ico">●</span>承認待ち</span>
          <span class="count-dot" id="pending-count">0</span>
        </button>
        <button class="tab-btn" data-tab="profile" type="button">
          <span class="tab-left"><span class="tab-ico">≡</span>自分のルール</span>
        </button>
        <button class="tab-btn" data-tab="check" type="button">
          <span class="tab-left"><span class="tab-ico">✓</span>0トークン検査</span>
        </button>
        <button class="tab-btn" data-tab="export" type="button">
          <span class="tab-left"><span class="tab-ico">↓</span>1ファイル書き出し</span>
        </button>
      </nav>
    </div>

    <div class="side-foot">
      <div class="meta-bar" id="meta-bar"></div>
      <button class="btn-side" id="btn-reload" type="button">再読み込み</button>
    </div>
  </aside>

  <main class="main">
    <div class="toast" id="toast" role="status" aria-live="polite"></div>

    <!-- Inbox Panel -->
    <section class="panel active" id="panel-inbox">
      <div class="page-head">
        <div>
          <h1>受信箱の承認待ち</h1>
          <p class="page-sub">普段の会話から拾われた候補です。承認したものだけが profile.md に反映されます。</p>
        </div>
        <div class="head-actions">
          <button class="btn" id="btn-toggle-add" type="button">＋ 候補を追加</button>
          <button class="btn primary" id="btn-approve-all" type="button">警告なしを一括承認</button>
          <button class="btn subtle" id="btn-toggle-history" type="button">履歴</button>
        </div>
      </div>

      <div class="form-box" id="add-form-box">
        <h3>候補を手動で受信箱に追加</h3>
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
              <option value="forbidden">NG表現（絶対に言わない）</option>
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
          <button class="btn dark" id="btn-propose" type="button">受信箱に追加</button>
          <button class="btn subtle" id="btn-cancel-add" type="button">閉じる</button>
        </div>
      </div>

      <div class="card-list" id="inbox-list"></div>

      <div id="history-wrap" style="display:none;">
        <div class="history-head">処理済みの履歴（最新20件）</div>
        <div class="card-list" id="history-list"></div>
      </div>
    </section>

    <!-- Profile Panel -->
    <section class="panel" id="panel-profile">
      <div class="page-head">
        <div>
          <h1>自分のルール（profile.md）</h1>
          <p class="page-sub">保存時にメール・電話・APIキーが含まれていないか自動で検査します。</p>
        </div>
        <div class="head-actions">
          <button class="btn primary" id="btn-save-profile" type="button">変更を保存</button>
        </div>
      </div>

      <div class="surface-card">
        <div class="editor-bar">
          <span id="editor-path">profile.md</span>
          <span>UTF-8 · PII自動ガード有効</span>
        </div>
        <textarea class="mono" id="profile-editor" spellcheck="false"></textarea>
      </div>

      <div class="sync-list" id="sync-box" style="display:none;">
        <h3>この PC で検出した同期フォルダ候補</h3>
        <p style="font-size:12.5px;color:var(--muted);margin-bottom:8px;">
          <code>nihongo-mcp init --target all --home "&lt;パス&gt;"</code> に渡すと複数 PC で同じルールを共有できます。
        </p>
        <div id="sync-rows"></div>
      </div>
    </section>

    <!-- 0-Token Check Panel -->
    <section class="panel" id="panel-check">
      <div class="page-head">
        <div>
          <h1>0トークン意味ズレ検査</h1>
          <p class="page-sub">AI編集後の数字・日時・「必ず」の弱まりと、避ける表現の混入をローカルで即時検出します。</p>
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
        <div class="surface-card" style="padding:14px 16px;">
          <label class="fld" for="check-orig">元の文章（新規作成の文なら空欄）</label>
          <textarea id="check-orig" rows="7" placeholder="例：資料は明日15時までに必ず送ってください。"></textarea>
        </div>
        <div class="surface-card" style="padding:14px 16px;">
          <label class="fld" for="check-draft">AIが書いた・直した文章</label>
          <textarea id="check-draft" rows="7" placeholder="例：恐れ入りますが、資料は明日15時頃までにご送付いただけますと幸いです。"></textarea>
        </div>
      </div>
      <div id="check-result"></div>
    </section>

    <!-- Export Panel -->
    <section class="panel" id="panel-export">
      <div class="page-head">
        <div>
          <h1>1ファイル書き出し（nihongo-setup.md）</h1>
          <p class="page-sub">今のルールを引き継いだ導入ファイルを生成します。別PCやスマホのChatGPT/Claudeへそのまま添付できます。</p>
        </div>
        <div class="head-actions">
          <button class="btn primary" id="btn-export-dl" type="button">ダウンロード ↓</button>
        </div>
      </div>

      <div class="grid-2" style="margin-bottom:14px;">
        <div class="surface-card" style="padding:14px 16px;">
          <label class="fld" for="exp-scene">既定の場面</label>
          <select id="exp-scene">
            <option value="work">仕事・社内チャット・ドキュメント</option>
            <option value="formal">社外メール・目上・公式お知らせ</option>
            <option value="casual">普段のチャット・雑談</option>
          </select>
        </div>
        <div class="surface-card" style="padding:14px 16px;">
          <label class="fld" for="exp-sync">他 PC 導入時の推奨保存先</label>
          <select id="exp-sync">
            <option value="local">ローカル（~/.nihongo/profile.md）</option>
            <option value="gdrive">自分の Google Drive 同期フォルダ</option>
          </select>
        </div>
      </div>

      <div class="surface-card">
        <div class="editor-bar">
          <span>nihongo-setup.md プレビュー</span>
          <span>ローカル生成・外部送信なし</span>
        </div>
        <textarea class="mono" id="export-preview" readonly></textarea>
      </div>
    </section>
  </main>
</div>

<script>
const CSRF = {token_json};
let STATE = null;

function showToast(msg, kind) {{
  const el = document.getElementById('toast');
  el.textContent = msg;
  el.className = 'toast show ' + (kind || '');
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

function shortPath(p) {{
  if (!p) return '';
  const parts = p.split(/[\\\\/]/);
  return parts.length > 3 ? '…/' + parts.slice(-3).join('/') : p;
}}

function renderMeta(state) {{
  const bar = document.getElementById('meta-bar');
  bar.textContent = '';
  const p = document.createElement('div');
  p.className = 'meta-item';
  p.title = state.profile.profile_path || '';
  p.textContent = shortPath(state.profile.profile_path || '');
  bar.appendChild(p);
  document.getElementById('editor-path').textContent = state.profile.profile_path || 'profile.md';

  if (state.profile.project_profile_path) {{
    const l = document.createElement('div');
    l.className = 'meta-item layer';
    l.title = state.profile.project_profile_path;
    l.textContent = '2層: ' + shortPath(state.profile.project_profile_path);
    bar.appendChild(l);
  }}
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
  p2.className = 'pill kind';
  p2.textContent = item.kind_label || item.kind;
  meta.appendChild(p2);

  if (item.source) {{
    const src = document.createElement('span');
    src.textContent = 'via ' + item.source;
    meta.appendChild(src);
  }}
  if (isHistory) {{
    const st = document.createElement('span');
    st.className = 'pill status' + (item.status === 'approved' ? '' : ' rej');
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
    btnOk.className = 'btn primary';
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
    btnRej.className = 'btn subtle';
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

async function loadState() {{
  try {{
    STATE = await apiGet('/api/state');
    renderMeta(STATE);

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

    const syncBox = document.getElementById('sync-box');
    const syncRows = document.getElementById('sync-rows');
    syncRows.textContent = '';
    const folders = STATE.sync_folders || [];
    if (folders.length > 0) {{
      syncBox.style.display = 'block';
      folders.forEach(f => {{
        const row = document.createElement('div');
        row.className = 'sync-row';
        row.textContent = '[' + f.provider + '] ' + f.suggested_home;
        syncRows.appendChild(row);
      }});
    }} else {{
      syncBox.style.display = 'none';
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

document.querySelectorAll('.tab-btn').forEach(btn => {{
  btn.addEventListener('click', () => {{
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById('panel-' + btn.dataset.tab).classList.add('active');
  }});
}});

document.getElementById('btn-reload').addEventListener('click', loadState);

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
