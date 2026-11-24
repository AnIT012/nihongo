#!/usr/bin/env python3
"""nihongo の個人プロフィール・HITL 受信箱・0トークン意味ズレ検査を提供する標準ライブラリ製 MCP サーバー。

使い方:
    python3 nihongo/scripts/mcp_server.py
    nihongo-mcp

設計原則:
- 外部パッケージ依存ゼロ（Python 3.10+ 標準ライブラリのみで JSON-RPC 2.0 / MCP over stdio を実装）。
- `~/.nihongo/profile.md` を唯一の正（Single Source of Truth）として読み取る。
- `propose_profile_entry` は受信箱（`inbox.jsonl`）に追記候補を溜めるだけで、`profile.md` は書き換えない。
- `review_inbox_entry` の承認（approve）は `confirmed_by_user: true` が明示されない限り `profile.md` へ書き込まない（HITL）。
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import shutil
import sys
from typing import Any, BinaryIO

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

SERVER_NAME = "nihongo-mcp"
SERVER_VERSION = cli_mod.__version__
DEFAULT_PROTOCOL_VERSION = "2025-03-26"

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

SERVER_INSTRUCTIONS_BASE = (
    "nihongo の個人プロフィール（profile.md）と HITL 受信箱（inbox）、"
    "0トークン意味ズレ検査を提供するローカル MCP サーバーです。\n"
    "【いつ使うか（積極トリガー）】\n"
    "- 本人名義のメール・チャット・記事・ES 等を書く／直す前に get_profile(scene=...) で自分の書き方を確認する。\n"
    "- 社外メールや重要文書の推敲後に check_meaning_diff(orig, draft, scene=...) で0トークン検品する"
    "（1から新規作成した文を検品する時は、雑な依頼文を orig に入れず orig='' で呼ぶと NG 表現と場面ガードだけを綺麗に検査できる）。\n"
    "【HITL 受信箱の運用ルール（UX 保護）】\n"
    "1. ユーザーが AI に向かって打った雑な指示文・誤字・タイポ・その場限りの内容変更からは絶対に学習候補を拾わないこと。\n"
    "2. propose_profile_entry を呼んでよいのは、外に出す成果物に対する修正のうち、"
    "(a) 明示的な NG 表現宣言（例：「ご査収のほどは使わない」→ 1回で静かに inbox へ積む。value には短い語句そのものだけを渡す）、"
    "(b) 同一会話内で同じトーン修正が2回出た時または「覚えておいて」と明示された時、の2条件だけ。\n"
    "3. inbox に積んだ時は会話の流れを止めず、返答の末尾に1行だけ静かに知らせる（その場で承認を迫らない）。\n"
    "4. ユーザーから「今のルール見せて」「私の書き方どうなってる？」と聞かれたら get_profile を呼び、"
    "返ってきた display_markdown をそのまま分かりやすく出力する。「承認待ちある？」「受信箱見せて」と聞かれたら "
    "list_inbox を呼び、display_markdown の番号と日本語ラベルを使って簡潔に見せ、「1と2だけOK、3は却下」のような返答でまとめて捌く。\n"
)

SERVER_INSTRUCTIONS_CHAT_APPROVE = (
    "5. profile.md は絶対に直接書き換えず、本人の明示承認後に "
    "review_inbox_entry(confirmed_by_user=true) でのみ反映する（承認と却下が混ざる時は action='batch' で1回にまとめる）。"
    "登録済みのNG表現を消してほしいと頼まれた時は、対象を確認したうえで remove_profile_forbidden(confirmed_by_user=true) を使う。"
)

SERVER_INSTRUCTIONS_STRICT = (
    "5. --strict-hitl モードのため MCP 経由の承認・却下・削除は無効です。"
    "反映する時はターミナルで `nihongo-check inbox review` を実行するよう案内してください。"
)

SERVER_INSTRUCTIONS = SERVER_INSTRUCTIONS_BASE + SERVER_INSTRUCTIONS_CHAT_APPROVE

TOOLS_SPEC: list[dict[str, Any]] = [
    {
        "name": "get_profile",
        "description": (
            "~/.nihongo/profile.md（唯一の正）を読み取り、場面別の書き方・絶対に言わない表現（Anti-Voice）・"
            "保留中の inbox 候補件数を返します。どの Chat 環境からでも同じ個人プロフィールを参照できます。"
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "scene": {
                    "type": "string",
                    "enum": list(inbox_mod.VALID_SCENES),
                    "description": "特定場面のみ返す場合に指定（common / casual / work / formal）。省略時は全文を返す。",
                },
                "project_dir": {
                    "type": "string",
                    "description": "作業フォルダのパス。フォルダ内に .nihongo/profile.md があれば共通プロフィールへ2層マージして返す（任意）。",
                },
            },
            "additionalProperties": False,
        },
        "annotations": {
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    },
    {
        "name": "propose_profile_entry",
        "description": (
            "外向けの成果物（メール・チャット・記事・ES等）に対するユーザーの修正から、"
            "追記候補を受信箱（inbox）に保留（pending）として保存します。profile.md 本体は一切書き換えません（HITL 原則）。"
            "AIへの雑な指示文・誤字・タイポ・その場限りの修正からは絶対に呼ばないでください。"
            "呼んでよいのは「明示的なNG表現宣言」か「同じトーン修正が2回出た時／覚えておいてと言われた時」だけです。"
            "実名・社名・メールアドレス・電話番号などの個人情報は含めないでください。"
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "scene": {
                    "type": "string",
                    "enum": list(inbox_mod.VALID_SCENES),
                    "description": "適用する場面（common=全場面共通 / casual=友達・雑談 / work=社内・同僚 / formal=社外・目上・公式）",
                },
                "kind": {
                    "type": "string",
                    "enum": list(inbox_mod.VALID_KINDS),
                    "description": "種類（forbidden=絶対に言わない表現 / rule=書く時の考え方 / tone=口調・記号 / first_person=一人称）",
                },
                "value": {
                    "type": "string",
                    "description": "追記したい表現やルール（1行で簡潔に。個人情報を含めないこと）",
                },
                "reason": {
                    "type": "string",
                    "description": "どの修正から拾ったかの短い根拠メモ（任意）",
                },
                "example_before": {
                    "type": "string",
                    "description": "修正前の文例（個人情報を含めない短い抜粋・任意）",
                },
                "example_after": {
                    "type": "string",
                    "description": "修正後の文例（個人情報を含めない短い抜粋・任意）",
                },
                "source": {
                    "type": "string",
                    "description": "収集元アプリ名（例: claude-desktop, chatgpt, cursor, claude-code）",
                },
            },
            "required": ["scene", "kind", "value"],
            "additionalProperties": False,
        },
        "annotations": {
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    },
    {
        "name": "list_inbox",
        "description": (
            "受信箱（~/.nihongo/inbox.jsonl）に溜まっている追記候補を一覧表示します。"
            "既定では本人承認待ち（pending）の候補だけを返します。"
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "enum": ["pending", "approved", "rejected", "all"],
                    "default": "pending",
                    "description": "絞り込む状態（既定: pending）",
                },
                "scene": {
                    "type": "string",
                    "enum": list(inbox_mod.VALID_SCENES),
                    "description": "特定場面で絞り込む場合に指定（任意）",
                },
            },
            "additionalProperties": False,
        },
        "annotations": {
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    },
    {
        "name": "review_inbox_entry",
        "description": (
            "受信箱（inbox）の保留候補を承認（approve）・却下（reject）・一括混在処理（batch）します。"
            "「1と2だけOK、3は却下」のように承認と却下が混ざる時は action='batch' で approve_ids と reject_ids を1回で渡せます。"
            "いずれの操作も本人の明示確認を得た上で confirmed_by_user: true を指定する必要があります"
            "（false または省略時はドライラン確認のみ行い profile.md も inbox も変更しません）。"
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["approve", "reject", "batch"],
                    "description": "approve（承認）/ reject（却下）/ batch（承認と却下を1回でまとめて実行）",
                },
                "ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "action=approve または reject 時の対象候補 ID の配列",
                },
                "approve_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "action=batch 時に承認する候補 ID の配列",
                },
                "reject_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "action=batch 時に却下する候補 ID の配列",
                },
                "approve_all": {
                    "type": "boolean",
                    "default": False,
                    "description": "action=approve 時、保留中の全候補を対象にする場合 true",
                },
                "confirmed_by_user": {
                    "type": "boolean",
                    "default": False,
                    "description": "本人から明示的な確認を得た場合のみ true（HITL 安全弁）",
                },
                "force": {
                    "type": "boolean",
                    "default": False,
                    "description": "[formal] 場面ガード警告がある候補も本人確認のうえで反映する場合 true",
                },
                "reason": {
                    "type": "string",
                    "description": "却下時の理由メモ（任意）",
                },
            },
            "required": ["action"],
            "additionalProperties": False,
        },
        "annotations": {
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": False,
            "openWorldHint": False,
        },
    },
    {
        "name": "remove_profile_forbidden",
        "description": (
            "~/.nihongo/profile.md に登録済みの「絶対に言わない表現（NG表現）」から指定した1語を削除します。"
            "本人の明示確認を得た上で confirmed_by_user: true を指定する必要があります"
            "（false または省略時はドライラン確認のみ行い profile.md は変更しません）。"
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "scene": {
                    "type": "string",
                    "enum": list(inbox_mod.VALID_SCENES),
                    "description": "削除対象の場面（common / casual / work / formal）",
                },
                "value": {
                    "type": "string",
                    "description": "削除するNG表現（かぎ括弧なしでも可）",
                },
                "confirmed_by_user": {
                    "type": "boolean",
                    "default": False,
                    "description": "本人から明示的な削除確認を得た場合のみ true（HITL 安全弁）",
                },
            },
            "required": ["scene", "value"],
            "additionalProperties": False,
        },
        "annotations": {
            "readOnlyHint": False,
            "destructiveHint": True,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    },
    {
        "name": "check_meaning_diff",
        "description": (
            "原文（orig）とAI編集後の文（draft）を比較し、数値・日時・否定・約束の強さ（必ず等）のズレと、"
            "~/.nihongo/profile.md の「絶対に言わない表現」違反・formal場面ガード違反をローカル（0トークン）で検出します。"
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "orig": {
                    "type": "string",
                    "description": "編集前の原文",
                },
                "draft": {
                    "type": "string",
                    "description": "AI が編集・推敲した後の文",
                },
                "request": {
                    "type": "string",
                    "description": "ユーザーからの編集依頼文（意図的な変更を除外するため・任意）",
                },
                "scene": {
                    "type": "string",
                    "enum": ["casual", "work", "formal"],
                    "description": "文章の場面（formal 指定時は崩し表現ガードも検査・任意）",
                },
                "check_commas": {
                    "type": "boolean",
                    "default": False,
                    "description": "true の場合、trim_commas.py による不要読点の整理案も併せて返す",
                },
                "project_dir": {
                    "type": "string",
                    "description": "作業フォルダのパス。フォルダ内に .nihongo/profile.md があれば共通ルールと合算して検査する（任意）。",
                },
            },
            "required": ["orig", "draft"],
            "additionalProperties": False,
        },
        "annotations": {
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    },
]

RESOURCES_SPEC: list[dict[str, Any]] = [
    {
        "uri": "nihongo://profile",
        "name": "Personal Writing Profile",
        "description": "唯一の正である個人プロフィール（~/.nihongo/profile.md）の現在内容",
        "mimeType": "text/markdown",
    },
    {
        "uri": "nihongo://inbox/pending",
        "name": "Pending Profile Inbox",
        "description": "本人承認待ち（pending）のプロフィール追記候補一覧（~/.nihongo/inbox.jsonl）",
        "mimeType": "application/json",
    },
]


class NihongoMcpServer:
    """状態を持たない純粋な JSON-RPC 2.0 ハンドラ（テストや将来のリモート HTTP 窓口から直接呼び出し可能）。"""

    def __init__(
        self,
        *,
        home: str | None = None,
        profile_path: str | None = None,
        inbox_path: str | None = None,
        storage: inbox_mod.ProfileStorage | None = None,
        strict_hitl: bool = False,
    ) -> None:
        self.storage: inbox_mod.ProfileStorage = (
            storage
            if storage is not None
            else inbox_mod.LocalFileStorage(
                home=home,
                profile_path=profile_path,
                inbox_path=inbox_path,
            )
        )
        self.profile_path = self.storage.profile_location
        self.inbox_path = self.storage.inbox_location
        self.strict_hitl = strict_hitl

    def _exposed_tools(self) -> list[dict[str, Any]]:
        if self.strict_hitl:
            return [t for t in TOOLS_SPEC if t["name"] not in ("review_inbox_entry", "remove_profile_forbidden")]
        return list(TOOLS_SPEC)

    def _instructions(self) -> str:
        tail = SERVER_INSTRUCTIONS_STRICT if self.strict_hitl else SERVER_INSTRUCTIONS_CHAT_APPROVE
        return SERVER_INSTRUCTIONS_BASE + tail

    def _tool_get_profile(self, args: dict[str, Any]) -> dict[str, Any]:
        scene = args.get("scene")
        raw_proj = args.get("project_dir")
        if raw_proj is not None and not isinstance(raw_proj, str):
            raise ValueError("project_dir は文字列で指定してください。")
        project_dir = raw_proj.strip() if isinstance(raw_proj, str) else None
        project_dir = project_dir or None
        info = inbox_mod.read_profile(
            storage=self.storage,
            scene=scene,
            project_dir=project_dir,
            include_project=bool(project_dir),
        )
        forbidden: list[str] = []
        if info["exists"]:
            forbidden = cli_mod.parse_profile_text(info["raw"], scene=scene)
        info["forbidden"] = forbidden
        info["structured"] = inbox_mod.parse_profile_structured(info["raw"]) if info["exists"] else {}
        info["display_markdown"] = inbox_mod.format_profile_summary(info)
        info["strict_hitl"] = self.strict_hitl
        if not info["exists"]:
            info["onboarding_hint"] = (
                "まだ個人プロフィールは未作成です。普段どおり文章を直していけば、"
                "NG表現の宣言などから受信箱（inbox）経由で少しずつ育てられます。"
            )
        return info

    def _tool_propose_profile_entry(self, args: dict[str, Any]) -> dict[str, Any]:
        return inbox_mod.propose_entry(
            scene=str(args.get("scene") or ""),
            kind=str(args.get("kind") or ""),
            value=str(args.get("value") or ""),
            reason=str(args.get("reason") or ""),
            example_before=str(args.get("example_before") or ""),
            example_after=str(args.get("example_after") or ""),
            source=str(args.get("source") or "mcp"),
            storage=self.storage,
        )

    def _tool_list_inbox(self, args: dict[str, Any]) -> dict[str, Any]:
        status = args.get("status", "pending")
        scene = args.get("scene")
        raw_items = inbox_mod.list_inbox(
            status=status,
            scene=scene,
            storage=self.storage,
        )
        enriched: list[dict[str, Any]] = []
        for idx, item in enumerate(raw_items, 1):
            sc = str(item.get("scene", "common"))
            kd = str(item.get("kind", "rule"))
            sc_label = _SCENE_LABELS.get(sc, sc)
            kd_label = _KIND_LABELS.get(kd, kd)
            copy_item = dict(item)
            copy_item["index"] = idx
            copy_item["scene_label"] = sc_label
            copy_item["kind_label"] = kd_label
            copy_item["display_line"] = f"{idx}. [{sc_label} / {kd_label}] {item.get('value', '')}"
            enriched.append(copy_item)

        if not enriched:
            display_md = "承認待ちの候補はありません。" if status == "pending" else "該当する履歴はありません。"
        else:
            md_lines = [f"### 承認待ちの候補（{len(enriched)}件）" if status == "pending" else f"### 受信箱一覧（{len(enriched)}件）"]
            for it in enriched:
                line = it["display_line"]
                if it.get("reason"):
                    line += f" — {it['reason']}"
                md_lines.append(line)
                if it.get("warning"):
                    md_lines.append(f"   - 注意: {it['warning']}")
            if status == "pending":
                if self.strict_hitl:
                    md_lines.append("\n（--strict-hitl 有効中のため、ターミナルで `nihongo-check inbox review` から反映してください）")
                else:
                    md_lines.append("\n「全部承認」「1と2だけ承認、3は却下」のように返信するだけで反映できます。")
            display_md = "\n".join(md_lines)

        return {
            "status_filter": status,
            "scene_filter": scene,
            "count": len(enriched),
            "items": enriched,
            "display_markdown": display_md,
            "strict_hitl": self.strict_hitl,
        }

    def _tool_review_inbox_entry(self, args: dict[str, Any]) -> dict[str, Any]:
        if self.strict_hitl:
            raise PermissionError(
                "--strict-hitl が有効なため、MCP 経由での承認・却下は無効です。"
                "ターミナルで `nihongo-check inbox review` を実行してください。"
            )
        action = str(args.get("action") or "").strip().lower()
        confirmed = args.get("confirmed_by_user") is True
        force = args.get("force") is True

        if action == "batch":
            raw_approve = args.get("approve_ids")
            raw_reject = args.get("reject_ids")
            if raw_approve is not None and not isinstance(raw_approve, list):
                raise ValueError("approve_ids は文字列の配列で指定してください。")
            if raw_reject is not None and not isinstance(raw_reject, list):
                raise ValueError("reject_ids は文字列の配列で指定してください。")
            approve_ids = [str(x) for x in (raw_approve or [])]
            reject_ids = [str(x) for x in (raw_reject or [])]
            if not approve_ids and not reject_ids:
                raise ValueError("action='batch' では approve_ids または reject_ids を1件以上指定してください。")
            if not confirmed:
                preview = (
                    inbox_mod.approve_entries(
                        approve_ids,
                        dry_run=True,
                        force=force,
                        storage=self.storage,
                    )
                    if approve_ids
                    else None
                )
                return {
                    "action": "batch",
                    "dry_run": True,
                    "requires_user_confirmation": True,
                    "approve_ids": approve_ids,
                    "reject_ids": reject_ids,
                    "approve_preview": preview,
                    "message": (
                        "HITL 保護のため一括反映を保留しました。対象候補をユーザーに確認したうえで "
                        "confirmed_by_user=true を指定して再実行してください。"
                    ),
                }
            reason_str = str(args.get("reason") or "")
            if reject_ids and reason_str:
                pii_err = inbox_mod._check_pii([inbox_mod._normalize_value(reason_str)])
                if pii_err:
                    raise ValueError(pii_err)
            appr_res = (
                inbox_mod.approve_entries(
                    approve_ids,
                    dry_run=False,
                    force=force,
                    storage=self.storage,
                )
                if approve_ids
                else {"approved_count": 0, "profile_updated": False, "results": []}
            )
            rej_res = (
                inbox_mod.reject_entries(
                    reject_ids,
                    reason=reason_str,
                    storage=self.storage,
                )
                if reject_ids
                else {"rejected_count": 0, "results": []}
            )
            return {
                "action": "batch",
                "dry_run": False,
                "approved_count": appr_res["approved_count"],
                "rejected_count": rej_res["rejected_count"],
                "profile_updated": appr_res["profile_updated"],
                "approve": appr_res,
                "reject": rej_res,
            }

        ids = args.get("ids") or []
        if not isinstance(ids, list):
            raise ValueError("ids は文字列の配列で指定してください。")
        str_ids = [str(x) for x in ids]

        if action == "reject":
            if not confirmed:
                return {
                    "action": "reject",
                    "dry_run": True,
                    "requires_user_confirmation": True,
                    "ids": str_ids,
                    "message": (
                        "HITL 保護のため却下を保留しました。ユーザーの確認を得たうえで "
                        "confirmed_by_user=true を指定して再実行してください。"
                    ),
                }
            return inbox_mod.reject_entries(
                str_ids,
                reason=str(args.get("reason") or ""),
                storage=self.storage,
            )

        if action == "approve":
            approve_all = args.get("approve_all") is True

            if not confirmed:
                # HITL 安全弁: 本人確認フラグが無ければ dry-run プレビューのみ返す
                preview = inbox_mod.approve_entries(
                    str_ids,
                    approve_all=approve_all,
                    dry_run=True,
                    force=force,
                    storage=self.storage,
                )
                preview["requires_user_confirmation"] = True
                preview["message"] = (
                    "HITL 保護のため profile.md への書き込みを保留しました。"
                    "対象候補の内容をユーザーに提示し、明示的な承認を得たうえで "
                    "confirmed_by_user=true を指定して再実行してください。"
                )
                return preview

            return inbox_mod.approve_entries(
                str_ids,
                approve_all=approve_all,
                dry_run=False,
                force=force,
                storage=self.storage,
            )

        raise ValueError(f"不正な action です: {action!r}（approve / reject / batch を指定）")

    def _tool_check_meaning_diff(self, args: dict[str, Any]) -> dict[str, Any]:
        orig = str(args.get("orig") or "")
        draft = str(args.get("draft") or "")
        request = str(args.get("request") or "")
        scene = args.get("scene")
        check_commas = args.get("check_commas") is True
        raw_proj = args.get("project_dir")
        if raw_proj is not None and not isinstance(raw_proj, str):
            raise ValueError("project_dir は文字列で指定してください。")
        project_dir = raw_proj.strip() if isinstance(raw_proj, str) else None
        project_dir = project_dir or None

        prof_info = inbox_mod.read_profile(
            storage=self.storage,
            project_dir=project_dir,
            include_project=bool(project_dir),
        )
        forbidden: list[str] = []
        if prof_info["exists"]:
            forbidden = cli_mod.parse_profile_text(prof_info["raw"], scene=scene)

        findings = revert_broken.remaining(orig, draft, request) if orig.strip() else []
        if forbidden or scene:
            findings = findings + cli_mod.check_profile_drift(orig, draft, forbidden, scene=scene)
        formatted = [cli_mod._format_finding(x) for x in findings]

        result: dict[str, Any] = {
            "clean": len(formatted) == 0,
            "count": len(formatted),
            "findings": formatted,
            "profile_used": prof_info["exists"],
            "layers": prof_info["layers"],
            "scene": scene,
        }
        if check_commas:
            trimmed, comma_logs = trim_commas.trim(draft)
            result["comma_trim_count"] = len(comma_logs)
            result["comma_trim_logs"] = comma_logs
            result["comma_trimmed_text"] = trimmed
        return result

    def _tool_remove_profile_forbidden(self, args: dict[str, Any]) -> dict[str, Any]:
        if self.strict_hitl:
            raise PermissionError(
                "--strict-hitl が有効なため、MCP 経由でのプロフィール削除は無効です。"
                "ローカルの profile.md を直接編集してください。"
            )
        scene = str(args.get("scene") or "").strip().lower()
        value = str(args.get("value") or "").strip()
        if scene not in inbox_mod.VALID_SCENES:
            raise ValueError(f"不正な scene です: {scene!r}")
        if not value:
            raise ValueError("削除するNG表現を指定してください。")
        confirmed = args.get("confirmed_by_user") is True
        if not confirmed:
            return {
                "dry_run": True,
                "requires_user_confirmation": True,
                "scene": scene,
                "scene_label": _SCENE_LABELS.get(scene, scene),
                "value": value,
                "message": (
                    f"HITL 保護のため削除を保留しました。[{_SCENE_LABELS.get(scene, scene)}] の「{value}」を"
                    "削除してよいかユーザーに確認したうえで confirmed_by_user=true を指定して再実行してください。"
                ),
            }
        return inbox_mod.remove_forbidden_from_profile(
            scene=scene,
            value=value,
            storage=self.storage,
        )

    def _dispatch_tool(self, name: str, args: dict[str, Any]) -> tuple[dict[str, Any], bool]:
        handlers = {
            "get_profile": self._tool_get_profile,
            "propose_profile_entry": self._tool_propose_profile_entry,
            "list_inbox": self._tool_list_inbox,
            "review_inbox_entry": self._tool_review_inbox_entry,
            "remove_profile_forbidden": self._tool_remove_profile_forbidden,
            "check_meaning_diff": self._tool_check_meaning_diff,
        }
        fn = handlers.get(name)
        if fn is None:
            return ({"error": f"未知のツールです: {name}"}, True)
        try:
            data = fn(args)
            return (data, False)
        except Exception as exc:
            return ({"error": str(exc)}, True)

    def _read_resource(self, uri: str) -> dict[str, Any]:
        if uri == "nihongo://profile":
            info = inbox_mod.read_profile(storage=self.storage)
            text = info["raw"] if info["exists"] else inbox_mod.DEFAULT_PROFILE_TEMPLATE
            return {
                "contents": [
                    {
                        "uri": uri,
                        "mimeType": "text/markdown",
                        "text": text,
                    }
                ]
            }
        if uri == "nihongo://inbox/pending":
            items = inbox_mod.list_inbox(status="pending", storage=self.storage)
            return {
                "contents": [
                    {
                        "uri": uri,
                        "mimeType": "application/json",
                        "text": json.dumps({"count": len(items), "items": items}, ensure_ascii=False, indent=2),
                    }
                ]
            }
        raise KeyError(f"リソースが見つかりません: {uri}")

    def handle_request(self, message: dict[str, Any]) -> dict[str, Any] | None:
        """1件の JSON-RPC 2.0 メッセージを処理してレスポンス dict（通知時は None）を返す。"""
        method = message.get("method")
        req_id = message.get("id")
        is_notification = "id" not in message

        if not isinstance(method, str):
            if is_notification:
                return None
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32600, "message": "Invalid Request: method must be a string"},
            }

        params = message.get("params")
        if params is None:
            params = {}
        if not isinstance(params, dict):
            if is_notification:
                return None
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32602, "message": "Invalid params: expected object"},
            }

        # Notifications
        if method in ("notifications/initialized", "notifications/cancelled"):
            return None
        if is_notification:
            return None

        if method == "initialize":
            client_ver = params.get("protocolVersion")
            proto_ver = client_ver if isinstance(client_ver, str) and client_ver else DEFAULT_PROTOCOL_VERSION
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": proto_ver,
                    "capabilities": {
                        "tools": {"listChanged": False},
                        "resources": {"subscribe": False, "listChanged": False},
                    },
                    "serverInfo": {
                        "name": SERVER_NAME,
                        "version": SERVER_VERSION,
                    },
                    "instructions": self._instructions(),
                },
            }

        if method == "ping":
            return {"jsonrpc": "2.0", "id": req_id, "result": {}}

        if method == "tools/list":
            return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": self._exposed_tools()}}

        if method == "tools/call":
            tool_name = params.get("name")
            tool_args = params.get("arguments") or {}
            if not isinstance(tool_name, str) or not isinstance(tool_args, dict):
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32602, "message": "Invalid params for tools/call"},
                }
            data, is_error = self._dispatch_tool(tool_name, tool_args)
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(data, ensure_ascii=False, indent=2),
                        }
                    ],
                    "structuredContent": data,
                    "isError": is_error,
                },
            }

        if method == "resources/list":
            return {"jsonrpc": "2.0", "id": req_id, "result": {"resources": RESOURCES_SPEC}}

        if method == "resources/read":
            uri = params.get("uri")
            if not isinstance(uri, str):
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32602, "message": "Invalid params: uri must be a string"},
                }
            try:
                res = self._read_resource(uri)
            except KeyError as exc:
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32002, "message": str(exc)},
                }
            return {"jsonrpc": "2.0", "id": req_id, "result": res}

        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32601, "message": f"Method not found: {method}"},
        }


def _read_message(stream: BinaryIO) -> tuple[dict[str, Any] | None, str]:
    """newline 区切り JSON-RPC と Content-Length フレーミングの両方に対応するリーダー。"""
    while True:
        line = stream.readline()
        if not line:
            return (None, "ndjson")
        stripped = line.strip()
        if not stripped:
            continue

        # Content-Length header framing (LSP-style fallback)
        if stripped.lower().startswith(b"content-length:"):
            headers: dict[str, str] = {}
            k, _, v = stripped.decode("ascii", errors="replace").partition(":")
            headers[k.strip().lower()] = v.strip()
            while True:
                hline = stream.readline()
                if not hline or hline in (b"\r\n", b"\n"):
                    break
                hk, _, hv = hline.decode("ascii", errors="replace").partition(":")
                headers[hk.strip().lower()] = hv.strip()
            length = int(headers.get("content-length", "0"))
            body = stream.read(length) if length > 0 else b""
            if not body:
                return (None, "content-length")
            return (json.loads(body.decode("utf-8")), "content-length")

        # Standard MCP stdio newline-delimited JSON-RPC
        return (json.loads(stripped.decode("utf-8")), "ndjson")


def _write_message(stream: BinaryIO, payload: dict[str, Any], framing: str) -> None:
    encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    if framing == "content-length":
        header = f"Content-Length: {len(encoded)}\r\n\r\n".encode("ascii")
        stream.write(header + encoded)
    else:
        stream.write(encoded + b"\n")
    stream.flush()


def serve_stdio(
    server: NihongoMcpServer,
    stdin: BinaryIO | None = None,
    stdout: BinaryIO | None = None,
) -> int:
    in_stream = stdin if stdin is not None else sys.stdin.buffer
    out_stream = stdout if stdout is not None else sys.stdout.buffer

    while True:
        try:
            msg, framing = _read_message(in_stream)
        except json.JSONDecodeError as exc:
            err = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": f"Parse error: {exc}"},
            }
            _write_message(out_stream, err, "ndjson")
            continue
        except Exception as exc:
            print(f"[nihongo-mcp] read error: {exc}", file=sys.stderr)
            break

        if msg is None:
            break

        if isinstance(msg, dict):
            resp = server.handle_request(msg)
            if resp is not None:
                _write_message(out_stream, resp, framing)
    return 0


INIT_TARGETS = ("claude-desktop", "claude-code", "cursor", "antigravity")


def resolve_client_config_path(target: str, *, platform: str | None = None) -> str:
    """対象クライアントの標準 MCP 設定ファイルパスを OS ごとに返す。"""
    plat = platform or sys.platform
    home = os.path.expanduser("~")
    t = target.strip().lower()
    if t == "claude-desktop":
        if plat.startswith("win"):
            appdata = os.environ.get("APPDATA") or os.path.join(home, "AppData", "Roaming")
            return os.path.join(appdata, "Claude", "claude_desktop_config.json")
        if plat == "darwin":
            return os.path.join(home, "Library", "Application Support", "Claude", "claude_desktop_config.json")
        return os.path.join(home, ".config", "Claude", "claude_desktop_config.json")
    if t == "claude-code":
        return os.path.join(home, ".claude.json")
    if t == "cursor":
        return os.path.join(home, ".cursor", "mcp.json")
    if t == "antigravity":
        return os.path.join(home, ".gemini", "antigravity", "mcp_config.json")
    raise ValueError(f"未対応の target です: {target!r}（{', '.join(INIT_TARGETS)} から指定）")


def build_mcp_server_entry(
    *,
    strict_hitl: bool = False,
    home: str | None = None,
    use_installed_cmd: bool = False,
) -> dict[str, Any]:
    """クライアント設定ファイルの mcpServers['nihongo'] に書き込むエントリを生成する。"""
    extra_args: list[str] = []
    if strict_hitl:
        extra_args.append("--strict-hitl")
    if home:
        extra_args.extend(["--home", os.path.abspath(os.path.expanduser(home))])

    if use_installed_cmd and shutil.which("nihongo-mcp"):
        return {
            "command": shutil.which("nihongo-mcp") or "nihongo-mcp",
            "args": extra_args,
            "env": {"PYTHONUTF8": "1"},
        }

    script_path = os.path.abspath(__file__)
    return {
        "command": sys.executable,
        "args": [script_path, *extra_args],
        "env": {"PYTHONUTF8": "1"},
    }


def init_mcp_config(
    *,
    target: str,
    config_path: str | None = None,
    strict_hitl: bool = False,
    home: str | None = None,
    dry_run: bool = False,
    use_installed_cmd: bool = False,
) -> dict[str, Any]:
    """既存 MCP 設定を壊さずに mcpServers['nihongo'] を安全に追加・更新する。"""
    cfg_path = (
        os.path.abspath(os.path.expanduser(config_path))
        if config_path
        else resolve_client_config_path(target)
    )
    entry = build_mcp_server_entry(
        strict_hitl=strict_hitl,
        home=home,
        use_installed_cmd=use_installed_cmd,
    )

    existed = os.path.isfile(cfg_path)
    data: dict[str, Any] = {}
    if existed:
        with open(cfg_path, encoding="utf-8-sig") as f:
            raw = f.read()
        if raw.strip():
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"既存の設定ファイルが正しい JSON ではないため上書きを中止しました（{cfg_path}）: {exc}"
                ) from exc
            if not isinstance(parsed, dict):
                raise ValueError(f"設定ファイルのルートが JSON オブジェクトではありません: {cfg_path}")
            data = parsed

    mcp_servers = data.get("mcpServers")
    if mcp_servers is None:
        mcp_servers = {}
        data["mcpServers"] = mcp_servers
    elif not isinstance(mcp_servers, dict):
        raise ValueError(f"設定ファイル内の mcpServers がオブジェクトではありません: {cfg_path}")

    already_configured = "nihongo" in mcp_servers
    mcp_servers["nihongo"] = entry

    backup_path: str | None = None
    if not dry_run:
        if existed:
            ts = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
            cand_bak = f"{cfg_path}.{ts}.bak"
            seq = 1
            while os.path.exists(cand_bak):
                cand_bak = f"{cfg_path}.{ts}_{seq}.bak"
                seq += 1
            backup_path = cand_bak
            shutil.copy2(cfg_path, backup_path)
        rendered = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
        inbox_mod._atomic_write_utf8(cfg_path, rendered)

    return {
        "target": target,
        "config_path": cfg_path,
        "existed": existed,
        "updated": already_configured,
        "dry_run": dry_run,
        "backup_path": backup_path,
        "entry": entry,
    }


def _main_init(argv: list[str]) -> int:
    cli_mod._ensure_utf8_stdio()
    parser = argparse.ArgumentParser(
        prog="nihongo-mcp init",
        description="Claude Desktop / Claude Code / Cursor / Antigravity の MCP 設定に nihongo を安全に自動登録する",
    )
    parser.add_argument(
        "--target",
        choices=(*INIT_TARGETS, "all"),
        default="claude-desktop",
        help="登録先の AI アプリ（既定: claude-desktop）",
    )
    parser.add_argument("--config", default=None, help="設定ファイルのパスを明示指定（単一 target 時のみ）")
    parser.add_argument("--home", default=None, help="データディレクトリ（既定: ~/.nihongo）")
    parser.add_argument(
        "--strict-hitl",
        action="store_true",
        help="MCP からの profile.md 承認を物理無効化する厳格モードで登録する",
    )
    parser.add_argument(
        "--use-installed-cmd",
        action="store_true",
        help="PATH 上に nihongo-mcp コマンドがある場合はそれを登録に使う",
    )
    parser.add_argument("--dry-run", action="store_true", help="ファイルを書き換えずに登録内容だけ確認する")
    parser.add_argument(
        "--detect-sync",
        action="store_true",
        help="PC 内の Google Drive / Dropbox / iCloud Drive 同期フォルダ候補を検出して終了する",
    )
    parser.add_argument("--json", action="store_true", help="JSON 形式で出力する")
    args = parser.parse_args(argv)

    if args.detect_sync:
        folders = inbox_mod.detect_sync_folders()
        if args.json:
            print(json.dumps({"count": len(folders), "folders": folders}, ensure_ascii=False, indent=2))
            return 0
        if not folders:
            print("既知のクラウド同期フォルダは見つかりませんでした。ローカル既定（~/.nihongo）が使えます。")
            return 0
        print(f"同期フォルダ候補を {len(folders)} 件見つけました:")
        for f in folders:
            print(f"- [{f['provider']}] {f['suggested_home']}")
        print("反映例: nihongo-mcp init --target all --home \"<上の suggested_home>\"")
        return 0

    targets = list(INIT_TARGETS) if args.target == "all" else [args.target]
    if args.config and len(targets) > 1:
        print("エラー: --config は --target all と併用できません。", file=sys.stderr)
        return 2

    results: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    for t in targets:
        try:
            res = init_mcp_config(
                target=t,
                config_path=args.config,
                strict_hitl=args.strict_hitl,
                home=args.home,
                dry_run=args.dry_run,
                use_installed_cmd=args.use_installed_cmd,
            )
            results.append(res)
        except Exception as exc:
            errors.append({"target": t, "error": str(exc)})

    if args.json:
        print(json.dumps({"results": results, "errors": errors}, ensure_ascii=False, indent=2))
        return 1 if errors else 0

    for res in results:
        prefix = "[ドライラン] " if res["dry_run"] else ""
        action = "更新" if res["updated"] else "新規登録"
        print(f"{prefix}{res['target']} に nihongo MCP を{action}しました: {res['config_path']}")
        if res["backup_path"]:
            print(f"  バックアップ: {res['backup_path']}")
    for err in errors:
        print(f"エラー ({err['target']}): {err['error']}", file=sys.stderr)
    if results and not args.dry_run and not errors:
        print("対象アプリを再起動すると nihongo MCP が自動で使えるようになります。")
    return 1 if errors else 0


def main(argv: list[str] | None = None) -> int:
    raw_argv = list(sys.argv[1:] if argv is None else argv)
    if raw_argv and raw_argv[0] == "init":
        return _main_init(raw_argv[1:])

    parser = argparse.ArgumentParser(
        prog="nihongo-mcp",
        description="nihongo 個人プロフィール・HITL 受信箱・0トークン意味ズレ検査の MCP サーバー（stdio）。自動登録は `nihongo-mcp init`",
    )
    parser.add_argument("--home", default=None, help="データディレクトリ（既定: ~/.nihongo）")
    parser.add_argument("--profile", default=None, help="profile.md のパス")
    parser.add_argument("--inbox", default=None, help="inbox.jsonl のパス")
    parser.add_argument(
        "--strict-hitl",
        action="store_true",
        help="MCP からの profile.md 承認・却下を物理的に無効化し、承認を CLI（nihongo-check inbox review）のみに限定する",
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="stdio 待機に入らず、公開ツール一覧と参照パスを確認して終了する",
    )
    args = parser.parse_args(raw_argv)

    server = NihongoMcpServer(
        home=args.home,
        profile_path=args.profile,
        inbox_path=args.inbox,
        strict_hitl=args.strict_hitl,
    )
    if args.self_test:
        cli_mod._ensure_utf8_stdio()
        print(
            json.dumps(
                {
                    "server": SERVER_NAME,
                    "version": SERVER_VERSION,
                    "strict_hitl": server.strict_hitl,
                    "profile_path": server.profile_path,
                    "inbox_path": server.inbox_path,
                    "tools": [t["name"] for t in server._exposed_tools()],
                    "resources": [r["uri"] for r in RESOURCES_SPEC],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    return serve_stdio(server)


if __name__ == "__main__":
    raise SystemExit(main())
