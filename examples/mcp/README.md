# nihongo-mcp（HITL 個人プロフィール・0トークン検査 MCP サーバー）

※このページは PC で Claude Desktop / Cursor / Claude Code / Antigravity を使い、Python やターミナル操作に慣れている方向けの拡張ガイドです。普段の Web 版やスマホ版の ChatGPT / Claude で使う方は、トップページのコピペ設定だけで十分使えます。

Python 3.10+ の標準ライブラリだけで動くローカル MCP サーバー（stdio）です。追加パッケージのインストールは不要で、作者側のサーバーへあなたの文章を送ったり保存したりすることも一切ありません。

## できること

| ツール / リソース | 役割 |
|---|---|
| `get_profile` | `~/.nihongo/profile.md`（唯一の正）と禁止表現一覧・保留中 inbox 件数を読み取る |
| `propose_profile_entry` | 外向け成果物への修正から追記候補を `~/.nihongo/inbox.jsonl` に積む（**`profile.md` は書き換えない**。雑なチャットや誤字からは拾わない） |
| `list_inbox` | 本人承認待ち（`pending`）の候補を連番と日本語ラベル付きで一覧表示する |
| `review_inbox_entry` | 候補を承認（`approve`）・却下（`reject`）・一括混在処理（`batch`）する（いずれも `confirmed_by_user: true` が必須） |
| `check_meaning_diff` | 原文と編集後の文の意味ズレ・`profile.md` 違反を0トークンでローカル検査する |
| `nihongo://profile` / `nihongo://inbox/pending` | MCP Resource として現在のプロフィールと保留候補を直接参照する |

## 1コマンドで自動登録する（推奨）

JSON を手書きせず、いま入っている他の設定を残したまま、自動でバックアップを取って追加できます。

```bash
# Claude Desktop に登録（まずは --dry-run で確認も可）
python3 nihongo/scripts/mcp_server.py init --target claude-desktop

# Cursor / Claude Code / Antigravity に登録
python3 nihongo/scripts/mcp_server.py init --target cursor
python3 nihongo/scripts/mcp_server.py init --target claude-code
python3 nihongo/scripts/mcp_server.py init --target antigravity

# 企業・厳格運用（MCP からの profile.md 承認を物理ブロックし、CLI 承認のみに限定）
python3 nihongo/scripts/mcp_server.py init --target claude-desktop --strict-hitl
```

## 手動設定例（Claude Desktop / Cursor / Claude Code）

`claude-desktop-config.json` のパスをローカルの配置先に合わせて登録します（`pip install` 済みなら `command` を `"nihongo-mcp"`、`args` を `[]` にできます）。

```json
{
  "mcpServers": {
    "nihongo": {
      "command": "python3",
      "args": [
        "/path/to/nihongo/nihongo/scripts/mcp_server.py"
      ]
    }
  }
}
```

## ローカル承認 UI（`nihongo-check ui`）

ターミナルを使わずブラウザ画面で受信箱の承認・却下、`profile.md` の編集、0トークン検査、他端末用 `nihongo-setup.md` の書き出しができます（`127.0.0.1` のみで動作、外部通信ゼロ）。

```bash
nihongo-check ui
# または
python3 nihongo/scripts/cli.py ui
```

## 複数 PC 同期と分野別ルール（2層プロファイル）

- **複数 PC 同期**：`python3 nihongo/scripts/mcp_server.py init --detect-sync` で PC 内の Google Drive / Dropbox / iCloud フォルダを検出し、`--home "<同期フォルダ>/nihongo"` を指定すると複数 PC で共有できます（API 直接連携の `GoogleDriveStorage` を含めた手順は [google-drive-sync.md](google-drive-sync.md) を参照）。
- **分野・案件別の別ルール**：作業フォルダ内に `.nihongo/profile.md` を置くと、`get_profile(project_dir=...)` や `nihongo-check profile show --project <dir>` で共通プロフィールに自動で重ねて適用されます。

## 動作確認

```bash
python3 nihongo/scripts/mcp_server.py --self-test
```

データ保存先を変えたい場合は `--home <dir>` または環境変数 `NIHONGO_HOME` を指定してください。
