#!/usr/bin/env python3
"""nihongo のローカル承認 UI サーバー（標準ライブラリのみ・外部通信ゼロ）。

使い方:
    nihongo-check ui
    nihongo-check ui --port 8765 --no-browser

セキュリティ原則:
- 127.0.0.1 のみにバインドし、外部ネットワークからは接続不可とする。
- Host / Origin ヘッダ検証とプロセス毎のランダム CSRF トークンで DNS リバインディングと CSRF を防ぐ。
- CSP により外部リソース読み込みと外部送信を禁止する。
- profile.md への手動保存・受信箱追加はすべて inbox.py の PII ガードとアトミック書き込みを経由する。
"""
from __future__ import annotations

import hmac
import http.server
import json
import os
import secrets
import sys
import threading
import time
import urllib.parse
import webbrowser
from typing import Any

if __package__:
    from . import cli as cli_mod
    from . import inbox as inbox_mod
    from . import revert_broken, trim_commas
else:
    _SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    if _SCRIPT_DIR not in sys.path:
        sys.path.insert(0, _SCRIPT_DIR)
    import cli as cli_mod  # noqa: E402
    import inbox as inbox_mod  # noqa: E402
    import revert_broken  # noqa: E402
    import trim_commas  # noqa: E402

MAX_BODY_BYTES = 256 * 1024

_SCENE_LABELS: dict[str, str] = {
    "common": "共通",
    "casual": "普段・雑談",
    "work": "社内・同僚",
    "formal": "社外・目上",
}
_KIND_LABELS: dict[str, str] = {
    "forbidden": "NG表現",
    "rule": "書く時の考え方",
    "tone": "口調・記号",
    "first_person": "一人称",
}


def _load_web_md_fallback() -> str | None:
    """リポジトリ内の nihongo/WEB.md があれば読み込む。"""
    cand = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "WEB.md"))
    if os.path.isfile(cand):
        try:
            with open(cand, encoding="utf-8-sig") as f:
                return f.read().strip()
        except OSError:
            return None
    return None


def _render_ui_html(csrf_token: str) -> str:
    """880px 1カラム・白×墨黒×赤の nihongo ローカル承認画面 HTML を返す（外部通信ゼロ）。"""
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
  --red: #D7261E;
  --red-dark: #B31E18;
  --ink: #111111;
  --muted: #555555;
  --line: #E4E4E4;
  --soft: #F6F6F5;
  --ok: #137333;
  --warn-bg: #FFF4F3;
}}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{
  background: #FFFFFF;
  color: var(--ink);
  font-family: -apple-system, BlinkMacSystemFont, "Hiragino Kaku Gothic ProN", "Yu Gothic UI", "Meiryo", sans-serif;
  line-height: 1.65;
  -webkit-font-smoothing: antialiased;
}}
.wrap {{
  max-width: 880px;
  margin: 0 auto;
  padding: 28px 24px 80px;
}}
header {{
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 14px;
  padding-bottom: 20px;
  border-bottom: 2px solid var(--ink);
}}
.brand {{
  display: flex;
  align-items: baseline;
  gap: 12px;
}}
.logo {{
  font-family: ui-sans-serif, system-ui, sans-serif;
  font-weight: 800;
  font-size: 30px;
  letter-spacing: -0.03em;
  line-height: 1;
}}
.logo i {{
  display: inline-block;
  width: 0.46em;
  height: 0.46em;
  border-radius: 50%;
  background: var(--red);
  margin: 0 0.04em;
}}
.sub-tag {{
  font-size: 13px;
  font-weight: 700;
  color: var(--muted);
}}
.meta-bar {{
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 14px;
  font-size: 12.5px;
  color: var(--muted);
}}
.meta-item {{
  background: var(--soft);
  border: 1px solid var(--line);
  border-radius: 999px;
  padding: 4px 12px;
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}}
.meta-item.layer {{
  border-color: var(--ink);
  color: var(--ink);
  background: #FFFFFF;
}}
.tabs {{
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin: 24px 0 22px;
}}
.tab-btn {{
  appearance: none;
  border: 2px solid var(--line);
  background: #FFFFFF;
  color: var(--ink);
  font: inherit;
  font-size: 14px;
  font-weight: 700;
  padding: 9px 16px;
  border-radius: 999px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 8px;
}}
.tab-btn:hover {{ border-color: var(--ink); }}
.tab-btn.active {{
  background: var(--ink);
  border-color: var(--ink);
  color: #FFFFFF;
}}
.count-dot {{
  background: var(--red);
  color: #FFFFFF;
  font-size: 12px;
  font-weight: 800;
  padding: 1px 7px;
  border-radius: 999px;
}}
.tab-btn.active .count-dot {{
  background: #FFFFFF;
  color: var(--ink);
}}
.panel {{ display: none; }}
.panel.active {{ display: block; }}

.toast {{
  display: none;
  margin-bottom: 18px;
  padding: 12px 16px;
  border-radius: 12px;
  font-size: 14px;
  font-weight: 700;
  border: 2px solid var(--ink);
  background: var(--soft);
}}
.toast.show {{ display: block; }}
.toast.error {{
  border-color: var(--red);
  background: var(--warn-bg);
  color: var(--red-dark);
}}
.toast.ok {{
  border-color: var(--ok);
  background: #F2FAF4;
  color: var(--ok);
}}

.section-head {{
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 16px;
}}
.section-head h2 {{
  font-size: 20px;
  font-weight: 800;
}}
.btn {{
  appearance: none;
  border: 2px solid var(--ink);
  background: #FFFFFF;
  color: var(--ink);
  font: inherit;
  font-size: 13.5px;
  font-weight: 700;
  padding: 8px 15px;
  border-radius: 10px;
  cursor: pointer;
}}
.btn:hover {{ background: var(--soft); }}
.btn.primary {{
  background: var(--red);
  border-color: var(--red);
  color: #FFFFFF;
}}
.btn.primary:hover {{ background: var(--red-dark); border-color: var(--red-dark); }}
.btn.dark {{
  background: var(--ink);
  border-color: var(--ink);
  color: #FFFFFF;
}}
.btn.subtle {{
  border-color: var(--line);
  color: var(--muted);
}}
.btn:disabled {{ opacity: 0.45; cursor: not-allowed; }}

.card-list {{
  display: flex;
  flex-direction: column;
  gap: 14px;
}}
.item-card {{
  border: 2.5px solid var(--ink);
  border-radius: 18px;
  padding: 18px 20px;
  background: #FFFFFF;
}}
.item-card.warn {{
  border-color: var(--red);
  background: var(--warn-bg);
}}
.item-top {{
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 10px;
}}
.tags {{
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  font-size: 12px;
  font-weight: 700;
}}
.tag {{
  border: 1.5px solid var(--ink);
  border-radius: 999px;
  padding: 2px 10px;
  background: #FFFFFF;
}}
.tag.muted {{
  border-color: var(--line);
  color: var(--muted);
}}
.item-val {{
  font-size: 17px;
  font-weight: 800;
  margin-bottom: 6px;
  word-break: break-word;
}}
.item-note {{
  font-size: 13.5px;
  color: var(--muted);
  margin-bottom: 8px;
}}
.warn-msg {{
  font-size: 13px;
  font-weight: 700;
  color: var(--red-dark);
  margin: 8px 0 10px;
}}
.item-actions {{
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
  margin-top: 12px;
}}
.force-check {{
  display: inline-flex;
  align-items: center;
  gap: 6px;
  flex-basis: 100%;
  font-size: 13px;
  font-weight: 700;
  color: var(--red-dark);
}}
.empty-box {{
  border: 2px dashed #CCCCCC;
  border-radius: 18px;
  padding: 32px 24px;
  text-align: center;
  color: var(--muted);
  font-size: 14.5px;
}}

.form-box {{
  margin-top: 24px;
  border: 2px solid var(--line);
  border-radius: 18px;
  padding: 20px;
  background: var(--soft);
}}
.form-box h3 {{
  font-size: 15.5px;
  font-weight: 800;
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
  font-size: 13px;
  font-weight: 700;
  margin-bottom: 5px;
}}
input[type="text"], select, textarea {{
  width: 100%;
  font: inherit;
  font-size: 14px;
  padding: 10px 12px;
  border: 2px solid #CCCCCC;
  border-radius: 10px;
  background: #FFFFFF;
  color: var(--ink);
}}
input[type="text"]:focus, select:focus, textarea:focus {{
  outline: none;
  border-color: var(--ink);
}}
textarea.mono {{
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 13.5px;
  line-height: 1.65;
  min-height: 280px;
}}
.findings-box {{
  margin-top: 16px;
  border: 2.5px solid var(--ink);
  border-radius: 16px;
  padding: 16px 18px;
  background: #FFFFFF;
}}
.findings-box.has-issue {{
  border-color: var(--red);
}}
.findings-box ul {{
  margin-top: 8px;
  padding-left: 20px;
}}
.findings-box li {{
  margin: 5px 0;
  font-size: 14px;
}}
.sync-list {{
  margin-top: 18px;
  border: 2px solid var(--line);
  border-radius: 16px;
  padding: 16px 18px;
  background: #FFFFFF;
}}
.sync-list h3 {{
  font-size: 15px;
  font-weight: 800;
  margin-bottom: 8px;
}}
.sync-row {{
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 13px;
  padding: 6px 0;
  border-top: 1px solid var(--line);
  word-break: break-all;
}}
@media (max-width: 640px) {{
  .wrap {{ padding: 20px 16px 64px; }}
  .grid-2 {{ grid-template-columns: 1fr; }}
  header {{ align-items: flex-start; }}
}}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <div class="brand">
      <div class="logo">nih<i></i>ngo</div>
      <span class="sub-tag">ローカル承認・ルール管理（外部通信なし）</span>
    </div>
    <button class="btn subtle" id="btn-reload" type="button">最新状態を読み込む</button>
  </header>

  <div class="meta-bar" id="meta-bar"></div>

  <nav class="tabs" aria-label="画面切り替え">
    <button class="tab-btn active" data-tab="inbox" type="button">
      承認待ち <span class="count-dot" id="pending-count">0</span>
    </button>
    <button class="tab-btn" data-tab="profile" type="button">自分のルール（profile.md）</button>
    <button class="tab-btn" data-tab="check" type="button">0トークン検査</button>
    <button class="tab-btn" data-tab="export" type="button">1ファイル書き出し</button>
  </nav>

  <div class="toast" id="toast" role="status" aria-live="polite"></div>

  <section class="panel active" id="panel-inbox">
    <div class="section-head">
      <h2>受信箱の承認待ち</h2>
      <div style="display:flex;gap:8px;flex-wrap:wrap;">
        <button class="btn primary" id="btn-approve-all" type="button">警告なしをまとめて承認</button>
        <button class="btn subtle" id="btn-toggle-history" type="button">履歴を見る</button>
      </div>
    </div>
    <div class="card-list" id="inbox-list"></div>
    <div id="history-wrap" style="display:none;margin-top:24px;">
      <h3 style="font-size:15.5px;margin-bottom:10px;">処理済みの履歴（最新20件）</h3>
      <div class="card-list" id="history-list"></div>
    </div>

    <div class="form-box">
      <h3>候補を手動で受信箱に追加する</h3>
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
      <div style="margin-bottom:12px;">
        <label class="fld" for="prop-value">内容（1行・個人情報は含めない）</label>
        <input type="text" id="prop-value" placeholder="例：いただけますと幸いです">
      </div>
      <div style="margin-bottom:14px;">
        <label class="fld" for="prop-reason">理由メモ（任意）</label>
        <input type="text" id="prop-reason" placeholder="例：メールの結びが硬くなりすぎるため">
      </div>
      <button class="btn dark" id="btn-propose" type="button">受信箱に追加する</button>
    </div>
  </section>

  <section class="panel" id="panel-profile">
    <div class="section-head">
      <h2>自分のルール（profile.md）</h2>
      <button class="btn primary" id="btn-save-profile" type="button">変更を保存する</button>
    </div>
    <p style="font-size:13.5px;color:var(--muted);margin-bottom:12px;">
      保存時にメールアドレス・電話番号・APIキーが含まれていないか自動で検査します。作業フォルダに <code>.nihongo/profile.md</code> がある場合は、検査時に自動で重ねて適用されます。
    </p>
    <textarea class="mono" id="profile-editor" spellcheck="false"></textarea>
    <div class="sync-list" id="sync-box" style="display:none;">
      <h3>この PC で検出した同期フォルダ候補（複数PC同期用）</h3>
      <p style="font-size:13px;color:var(--muted);margin-bottom:8px;">
        下のパスを <code>nihongo-mcp init --target all --home "&lt;パス&gt;"</code> に渡すと、Google Drive 等で複数 PC と同じルールを共有できます。
      </p>
      <div id="sync-rows"></div>
    </div>
  </section>

  <section class="panel" id="panel-check">
    <div class="section-head">
      <h2>0トークン意味ズレ・NG表現検査</h2>
      <div style="display:flex;gap:8px;align-items:center;">
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
        <label class="fld" for="check-orig">元の文章（1から書いた文なら空欄でOK）</label>
        <textarea id="check-orig" rows="6" placeholder="例：資料は明日15時までに必ず送ってください。"></textarea>
      </div>
      <div>
        <label class="fld" for="check-draft">AIが書いた・直した文章</label>
        <textarea id="check-draft" rows="6" placeholder="例：恐れ入りますが、資料は明日15時頃までにご送付いただけますと幸いです。"></textarea>
      </div>
    </div>
    <div id="check-result"></div>
  </section>

  <section class="panel" id="panel-export">
    <div class="section-head">
      <h2>他 PC・スマホ AI 用の 1 ファイルを書き出す</h2>
      <button class="btn primary" id="btn-export-dl" type="button">nihongo-setup.md をダウンロード</button>
    </div>
    <p style="font-size:14px;color:var(--muted);margin-bottom:14px;">
      現在の <code>profile.md</code> の設定を引き継いだ <code>nihongo-setup.md</code> をローカルで生成します。別の PC やスマホの ChatGPT / Claude にそのまま添付して使えます。
    </p>
    <div class="grid-2" style="margin-bottom:14px;">
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
    <textarea class="mono" id="export-preview" readonly></textarea>
  </section>
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

function renderMeta(state) {{
  const bar = document.getElementById('meta-bar');
  bar.textContent = '';
  const p = document.createElement('span');
  p.className = 'meta-item';
  p.textContent = '保存先: ' + state.profile.profile_path;
  bar.appendChild(p);
  if (state.profile.project_profile_path) {{
    const l = document.createElement('span');
    l.className = 'meta-item layer';
    l.textContent = '2層適用中: ' + state.profile.project_profile_path;
    bar.appendChild(l);
  }}
}}

function buildItemCard(item, isHistory) {{
  const card = document.createElement('div');
  card.className = 'item-card' + (item.warning && !isHistory ? ' warn' : '');

  const top = document.createElement('div');
  top.className = 'item-top';
  const tags = document.createElement('div');
  tags.className = 'tags';

  const t1 = document.createElement('span');
  t1.className = 'tag';
  t1.textContent = item.scene_label || item.scene;
  tags.appendChild(t1);

  const t2 = document.createElement('span');
  t2.className = 'tag';
  t2.textContent = item.kind_label || item.kind;
  tags.appendChild(t2);

  if (item.source) {{
    const t3 = document.createElement('span');
    t3.className = 'tag muted';
    t3.textContent = item.source;
    tags.appendChild(t3);
  }}
  if (isHistory) {{
    const ts = document.createElement('span');
    ts.className = 'tag muted';
    ts.textContent = item.status === 'approved' ? '承認済み' : '却下済み';
    tags.appendChild(ts);
  }}

  const idSpan = document.createElement('span');
  idSpan.style.fontSize = '12px';
  idSpan.style.color = '#666';
  idSpan.style.fontFamily = 'ui-monospace, monospace';
  idSpan.textContent = item.id;

  top.appendChild(tags);
  top.appendChild(idSpan);
  card.appendChild(top);

  const val = document.createElement('div');
  val.className = 'item-val';
  val.textContent = item.value || '';
  card.appendChild(val);

  if (item.reason) {{
    const r = document.createElement('div');
    r.className = 'item-note';
    r.textContent = '理由: ' + item.reason;
    card.appendChild(r);
  }}
  if (item.example_before || item.example_after) {{
    const ex = document.createElement('div');
    ex.className = 'item-note';
    ex.textContent = '例: ' + (item.example_before || '') + ' → ' + (item.example_after || '');
    card.appendChild(ex);
  }}

  if (!isHistory) {{
    let forceBox = null;
    if (item.warning) {{
      const w = document.createElement('div');
      w.className = 'warn-msg';
      w.textContent = item.warning;
      card.appendChild(w);
    }}

    const actions = document.createElement('div');
    actions.className = 'item-actions';

    if (item.warning) {{
      const lbl = document.createElement('label');
      lbl.className = 'force-check';
      forceBox = document.createElement('input');
      forceBox.type = 'checkbox';
      lbl.appendChild(forceBox);
      lbl.appendChild(document.createTextNode('警告を確認した上で反映する'));
      actions.appendChild(lbl);
    }}

    const btnOk = document.createElement('button');
    btnOk.type = 'button';
    btnOk.className = 'btn primary';
    btnOk.textContent = '承認して反映';
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
    btnRej.className = 'btn';
    btnRej.textContent = '却下する';
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
    card.appendChild(actions);
  }}
  return card;
}}

async function loadState() {{
  try {{
    STATE = await apiGet('/api/state');
    renderMeta(STATE);

    const pending = STATE.pending_inbox || [];
    document.getElementById('pending-count').textContent = String(pending.length);
    document.getElementById('btn-approve-all').disabled = pending.length === 0;

    const listEl = document.getElementById('inbox-list');
    listEl.textContent = '';
    if (pending.length === 0) {{
      const empty = document.createElement('div');
      empty.className = 'empty-box';
      empty.textContent = '承認待ちの候補はありません。普段のチャットで言い回しを直すと、ここに候補が溜まります。';
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

    const editor = document.getElementById('profile-editor');
    editor.value = STATE.profile.global_raw || STATE.default_template || '';

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

document.getElementById('btn-toggle-history').addEventListener('click', () => {{
  const wrap = document.getElementById('history-wrap');
  const open = wrap.style.display === 'none';
  wrap.style.display = open ? 'block' : 'none';
  document.getElementById('btn-toggle-history').textContent = open ? '履歴を閉じる' : '履歴を見る';
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
    title.style.fontWeight = '800';
    title.textContent = res.count === 0
      ? '見直す候補はありません（0 tokens / ' + res.elapsed_ms + 'ms）'
      : '見直す候補が ' + res.count + ' 件あります（0 tokens / ' + res.elapsed_ms + 'ms）';
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


class NihongoUiServer(http.server.ThreadingHTTPServer):
    """ローカル承認 UI 用の軽量 HTTP サーバー（127.0.0.1 専用）。"""

    allow_reuse_address = os.name != "nt"

    def __init__(
        self,
        *,
        host: str = "127.0.0.1",
        port: int = 8765,
        home: str | None = None,
        profile_path: str | None = None,
        inbox_path: str | None = None,
        project_dir: str | None = None,
        storage: inbox_mod.ProfileStorage | None = None,
    ) -> None:
        if host not in ("127.0.0.1", "localhost"):
            raise ValueError("セキュリティ保護のため、ローカル承認 UI は 127.0.0.1 のみで起動します。")
        self.storage: inbox_mod.ProfileStorage = (
            storage
            if storage is not None
            else inbox_mod.LocalFileStorage(
                home=home,
                profile_path=profile_path,
                inbox_path=inbox_path,
            )
        )
        self.project_dir = project_dir
        self.state_lock = threading.RLock()
        self.csrf_token = secrets.token_urlsafe(32)
        self.html_bytes = _render_ui_html(self.csrf_token).encode("utf-8")
        super().__init__(("127.0.0.1", int(port)), _UiRequestHandler)


class _UiRequestHandler(http.server.BaseHTTPRequestHandler):
    server: NihongoUiServer

    def log_message(self, format: str, *args: Any) -> None:
        # 標準エラー出力を汚さない
        return

    def _allowed_hosts(self) -> set[str]:
        port = self.server.server_address[1]
        allowed = {f"127.0.0.1:{port}", f"localhost:{port}"}
        if port == 80:
            allowed.update({"127.0.0.1", "localhost"})
        return allowed

    def _check_host(self) -> bool:
        host = (self.headers.get("Host") or "").strip().lower()
        return host in self._allowed_hosts()

    def _check_origin_and_csrf(self) -> str | None:
        origin = (self.headers.get("Origin") or "").strip().lower()
        if origin:
            parsed = urllib.parse.urlparse(origin)
            if parsed.scheme != "http" or parsed.netloc not in self._allowed_hosts():
                return "不正な Origin からのリクエストを拒否しました。"
        token = (self.headers.get("X-Nihongo-CSRF") or "").strip()
        if not token or not hmac.compare_digest(token, self.server.csrf_token):
            return "CSRF トークンが一致しません。ページを再読み込みしてください。"
        return None

    def _send_headers(self, status: int, content_type: str, length: int, *, close: bool = False) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(length))
        if close:
            self.send_header("Connection", "close")
            self.close_connection = True
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self' 'unsafe-inline'; connect-src 'self'; img-src 'self' data:; frame-ancestors 'none'",
        )
        self.end_headers()

    def _send_json(self, status: int, payload: dict[str, Any], *, close: bool = False) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self._send_headers(status, "application/json; charset=utf-8", len(body), close=close)
        self.wfile.write(body)

    def _read_json_body(self) -> tuple[dict[str, Any] | None, int | None, str | None]:
        raw_len = self.headers.get("Content-Length")
        if raw_len is None:
            return ({}, None, None)
        try:
            length = int(raw_len)
        except ValueError:
            return (None, 400, "Content-Length が不正です。")
        if length < 0 or length > MAX_BODY_BYTES:
            return (None, 413, "リクエストサイズが大きすぎます。")
        raw = self.rfile.read(length) if length > 0 else b"{}"
        try:
            data = json.loads(raw.decode("utf-8"))
        except Exception:
            return (None, 400, "JSON の形式が正しくありません。")
        if not isinstance(data, dict):
            return (None, 400, "JSON オブジェクトを送信してください。")
        return (data, None, None)

    def _enrich_items(self, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for item in items:
            sc = str(item.get("scene", "common"))
            kd = str(item.get("kind", "rule"))
            c = dict(item)
            c["scene_label"] = _SCENE_LABELS.get(sc, sc)
            c["kind_label"] = _KIND_LABELS.get(kd, kd)
            out.append(c)
        return out

    def do_GET(self) -> None:
        if not self._check_host():
            self._send_json(403, {"error": "不正な Host ヘッダのため拒否しました。"})
            return

        path = urllib.parse.urlparse(self.path).path
        if path == "/favicon.ico":
            self._send_headers(204, "image/x-icon", 0)
            return
        if path in ("/", "/index.html"):
            body = self.server.html_bytes
            self._send_headers(200, "text/html; charset=utf-8", len(body))
            self.wfile.write(body)
            return

        if path == "/api/state":
            try:
                with self.server.state_lock:
                    prof = inbox_mod.read_profile(
                        storage=self.server.storage,
                        project_dir=self.server.project_dir,
                        include_project=True,
                    )
                    all_items = inbox_mod.list_inbox(status="all", storage=self.server.storage)
                pending = [x for x in all_items if x.get("status") == "pending"]
                history = [x for x in all_items if x.get("status") != "pending"][-20:][::-1]
                self._send_json(
                    200,
                    {
                        "version": cli_mod.__version__,
                        "profile": prof,
                        "default_template": inbox_mod.DEFAULT_PROFILE_TEMPLATE,
                        "pending_inbox": self._enrich_items(pending),
                        "history_inbox": self._enrich_items(history),
                        "sync_folders": inbox_mod.detect_sync_folders(),
                    },
                )
            except Exception as exc:
                self._send_json(500, {"error": f"状態の読み込みに失敗しました: {exc}"})
            return

        self._send_json(404, {"error": "Not Found"})

    def do_POST(self) -> None:
        if not self._check_host():
            self._send_json(403, {"error": "不正な Host ヘッダのため拒否しました。"})
            return
        csrf_err = self._check_origin_and_csrf()
        if csrf_err:
            self._send_json(403, {"error": csrf_err})
            return

        data, err_status, err_msg = self._read_json_body()
        if err_status is not None or data is None:
            self._send_json(err_status or 400, {"error": err_msg or "Bad Request"}, close=(err_status == 413))
            return

        path = urllib.parse.urlparse(self.path).path
        try:
            if path == "/api/inbox/propose":
                with self.server.state_lock:
                    res = inbox_mod.propose_entry(
                        scene=str(data.get("scene") or "common"),
                        kind=str(data.get("kind") or "rule"),
                        value=str(data.get("value") or ""),
                        reason=str(data.get("reason") or ""),
                        source="local-ui",
                        storage=self.server.storage,
                    )
                self._send_json(200, res)
                return

            if path == "/api/inbox/approve":
                raw_ids = data.get("ids")
                if raw_ids is not None and not isinstance(raw_ids, list):
                    raise ValueError("ids は文字列の配列で指定してください。")
                ids = [str(x) for x in (raw_ids or [])]
                approve_all = data.get("approve_all") is True
                force = data.get("force") is True
                with self.server.state_lock:
                    res = inbox_mod.approve_entries(
                        ids,
                        approve_all=approve_all,
                        force=force,
                        storage=self.server.storage,
                    )
                self._send_json(200, res)
                return

            if path == "/api/inbox/reject":
                raw_ids = data.get("ids")
                if raw_ids is not None and not isinstance(raw_ids, list):
                    raise ValueError("ids は文字列の配列で指定してください。")
                ids = [str(x) for x in (raw_ids or [])]
                reject_all = data.get("reject_all") is True
                reason = str(data.get("reason") or "")
                with self.server.state_lock:
                    res = inbox_mod.reject_entries(
                        ids,
                        reject_all=reject_all,
                        reason=reason,
                        storage=self.server.storage,
                    )
                self._send_json(200, res)
                return

            if path == "/api/profile/save":
                if "content" not in data or not isinstance(data["content"], str):
                    raise ValueError("content は文字列で指定してください。")
                with self.server.state_lock:
                    res = inbox_mod.save_profile_direct(data["content"], storage=self.server.storage)
                self._send_json(200, res)
                return

            if path == "/api/check":
                t0 = time.perf_counter()
                orig = str(data.get("orig") or "")
                draft = str(data.get("draft") or "")
                request = str(data.get("request") or "")
                scene = data.get("scene")
                if scene not in ("casual", "work", "formal"):
                    scene = None

                prof = inbox_mod.read_profile(
                    storage=self.server.storage,
                    project_dir=self.server.project_dir,
                    include_project=True,
                )
                forbidden = cli_mod.parse_profile_text(prof["raw"], scene=scene) if prof["exists"] else []
                findings = revert_broken.remaining(orig, draft, request)
                if forbidden or scene:
                    findings = findings + cli_mod.check_profile_drift(orig, draft, forbidden, scene=scene)
                formatted = [cli_mod._format_finding(x) for x in findings]
                elapsed_ms = max(1, int(round((time.perf_counter() - t0) * 1000)))
                self._send_json(
                    200,
                    {
                        "clean": len(formatted) == 0,
                        "count": len(formatted),
                        "findings": formatted,
                        "elapsed_ms": elapsed_ms,
                        "layers": prof["layers"],
                    },
                )
                return

            if path == "/api/setup/export":
                scene = str(data.get("scene") or "work")
                sync_pref = str(data.get("sync_preference") or "local")
                prof = inbox_mod.read_profile(
                    storage=self.server.storage,
                    project_dir=self.server.project_dir,
                    include_project=True,
                )
                forbidden = cli_mod.parse_profile_text(prof["raw"]) if prof["exists"] else []
                md = inbox_mod.build_setup_markdown(
                    forbidden=forbidden,
                    scene=scene,
                    sync_preference=sync_pref,
                    web_fallback_text=_load_web_md_fallback(),
                )
                self._send_json(200, {"markdown": md, "forbidden_count": len(forbidden)})
                return

            self._send_json(404, {"error": "Not Found"})
        except ValueError as exc:
            self._send_json(400, {"error": str(exc)})
        except Exception as exc:
            self._send_json(500, {"error": f"処理中にエラーが発生しました: {exc}"})


def run_ui_server(
    *,
    port: int = 8765,
    home: str | None = None,
    profile_path: str | None = None,
    inbox_path: str | None = None,
    project_dir: str | None = None,
    open_browser: bool = True,
) -> int:
    server = NihongoUiServer(
        port=port,
        home=home,
        profile_path=profile_path,
        inbox_path=inbox_path,
        project_dir=project_dir,
    )
    actual_port = server.server_address[1]
    url = f"http://127.0.0.1:{actual_port}/"
    print(f"nihongo ローカル承認 UI を起動しました: {url}", flush=True)
    print("終了するには Ctrl+C を押してください（この画面は 127.0.0.1 のみで動作します）。", flush=True)
    if open_browser:
        try:
            webbrowser.open(url)
        except Exception:
            pass
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nローカル承認 UI を停止しました。")
    finally:
        server.server_close()
    return 0
