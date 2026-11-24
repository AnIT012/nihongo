# nihongo-setup.md — nihongo 導入・適用ガイド（AI向け）

このファイルを添付された AI は、自分の動作環境に応じて次の A か B のどちらか 1 つだけを実行してください。

## A. ブラウザ・スマホのチャット（ChatGPT / Claude / Gemini 等）の場合
※ChatGPT の Code Interpreter や Claude の Artifacts などのサンドボックス環境も含みます。GitHub へのアクセスやコマンド導入は行わないでください。
- 下の「ユーザーの初期ルール」と「共通ルール」を、**今開いているこの会話から直ちに適用**する。
- 最初の返答は専門用語（Python / MCP / JSON 等）を出さず、「nihongo の日本語ルールを適用しました。このまま文章作成や手直しをどうぞ（毎回貼りたくない場合は Projects や Google Drive に置いておけます）」と 1〜2 行で返す。

## B. ローカル PC の開発エージェント（Claude Code / Cursor / Codex / Antigravity 等）の場合
ユーザー自身の PC のファイルシステムとシェルへ直接アクセスできる環境でのみ実行してください。**勝手に実行せず**、必ず次の順序と 2 回の承認を守ってください。

### 1. 安全性チェック（最初に確認して1行報告）
- 正本リポジトリ: `https://github.com/AnIT012/nihongo`（MIT ライセンス）
- 外部パッケージ依存ゼロ（Python 3.10+ の標準ライブラリのみで動作）
- 運営者サーバーへのデータ送信・保存は一切なし（`profile.md` と `inbox.jsonl` はユーザー端末または本人所有の Google Drive のみに保存）
- 実名・住所・メールアドレス・電話番号・APIキーなどの個人情報は記録しない

### 2. 確認カード 1（導入・更新の承認・必須）
正本リポジトリの安全性を確認したうえで、既存の `nihongo` や `profile.md` の有無を調べ、ユーザーに以下を提示して OK を待つ:
- `https://github.com/AnIT012/nihongo` から最新版を取得（未導入なら新規導入、導入済みなら既存設定を保ったまま最新版へ更新）
- 下の初期ルールを `profile.md` に反映（**既存の `profile.md` がある場合は絶対に上書きせず、未登録の項目だけ追記マージ**）
- この PC に入っている AI（Claude Desktop / Claude Code / Cursor / Antigravity）へ `nihongo-mcp init` で自動登録（既存設定は `.bak` に退避してから追記）

### 3. 確認カード 2（保存先と同期の選択・必須）
導入承認のあと、保存先を 1 つ選んでもらう:
- A: この PC だけで使う（`~/.nihongo/profile.md`）
- B: 自分の Google Drive / Dropbox / iCloud の同期フォルダに置く（`nihongo-mcp init --detect-sync` で検出し `--home <同期フォルダ>/nihongo` を指定）
- C: 今開いている作業フォルダ専用にする（`nihongo-check profile init --project` で `./.nihongo/profile.md` を作成）

### 4. 承認後の実行コマンド（AI が代行）
- CLI・MCP 導入: `pip install "git+https://github.com/AnIT012/nihongo.git@v3.1.0"`
- スキル導入（対応環境）: `npx skills add AnIT012/nihongo -g`（またはリポジトリの `nihongo/` フォルダをスキル配置先へコピー）
- AI アプリ自動登録: `nihongo-mcp init --target all`（同期フォルダ選択時は `--home "<同期フォルダ>/nihongo"` を付与）
- 初期ルール反映: 既存 `profile.md` があれば上書きせず未登録の表現だけ追記マージ（新規は `nihongo-check profile init`）
- 疎通・診断確認: `nihongo-mcp --self-test` と `nihongo-check doctor` を実行

完了したら「以降は普段どおり話すだけで自動適用されます。今のルールや承認待ちはチャットで「ルール見せて」「承認待ちある？」と聞くだけで確認できます」と 1 行で案内する。

## ユーザーの初期ルール（profile.md 互換）
- よく使う場面：仕事・社内チャット・ドキュメント（`[work]`）
- 避ける表現（絶対に言わない表現）：（未設定・会話しながら追加）
- 書く時の考え方：（会話しながら追加）

## 共通ルール（ブラウザ・スマホチャット即適用）
1. 事実を作らない。依頼や資料にない数字・理由・約束（調整します等）を足さず、不明な値だけ【日時】等の空欄にする。
2. なりすまし・詐欺・個人情報窃取の文は断る。
3. 敬語は迷ったら1段低くし、読点は読み違える所と長い前置きの後にだけ打つ。
4. 前置き・言い直し・不要なまとめを省き、推敲では元の意味や必須度（必ず等）を弱めない。
5. 友達向けのくだけた語尾や絵文字を目上・社外向けへ持ち込まない。
