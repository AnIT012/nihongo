# Google Drive / クラウド同期ガイド（運営サーバー保存ゼロ）

`nihongo` は運営者側のデータベースを一切持たず、ユーザー自身の端末またはクラウドストレージに `profile.md` と `inbox.jsonl` を置く設計です。複数 PC やスマホから同じ日本語ルールを使いたい場合は、次の 2 つの方法から選べます。

## 方法 A：PC の同期フォルダを指定する（OAuth 設定不要・最短 1 分）

すでに PC に Google Drive for Desktop / Dropbox / iCloud Drive / OneDrive が入っている場合は、追加認証なしで今すぐ複数 PC 同期できます。

1. まず検出できる同期フォルダを確認します:
   ```bash
   nihongo-mcp init --detect-sync
   ```
2. 表示されたフォルダを指定して一括登録します（例：Windows の Google Drive）:
   ```bash
   nihongo-mcp init --target all --home "G:\マイドライブ\nihongo"
   ```
3. 同じ同期フォルダを別の PC でも指定すれば、どの PC で承認したルールも自動で揃います。
4. スマホの ChatGPT / Claude アプリからも、チャット入力欄の「＋ → Google Drive からファイルを追加」で `nihongo/profile.md` を選べばそのまま適用できます。

## 方法 B：`GoogleDriveStorage` で Drive API に直接つなぐ（標準ライブラリのみ）

ローカル同期アプリを入れられない環境や、将来のリモート MCP 構成では `nihongo/scripts/gdrive_storage.py` を使えます（追加パッケージ不要）。

1. 自分の Google Cloud プロジェクトで **Google Drive API** を有効化し、OAuth クライアント（デスクトップアプリ）を作成します。
2. スコープは最小権限の `https://www.googleapis.com/auth/drive.file`（`nihongo` が作成したファイルのみアクセス可）または `https://www.googleapis.com/auth/drive.appdata`（非表示領域のみ）を指定します。
3. 取得した認証情報を環境変数に渡します（ファイルや Git には絶対に保存しないこと）:
   - `NIHONGO_GDRIVE_CLIENT_ID`
   - `NIHONGO_GDRIVE_CLIENT_SECRET`
   - `NIHONGO_GDRIVE_REFRESH_TOKEN`
   （短期検証なら `NIHONGO_GDRIVE_ACCESS_TOKEN` だけでも動作します）
4. Python から `NihongoMcpServer(storage=GoogleDriveStorage())` のように差し替えれば、同じ HITL 受信箱・承認ロジックがそのまま Google Drive 上で動きます。

## 分野・案件ごとに別ルールを重ねる（2 層プロファイル）

研究・就活・クライアント案件などフォルダ単位でルールを変えたい場合は、対象フォルダの直下に `.nihongo/profile.md` を 1 枚置くだけで、共通の `profile.md` に自動で重なって適用されます。
