![nihongo — あなたのAIをネイティブに。](assets/nihongo-hero.png)

# nihongo

[![v3.1.0](https://img.shields.io/badge/-v3.1.0-D7261E?style=flat-square)](CHANGELOG.md)
[![stars](https://img.shields.io/github/stars/AnIT012/nihongo?style=flat-square&labelColor=111111&color=D7261E)](https://github.com/AnIT012/nihongo/stargazers)
[![license](https://img.shields.io/badge/license-MIT-D7261E?style=flat-square&labelColor=111111&color=D7261E)](LICENSE)
[![works with](https://img.shields.io/badge/works_with-Claude_%7C_Antigravity_%7C_Codex_%7C_Cursor_%7C_ChatGPT_%7C_Muse-D7261E?style=flat-square&labelColor=111111&color=D7261E)](#インストール)

## 禁止用途

詐欺、フィッシング、なりすまし、相手を騙すための文には使わないでください。ClaudeやChatGPTなど、各AIの利用規約でも禁止されています。

nihongoは、読み手を騙さないことを大事にしています。依頼に無い理由・約束・数字は書かず、発信者も偽りません。

## nihongoとは

### nihongo — AI編集のための日本語ガード

「上出来だけど、そのままでは出せない」をなくす。AI編集の仕上げと確認をまとめて引き受けます。

AIが書いた日本語は一見きれいに見えても、敬語が1段高すぎたり、頼んでいない約束が混ざったり、推敲の拍子に日時や「必ず」が落ちたりします。nihongo v3.0 は、**入れた初日はまず誰でも困りやすい一般的なズレを減らし、使い続けるうちに自分の書き方や避けたい表現を1行ずつ覚えて、手直しを減らしていく**仕組みです。次の3つで仕上げと確認を分担します。

- **軽量スキル（Lite / Full）**：普段のやりとりは短いLite（約1,200字）で、メール・資料・技術文書はFull（約93行＋21本の詳細資料）で書き分けます。依頼に無い事実や約束を足さず、相手と場面に合う日本語に整えます。
- **会話で育つ Personal**：`~/.nihongo/profile.md` に自分の書き方を4つの箱（`[common]` / `[casual]` / `[work]` / `[formal]`）と「絶対に言わない表現」に分けて保存します。会話で直した癖だけを1行確認してから追記し、裏で勝手に書き換えることはありません。
- **0トークン自動チェッカー（`nihongo-check`）**：Python 3.10+ の標準ライブラリだけで動くCLIです。原文と編集後の文を比べ、日時・数字・否定・条件・求める強さ（「必ず」など）のズレや、避けたい表現の混入など**見直す候補**を0トークンで見つけます。Claude Code の Hook や GitHub Actions にもそのまま組み込めます。

## まず試す

**普段の ChatGPT / Claude（Web・アプリ／コマンド不要）**

1. [nihongo/WEB.md](nihongo/WEB.md) を開き、右上のコピーボタンを押す
2. 設定画面の「カスタム指示（ChatGPT）」または「応答の好み（Claude）」にそのまま貼って保存する

普段使いの方はこれだけで始められます（下の CLI・Hook・MCP は開発環境でさらに自動化したい方向けの追加機能です）。

**Claude Code（開発環境）**

```bash
npx skills add AnIT012/nihongo -g -a claude-code
echo '@~/.claude/skills/nihongo/ALWAYS.md' >> ~/.claude/CLAUDE.md
```

1行目でスキルを入れ、2行目でLiteが毎回読み込まれるようにします。ほかの環境での入れ方は[インストール](#インストール)にあります。

## 特徴

禁止語を並べるのではなく、読み手・場面・書き手から、その場の人ならどう書くかを判断します。

- 依頼に無い感想・理由・約束は書き足さず、数字・日付・条件・誰が何をするかは変えない
- お知らせや目上への文は定型の敬語を残し、くだけた癖（`[casual]`）はフォーマルな場面（`[formal]`）に持ち込まない
- 要らない読点を打たずに書く（今日は、駅で → 今日は駅で）
- 自然な文は無理に直さない
- 編集後の確認はAIに頼み直さず、0トークンの `nihongo-check` で意味のズレを機械的に検出し、必要に応じて原文へ戻せる

## 使用例

### 1. Slackの投稿を整える（スキル）

AIが書いたSlackの投稿です。

```
@channel お疲れさまです！

本日のデプロイについて共有させていただきます🚀

**結論**：本日18時のリリースは予定どおり実施します。

**背景**：昨日発見された決済画面の不具合は、すでに修正済みであり、ステージング環境での検証も完了しております。

**お願い**：18時〜18時30分の間は、本番環境への変更を控えていただけますと幸いです。

ご不明点等ございましたら、お気軽にスレッドにてお知らせください！引き続きよろしくお願いいたします🙏
```

nihongoで直すと、こうなりました。

```
@channel お疲れさまです！
本日18時のリリースは予定どおり実施します🚀

昨日見つかった決済画面の不具合は修正済みで、ステージング環境での検証も完了しています。

**18時〜18時30分は、本番環境への変更を控えてください。**

不明点があればスレッドでお知らせください。よろしくお願いします🙏
```

「結論：」「背景：」のようなラベルを外し、社内のチャットには重すぎる「させていただきます」「いただけますと幸いです」をチームに向けた普通の言い方にしています。日時やお願いの中身は変えていません。

### 2. AI編集後の意味ズレを0トークンで止める（`nihongo-check git --hook`）

たとえば `docs/release.md` の原文にあった「15時までに必ず確認してください。」が、AIによる文章整理で「16時までに確認してください。」に変わったとします。

[examples/hooks/claude-code-hook.json](examples/hooks/claude-code-hook.json) を設定しておくと、ファイルの編集直後に0トークンで `nihongo-check git --hook` が走り、ズレがあれば終了コード `2` で止めて該当箇所を返します。

```text
nihongo-check: 意味が変わった可能性がある箇所を検出しました（base: HEAD）
[docs/release.md] (4件)
- [数値・日時] 削除（原文のみ）: 15時
- [数値・日時] 追加（編集後のみ）: 16時
- [確度・必須度] 「必須」表現が減少（1→0）
- [程度・約束] 「必ず」が減少（1→0）
原文と読み比べ、意図しない変更があれば元に戻してください。
```

AIのトークンを使わずに、時刻の書き換わりや「必ず」の脱落をその場で拾えます。

### 3. 会話で育つ Personal（`~/.nihongo/profile.md`）

自分の名前で出す文（LINE・Slack・メール・SNSなど）を自分の書き方に寄せる機能です。設定ファイルはホーム配下の `~/.nihongo/profile.md` に置き、4つの箱と「絶対に言わない表現」に分けて管理します。

```markdown
## [common]
- 結論を1文目に書く
- 絶対に言わない表現：〜させていただきます / ご査収のほど

## [casual]
- 一人称：僕
- 友達への返事は短めに返す

## [work]
- 了解の返事は「了解です」にする

## [formal]
- 一人称：私
- 先生・社外向けは標準的な敬語を保つ
```

会話の中でユーザーが言い回しを直した時だけ、AIが返答の末尾で1行確認します。

```text
今後 `[work]` に「了解の返事は『了解です』にする」を追記しておきますか？
```

- 裏で勝手に書き込むことはせず、本人がOKした内容だけを追記します
- ファイルは普通のMarkdownなので、いつでも中身を見たり消したりできます
- `[casual]` の癖は `[formal]` には持ち込みません
- 個人情報や固有名詞（人名・社名・連絡先など）は書きません
- これまでどおり、自分が送った文を3〜5通貼って「私の書き方を覚えて」と頼み、まとめて作ることもできます
- `nihongo-check` に `--profile ~/.nihongo/profile.md`（フォーマル文書なら `--scene formal` も追加）を渡せば、「絶対に言わない表現」の混入も0トークンで検出できます

## LiteとFull

nihongoには、毎回読み込む短いLiteと、詳しい手順が入ったFullがあります。両方入れておけば、普段はLiteだけを使い、人に出す文章を書く時だけFullまで読みます。v3.0ではLite・Fullともにv2.3.2から半分以下に軽量化しました。

| | Lite | Full |
|---|---|---|
| ファイル | `nihongo/ALWAYS.md` | `nihongo/SKILL.md` と `references/`（21本） |
| 使う場面 | 普段の返事、雑談、短い質問 | メール、お知らせ、ES、資料、README、UIの文言 |
| 読み込まれ方 | 設定に入れておけば毎回 | 人に出す文章を書く時に自動で。名前を出して呼ぶこともできる |
| サイズ（目安） | 約1,200字（v2.3.2 の 2,704字から約55%軽量化） | 約93行・約5,675字（v2.3.2 の 275行・12,819字から約56%軽量化。該当する `references/` のみ追加読み込み） |

## インストール

スキルを入れて、Liteを毎回読み込まれる場所に置きます。使う環境を開いてください。

<details>
<summary><b>Claude Code</b></summary>

```bash
npx skills add AnIT012/nihongo -g -a claude-code
echo '@~/.claude/skills/nihongo/ALWAYS.md' >> ~/.claude/CLAUDE.md
```

`-a claude-code` を付けないと入れ先を聞かれるので、Claude Code をスペースキーで選んでください。プロジェクトだけに入れた場合は、プロジェクトの `CLAUDE.md` に `@.claude/skills/nihongo/ALWAYS.md` と書きます。

</details>

<details>
<summary><b>Antigravity</b></summary>

[最新のリリース](https://github.com/AnIT012/nihongo/releases/latest)から `nihongo-v3.1.0.zip` を落として展開するか、このリポジトリの `nihongo/` フォルダを `~/.gemini/config/skills/nihongo/` に配置します。

```bash
git clone --depth 1 --branch v3.1.0 https://github.com/AnIT012/nihongo.git /tmp/nihongo-src
mkdir -p ~/.gemini/config/skills
cp -r /tmp/nihongo-src/nihongo ~/.gemini/config/skills/nihongo
```

Windows（PowerShell）では、同じように `nihongo` フォルダを `%USERPROFILE%\.gemini\config\skills\nihongo\` に置きます。Liteを毎回効かせたい場合は、`ALWAYS.md` の内容をユーザー共通ルールに入れてください。

</details>

<details>
<summary><b>Codex</b></summary>

```bash
npx skills add AnIT012/nihongo -g
```

入れ先を聞かれたら Codex を選びます。Liteを入れるには、`ALWAYS.md` の中身を `~/.codex/AGENTS.md` かプロジェクトの `AGENTS.md` にそのまま貼ってください。

</details>

<details>
<summary><b>Cursor</b></summary>

```bash
npx skills add AnIT012/nihongo -g
```

入れ先を聞かれたら Cursor を選びます。Liteを毎回効かせるには、`ALWAYS.md` の中身を Cursor の User Rules、またはプロジェクトの `.cursor/rules/nihongo.mdc`（`alwaysApply: true`）に貼ってください。

</details>

<details>
<summary><b>Muse</b></summary>

`nihongo/` フォルダをスキルの置き場に置くと、スキルとして読み込めたと報告をいただきました（Issue #15）。`npx skills add` で入れたスキルも、そのまま見えるはずです。Liteを入れるには、`ALWAYS.md` の中身を `AGENTS.md` に貼ってください。

</details>

<details>
<summary><b>Claude / ChatGPT アプリ（コマンド不要）</b></summary>

- **いちばん簡単（Web版）**：[nihongo/WEB.md](nihongo/WEB.md) を開いて右上のコピーボタンを押し、ChatGPT の「設定 → パーソナライズ → カスタム指示」または Claude の「設定 → プロフィール → 応答の好み」に貼って保存します（無料プランでも使えます）。
- **メール・資料・ES まで本格的に使う（Full）**：[最新のリリース](https://github.com/AnIT012/nihongo/releases/latest)から `nihongo-v3.1.0.zip` をダウンロードします。
  - **Claude（Web / デスクトップアプリ）**：設定のスキル画面から `nihongo-v3.1.0.zip` をそのままアップロード（または解凍してプロジェクトのナレッジに追加）します。
  - **ChatGPT**：My GPTs のナレッジに解凍したファイルを追加します（Skills 画面が使える環境では `nihongo-v3.1.0.zip` をそのままアップロードできます）。
- ※GitHub トップの緑色の「Code → Download ZIP」はフォルダ構造が1段深いため、そのままではアップロードできません。必ず上の最新リリースページにある `nihongo-v3.1.0.zip` を使ってください。
- Web / スマホ版で自分の書き方を1行ずつ育てたい時は、言い回しを直したあとに「設定欄にそのまま足せる1行を作って」と頼めば、ファイル保存や MCP なしでもカスタム指示に1行足すだけで育てられます。

</details>

### 使い方と更新

メールや資料を書く時はFullが自動で使われます。ほかの場面では「nihongoで直して」と頼むか、Claude Codeなら `/nihongo` と送ってください。更新は `npx skills update nihongo -g` です。

### 会話の途中から使う

- **Claude Code**：スキルを入れると、再起動しなくても今の会話で使えます。会話を始めた時に `~/.claude/skills/` が無かった場合は、先に `/reload-skills` を実行してください。Liteをその場で効かせたい時は、`@~/.claude/skills/nihongo/ALWAYS.md` をメッセージに書いて読み込ませます。
- **Claudeのアプリ**：「nihongoのスキルを使って」と名前を出して頼むと、使われやすくなります。途中の会話で効かない時は、新しい会話で始めてください。

### 自動チェッカー（`nihongo-check` / Hook / GitHub Actions）

Python 3.10+ の標準ライブラリだけで動き、追加の依存パッケージは要りません。

```bash
pip install "git+https://github.com/AnIT012/nihongo.git@v3.1.0"
```

pip で入れると `nihongo-check` コマンド（`nihongo_check` 名前空間）が使えるようになります。インストールせずに、スキル内の `python3 nihongo/scripts/cli.py` をそのまま実行することもできます。

| コマンド | できること |
|---|---|
| `nihongo-check diff <orig> <draft> [--request <req>] [--profile <path>\|--auto-profile] [--scene formal] [--json]` | 原文と直した文を比べ、意味のズレやプロフィール違反の候補を出す |
| `nihongo-check fix <orig> <draft> <out> [--request <req>] [--no-trim-commas] [--fail-on-remaining]` | 意味が変わった文を原文に戻し、要らない読点を外す |
| `nihongo-check git [--base HEAD] [--staged] [--ext .md,.txt] [--request <req>] [--profile <path>\|--auto-profile] [--scene formal] [--hook] [--json]` | git の変更差分（Markdown・テキスト）をまとめて確認する |
| `nihongo-check doctor [--json]` | 導入状況・`profile.md`（2層）・MCP 接続・クラウド同期フォルダをまとめて診断する |

そのまま使える設定例を `examples/hooks/` に置いています。

- **Claude Code Hook**：[examples/hooks/claude-code-hook.json](examples/hooks/claude-code-hook.json) — `PostToolUse`（`Edit|Write`）で0トークン実行し、意味のズレ候補があれば終了コード `2` で通知します。
- **GitHub Actions**：[examples/hooks/github-actions-docs-check.yml](examples/hooks/github-actions-docs-check.yml) — PR で変更した Markdown ファイルに意図しない意味のズレがないか自動で確かめます。

### Personal を育てる HITL 受信箱（`inbox`）と MCP 連携（`nihongo-mcp`）

普段使いの Chat（Claude Desktop・Cursor・Claude Code など）で直した言い回しを環境に縛られず資産化するため、**「候補を拾うのは自動、反映は本人承認（HITL）」** の受信箱とローカル MCP サーバーを用意しています（Python 3.10+ 標準ライブラリのみ、追加依存ゼロ）。

- **受信箱（`~/.nihongo/inbox.jsonl`）**：`propose` は一時置き場に追記候補を溜めるだけで、`~/.nihongo/profile.md` 本体は書き換えません。
- **本人承認（HITL）**：`nihongo-check inbox review`（または `approve`）で承認した候補だけが `~/.nihongo/profile.md`（唯一の正）へ反映されます。個人情報（メール・電話番号・APIキー等）の自動拒否と、`[formal]` 場面への崩し混入ガード付きです。
- **MCP サーバー（`nihongo-mcp` / `python3 nihongo/scripts/mcp_server.py`）**：どの MCP 対応ツールからでも `get_profile`・`propose_profile_entry`・`list_inbox`・`review_inbox_entry`（`confirmed_by_user: true` 必須）・`remove_profile_forbidden`（NG表現の削除・本人確認必須）・`check_meaning_diff`（0トークン意味ズレ検査）を直接呼べます。チャットで「今のルール見せて」「承認待ちある？」と聞くだけで確認・承認・削除まで完結します。設定例は [examples/mcp/](examples/mcp/) にあります。

| コマンド（手動操作したい時だけ） | できること |
|---|---|
| `nihongo-mcp init --target all [--home <同期フォルダ>]` | PC 内の AI アプリへ自動登録する（`--detect-sync` で Google Drive / Dropbox / iCloud / OneDrive フォルダを検出） |
| `nihongo-check inbox list` / `review` | 承認待ち候補の一覧表示、またはターミナルからの対話承認・却下（`--strict-hitl` 運用時） |
| `nihongo-check inbox propose` / `approve` / `reject` | 候補の手動追加・ID指定での承認（`--dry-run` 対応）・却下 |
| `nihongo-check profile show [--scene formal] [--project <dir>]` | 現在の `profile.md`（作業フォルダの `.nihongo/profile.md` 2層マージ対応）と保留件数を表示する |
| `nihongo-check profile init [--project] [--force]` | グローバルまたは作業フォルダ専用の `profile.md` 雛形を作成する |
| `nihongo-mcp`（または `python3 nihongo/scripts/mcp_server.py`） | stdio 経由のローカル MCP サーバーを起動する |

## 評価

v2.2.0 時点の基準結果です（v3.0.0 での再計測は未実施）。推敲用に作られた別のスキル（当時最新版）と同じ10題で比べ、別のAIが目隠しで判定しました。依頼どおりかを最優先に見ています。

| 見た点 | 結果（v2.2.0） |
|---|---|
| 依頼どおりか（頼んだ中身がそろい、本人の経験や約束を作っていないか） | 2回の審査とも、LiteとFullの両方でnihongoが勝ち越し |
| 依頼に無い事実を作った案 | nihongoは0件。作ったのは別のスキルだけ |
| 自然さ | 2回の審査とも、別のスキルが勝ち越し |
| 10題を書いた時に増えたトークン | Fullは約1.9万、別のスキルは約4.1万 |

判定したのは作者か同じ会社のAIなので、数字は目安として見てください。版ごとの結果と課題の原文は [evaluations/](evaluations/) にあります。

## 変更履歴

各版の変更点は [CHANGELOG.md](CHANGELOG.md) にあります。

## 注意事項

スキル部分はAIが手順を読んで判断する作りなので、同じ依頼でも毎回同じ文になるとは限りません。`nihongo-check` の検出結果も「見直す候補」を出すものであり、最終的な数字・日付・固有名詞は送る前に自分の目で確認してください。

## 制作について

Claude（Anthropic）と一緒に作りました。方針を決め、ルールの一部を書き、目隠しの判定で採用するかを決めたのは作者です。

## チーム・企業での導入相談

自社専用の日本語ルール設計や社内AIへの導入・同期についてのご相談は、[お問い合わせフォーム](https://docs.google.com/forms/d/e/1FAIpQLSdub3SihSvTguflQWWttOQUnLvWf_QerZ4r2SNfMO4tYD6ACg/viewform)または [X (@sincostansinhk)](https://x.com/sincostansinhk) のDMからご連絡ください。

## ライセンス

MIT Licenseで、詳しくは `LICENSE` に書いてあります。
