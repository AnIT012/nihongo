"""HITL inbox・CLI・stdio MCP サーバーの包括テスト（標準ライブラリだけで動作）。"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(HERE, ".."))
SCRIPTS_DIR = os.path.join(REPO_ROOT, "nihongo", "scripts")
CLI = os.path.join(SCRIPTS_DIR, "cli.py")
MCP = os.path.join(SCRIPTS_DIR, "mcp_server.py")

if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

import cli as cli_mod  # noqa: E402
import inbox as inbox_mod  # noqa: E402
import mcp_server as mcp_mod  # noqa: E402


def run_cli(
    args: list[str],
    stdin_text: str | None = None,
    env_extra: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        [sys.executable, CLI, *args],
        input=stdin_text,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
        check=False,
    )


def run_mcp_session(
    messages: list[dict],
    home_dir: str,
    *,
    framing: str = "ndjson",
) -> list[dict]:
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["NIHONGO_HOME"] = home_dir

    chunks: list[bytes] = []
    for msg in messages:
        raw = json.dumps(msg, ensure_ascii=False).encode("utf-8")
        if framing == "content-length":
            chunks.append(f"Content-Length: {len(raw)}\r\n\r\n".encode("ascii") + raw)
        else:
            chunks.append(raw + b"\n")

    proc = subprocess.run(
        [sys.executable, MCP, "--home", home_dir],
        input=b"".join(chunks),
        capture_output=True,
        env=env,
        check=False,
    )
    if proc.returncode != 0:
        raise AssertionError(f"mcp_server exited {proc.returncode}: {proc.stderr.decode('utf-8', errors='replace')}")

    out = proc.stdout
    responses: list[dict] = []
    if framing == "content-length":
        pos = 0
        while pos < len(out):
            sep = out.find(b"\r\n\r\n", pos)
            if sep == -1:
                break
            header = out[pos:sep].decode("ascii")
            length = 0
            for line in header.split("\r\n"):
                if line.lower().startswith("content-length:"):
                    length = int(line.split(":", 1)[1].strip())
            body_start = sep + 4
            body = out[body_start : body_start + length]
            responses.append(json.loads(body.decode("utf-8")))
            pos = body_start + length
    else:
        for line in out.decode("utf-8").splitlines():
            if line.strip():
                responses.append(json.loads(line))
    return responses


class InboxEngineTests(unittest.TestCase):
    def test_propose_never_writes_profile_and_deduplicates(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            profile_p = os.path.join(d, "profile.md")
            inbox_p = os.path.join(d, "inbox.jsonl")

            res1 = inbox_mod.propose_entry(
                scene="common",
                kind="forbidden",
                value="ご査収のほど",
                reason="社外メールで消した",
                source="claude-desktop",
                inbox_path=inbox_p,
                profile_path=profile_p,
            )
            self.assertTrue(res1["created"])
            self.assertFalse(os.path.exists(profile_p))
            self.assertTrue(os.path.isfile(inbox_p))

            # 「」付き重複は新規作成されない
            res2 = inbox_mod.propose_entry(
                scene="common",
                kind="forbidden",
                value="「ご査収のほど」",
                inbox_path=inbox_p,
                profile_path=profile_p,
            )
            self.assertFalse(res2["created"])
            self.assertTrue(res2["duplicate"])
            self.assertEqual(res2["entry"]["id"], res1["entry"]["id"])

    def test_pii_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            inbox_p = os.path.join(d, "inbox.jsonl")
            with self.assertRaises(ValueError):
                inbox_mod.propose_entry(
                    scene="common",
                    kind="rule",
                    value="連絡先は taro@example.com にする",
                    inbox_path=inbox_p,
                )
            with self.assertRaises(ValueError):
                inbox_mod.propose_entry(
                    scene="work",
                    kind="rule",
                    value="電話は 090-1234-5678 を書く",
                    inbox_path=inbox_p,
                )
            with self.assertRaises(ValueError):
                inbox_mod.propose_entry(
                    scene="common",
                    kind="rule",
                    value="キーは sk-1234567890abcdef12345678",
                    inbox_path=inbox_p,
                )

    def test_formal_boundary_guard_blocks_casual_slang_unless_forced(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            profile_p = os.path.join(d, "profile.md")
            inbox_p = os.path.join(d, "inbox.jsonl")

            res = inbox_mod.propose_entry(
                scene="formal",
                kind="tone",
                value="語尾は「了解っすw」にする",
                inbox_path=inbox_p,
                profile_path=profile_p,
            )
            self.assertIsNotNone(res["warning"])
            item_id = res["entry"]["id"]

            # 通常承認ではブロックされる
            appr1 = inbox_mod.approve_entries(
                [item_id],
                inbox_path=inbox_p,
                profile_path=profile_p,
            )
            self.assertEqual(appr1["approved_count"], 0)
            self.assertEqual(len(appr1["blocked_by_guard"]), 1)
            self.assertFalse(os.path.exists(profile_p))

            # 禁止表現（forbidden）なら formal でもブロックされない
            res_forb = inbox_mod.propose_entry(
                scene="formal",
                kind="forbidden",
                value="っす",
                inbox_path=inbox_p,
                profile_path=profile_p,
            )
            self.assertIsNone(res_forb["warning"])

    def test_approve_updates_profile_and_preserves_existing_sections(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            profile_p = os.path.join(d, "profile.md")
            inbox_p = os.path.join(d, "inbox.jsonl")
            with open(profile_p, "w", encoding="utf-8", newline="\n") as f:
                f.write(
                    "# 私の書き方\n\n"
                    "## [common]\n"
                    "- 一人称：私\n"
                    "- 絶対に言わない表現：「させていただきます」\n"
                    "- 書く時の考え方：結論を先に書く\n\n"
                    "## [work]\n"
                    "- 場面：社内チャット・PR・同僚\n"
                    "- 口調・記号：フラットなです・ます\n\n"
                    "## 手本\n"
                    "- 【名前】です。確認しました。\n"
                )

            p1 = inbox_mod.propose_entry(
                scene="common",
                kind="forbidden",
                value="ご査収のほど",
                inbox_path=inbox_p,
                profile_path=profile_p,
            )
            p2 = inbox_mod.propose_entry(
                scene="work",
                kind="tone",
                value="了解は「了解です」と短く返す",
                inbox_path=inbox_p,
                profile_path=profile_p,
            )
            p3 = inbox_mod.propose_entry(
                scene="casual",
                kind="tone",
                value="常体寄り",
                inbox_path=inbox_p,
                profile_path=profile_p,
            )

            # dry-run ではファイル未変更
            dry = inbox_mod.approve_entries(
                approve_all=True,
                dry_run=True,
                inbox_path=inbox_p,
                profile_path=profile_p,
            )
            self.assertTrue(dry["dry_run"])
            self.assertEqual(dry["approved_count"], 3)
            self.assertEqual(len(inbox_mod.list_inbox(status="pending", inbox_path=inbox_p)), 3)

            # 本承認で反映
            appr = inbox_mod.approve_entries(
                [p1["entry"]["id"], p2["entry"]["id"], p3["entry"]["id"]],
                inbox_path=inbox_p,
                profile_path=profile_p,
            )
            self.assertEqual(appr["approved_count"], 3)
            self.assertTrue(appr["profile_updated"])
            self.assertEqual(len(inbox_mod.list_inbox(status="pending", inbox_path=inbox_p)), 0)

            with open(profile_p, encoding="utf-8") as f:
                content = f.read()
            self.assertIn("「させていただきます」、「ご査収のほど」", content)
            self.assertIn("了解は「了解です」と短く返す", content)
            self.assertIn("## [casual]", content)
            self.assertIn("## 手本", content)
            self.assertIn("【名前】です。確認しました。", content)

            # cli.py の parse_profile でもすぐ機械検出できること
            forbidden = cli_mod.parse_profile(profile_p, scene="formal")
            self.assertIn("させていただきます", forbidden)
            self.assertIn("ご査収のほど", forbidden)


class CliInboxTests(unittest.TestCase):
    def test_cli_propose_approve_then_diff_detects_forbidden(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            profile_p = os.path.join(d, "profile.md")
            inbox_p = os.path.join(d, "inbox.jsonl")
            orig_p = os.path.join(d, "orig.md")
            draft_p = os.path.join(d, "draft.md")

            r_prop = run_cli([
                "inbox", "propose",
                "--scene", "common",
                "--kind", "forbidden",
                "--value", "ご査収のほど",
                "--reason", "普段使わない表現",
                "--inbox", inbox_p,
                "--profile", profile_p,
                "--json",
            ])
            self.assertEqual(r_prop.returncode, 0, r_prop.stderr)
            item_id = json.loads(r_prop.stdout)["entry"]["id"]

            r_list = run_cli(["inbox", "list", "--inbox", inbox_p, "--json"])
            self.assertEqual(r_list.returncode, 0, r_list.stderr)
            self.assertEqual(json.loads(r_list.stdout)["count"], 1)

            r_appr = run_cli([
                "inbox", "approve", item_id,
                "--inbox", inbox_p,
                "--profile", profile_p,
                "--json",
            ])
            self.assertEqual(r_appr.returncode, 0, r_appr.stderr)
            self.assertTrue(json.loads(r_appr.stdout)["profile_updated"])

            # 承認した表現を diff --profile が検出できる
            with open(orig_p, "w", encoding="utf-8") as f:
                f.write("資料をご確認ください。\n")
            with open(draft_p, "w", encoding="utf-8") as f:
                f.write("資料をご査収のほどお願いいたします。\n")

            r_diff = run_cli(["diff", orig_p, draft_p, "--profile", profile_p, "--scene", "formal"])
            self.assertEqual(r_diff.returncode, 1)
            self.assertIn("[個人ルール]", r_diff.stdout)
            self.assertIn("ご査収のほど", r_diff.stdout)

    def test_cli_interactive_review_and_profile_show(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            profile_p = os.path.join(d, "profile.md")
            inbox_p = os.path.join(d, "inbox.jsonl")
            inbox_mod.propose_entry(scene="common", kind="forbidden", value="アサイン", inbox_path=inbox_p)
            inbox_mod.propose_entry(scene="work", kind="tone", value="語尾に！を3連打", inbox_path=inbox_p)

            r_rev = run_cli(
                ["inbox", "review", "--inbox", inbox_p, "--profile", profile_p],
                stdin_text="a\nr\n",
            )
            self.assertEqual(r_rev.returncode, 0, r_rev.stderr)
            self.assertIn("承認 1 件 / 却下 1 件", r_rev.stdout)

            r_show = run_cli(["profile", "show", "--profile", profile_p, "--inbox", inbox_p, "--json"])
            self.assertEqual(r_show.returncode, 0, r_show.stderr)
            data = json.loads(r_show.stdout)
            self.assertTrue(data["exists"])
            self.assertEqual(data["pending_inbox_count"], 0)
            self.assertIn("アサイン", data["forbidden"])


class McpServerStdioTests(unittest.TestCase):
    def test_full_mcp_hitl_lifecycle_ndjson(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            # 1. initialize -> tools/list -> propose_profile_entry
            resps1 = run_mcp_session(
                [
                    {
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "initialize",
                        "params": {"protocolVersion": "2025-03-26", "capabilities": {}, "clientInfo": {"name": "test", "version": "1.0"}},
                    },
                    {"jsonrpc": "2.0", "method": "notifications/initialized"},
                    {"jsonrpc": "2.0", "id": 2, "method": "ping"},
                    {"jsonrpc": "2.0", "id": 3, "method": "tools/list"},
                    {
                        "jsonrpc": "2.0",
                        "id": 4,
                        "method": "tools/call",
                        "params": {
                            "name": "propose_profile_entry",
                            "arguments": {
                                "scene": "common",
                                "kind": "forbidden",
                                "value": "恐れ入りますが",
                                "reason": "チャットで毎回削っている",
                                "source": "claude-desktop",
                            },
                        },
                    },
                ],
                home_dir=d,
                framing="ndjson",
            )
            self.assertEqual(len(resps1), 4)  # notification returns no response
            self.assertEqual(resps1[0]["result"]["serverInfo"]["name"], "nihongo-mcp")
            self.assertEqual(resps1[1]["result"], {})
            tool_names = [t["name"] for t in resps1[2]["result"]["tools"]]
            self.assertEqual(
                tool_names,
                [
                    "get_profile",
                    "propose_profile_entry",
                    "list_inbox",
                    "review_inbox_entry",
                    "remove_profile_forbidden",
                    "check_meaning_diff",
                ],
            )
            prop_data = resps1[3]["result"]["structuredContent"]
            self.assertTrue(prop_data["created"])
            item_id = prop_data["entry"]["id"]

            # profile.md はまだ作られていない（HITL原則）
            self.assertFalse(os.path.exists(os.path.join(d, "profile.md")))

            # 2. confirmed_by_user 無し approve はブロックされ dry-run のみ返す
            resps2 = run_mcp_session(
                [
                    {
                        "jsonrpc": "2.0",
                        "id": 10,
                        "method": "tools/call",
                        "params": {
                            "name": "review_inbox_entry",
                            "arguments": {
                                "action": "approve",
                                "ids": [item_id],
                                "confirmed_by_user": False,
                            },
                        },
                    },
                    {
                        "jsonrpc": "2.0",
                        "id": 11,
                        "method": "tools/call",
                        "params": {
                            "name": "review_inbox_entry",
                            "arguments": {
                                "action": "approve",
                                "ids": [item_id],
                                "confirmed_by_user": True,
                            },
                        },
                    },
                    {
                        "jsonrpc": "2.0",
                        "id": 12,
                        "method": "tools/call",
                        "params": {
                            "name": "get_profile",
                            "arguments": {"scene": "formal"},
                        },
                    },
                    {
                        "jsonrpc": "2.0",
                        "id": 13,
                        "method": "tools/call",
                        "params": {
                            "name": "check_meaning_diff",
                            "arguments": {
                                "orig": "資料は明日15時までに必ず送ってください。",
                                "draft": "恐れ入りますが、資料は明日16時までにお送りいただけますでしょうか。",
                                "scene": "formal",
                                "check_commas": True,
                            },
                        },
                    },
                    {
                        "jsonrpc": "2.0",
                        "id": 14,
                        "method": "resources/read",
                        "params": {"uri": "nihongo://profile"},
                    },
                ],
                home_dir=d,
                framing="ndjson",
            )
            dry_data = resps2[0]["result"]["structuredContent"]
            self.assertTrue(dry_data["requires_user_confirmation"])
            self.assertTrue(dry_data["dry_run"])

            appr_data = resps2[1]["result"]["structuredContent"]
            self.assertFalse(appr_data["dry_run"])
            self.assertTrue(appr_data["profile_updated"])
            self.assertTrue(os.path.isfile(os.path.join(d, "profile.md")))

            prof_data = resps2[2]["result"]["structuredContent"]
            self.assertIn("恐れ入りますが", prof_data["forbidden"])
            self.assertEqual(prof_data["pending_inbox_count"], 0)

            diff_data = resps2[3]["result"]["structuredContent"]
            self.assertFalse(diff_data["clean"])
            findings_joined = "\n".join(diff_data["findings"])
            self.assertIn("[数値・日時]", findings_joined)
            self.assertIn("[個人ルール]", findings_joined)
            self.assertIn("恐れ入りますが", findings_joined)

            res_profile = resps2[4]["result"]["contents"][0]
            self.assertEqual(res_profile["mimeType"], "text/markdown")
            self.assertIn("恐れ入りますが", res_profile["text"])

    def test_mcp_content_length_framing_and_self_test(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            resps = run_mcp_session(
                [
                    {"jsonrpc": "2.0", "id": 1, "method": "resources/list"},
                    {"jsonrpc": "2.0", "id": 2, "method": "resources/read", "params": {"uri": "nihongo://inbox/pending"}},
                ],
                home_dir=d,
                framing="content-length",
            )
            self.assertEqual(len(resps), 2)
            uris = [r["uri"] for r in resps[0]["result"]["resources"]]
            self.assertEqual(uris, ["nihongo://profile", "nihongo://inbox/pending"])
            pending_json = json.loads(resps[1]["result"]["contents"][0]["text"])
            self.assertEqual(pending_json["count"], 0)

            env = os.environ.copy()
            env["PYTHONUTF8"] = "1"
            st = subprocess.run(
                [sys.executable, MCP, "--home", d, "--self-test"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                env=env,
                check=False,
            )
            self.assertEqual(st.returncode, 0, st.stderr)
            info = json.loads(st.stdout)
            self.assertEqual(info["server"], "nihongo-mcp")
            self.assertIn("propose_profile_entry", info["tools"])

    def test_strict_hitl_blocks_mcp_profile_writes(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            srv = mcp_mod.NihongoMcpServer(home=d, strict_hitl=True)
            r_list = srv.handle_request({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
            assert r_list is not None
            names = [t["name"] for t in r_list["result"]["tools"]]
            self.assertNotIn("review_inbox_entry", names)
            self.assertIn("propose_profile_entry", names)

            # propose は通る
            r_prop = srv.handle_request({
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "propose_profile_entry",
                    "arguments": {"scene": "common", "kind": "forbidden", "value": "コミット"},
                },
            })
            assert r_prop is not None
            item_id = r_prop["result"]["structuredContent"]["entry"]["id"]

            # 直接 review_inbox_entry を叩いても物理拒否され profile.md は作られない
            r_rev = srv.handle_request({
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "review_inbox_entry",
                    "arguments": {"action": "approve", "ids": [item_id], "confirmed_by_user": True},
                },
            })
            assert r_rev is not None
            self.assertTrue(r_rev["result"]["isError"])
            self.assertIn("--strict-hitl", r_rev["result"]["structuredContent"]["error"])
            self.assertFalse(os.path.exists(os.path.join(d, "profile.md")))

    def test_custom_storage_adapter_runs_without_local_disk(self) -> None:
        """将来の GoogleDriveStorage 等と同じ 4 メソッド実装だけで全機能が動くことを確認。"""

        class MemoryStorage:
            def __init__(self) -> None:
                self.profile: str | None = None
                self.inbox: str | None = None

            @property
            def profile_location(self) -> str:
                return "memory://profile.md"

            @property
            def inbox_location(self) -> str:
                return "memory://inbox.jsonl"

            def read_profile_text(self) -> str | None:
                return self.profile

            def write_profile_text(self, content: str) -> None:
                self.profile = content

            def read_inbox_text(self) -> str | None:
                return self.inbox

            def write_inbox_text(self, content: str) -> None:
                self.inbox = content

        mem = MemoryStorage()
        srv = mcp_mod.NihongoMcpServer(storage=mem)

        r1 = srv.handle_request({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "propose_profile_entry",
                "arguments": {"scene": "common", "kind": "forbidden", "value": "アサイン"},
            },
        })
        assert r1 is not None
        item_id = r1["result"]["structuredContent"]["entry"]["id"]
        self.assertIsNone(mem.profile)
        self.assertIsNotNone(mem.inbox)

        r2 = srv.handle_request({
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "review_inbox_entry",
                "arguments": {"action": "approve", "ids": [item_id], "confirmed_by_user": True},
            },
        })
        assert r2 is not None
        self.assertTrue(r2["result"]["structuredContent"]["profile_updated"])
        self.assertIn("アサイン", mem.profile or "")

        r3 = srv.handle_request({
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "check_meaning_diff",
                "arguments": {
                    "orig": "担当者を決めます。",
                    "draft": "担当者をアサインします。",
                    "scene": "work",
                },
            },
        })
        assert r3 is not None
        self.assertFalse(r3["result"]["structuredContent"]["clean"])
        self.assertIn("アサイン", "\n".join(r3["result"]["structuredContent"]["findings"]))

    def test_init_creates_merges_backs_up_and_protects_corrupt_json(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            cfg = os.path.join(d, "claude_desktop_config.json")
            env = os.environ.copy()
            env["PYTHONUTF8"] = "1"

            # 1. dry-run はファイルを作らない
            r_dry = subprocess.run(
                [sys.executable, MCP, "init", "--target", "claude-desktop", "--config", cfg, "--dry-run", "--json"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                env=env,
                check=False,
            )
            self.assertEqual(r_dry.returncode, 0, r_dry.stderr)
            self.assertFalse(os.path.exists(cfg))

            # 2. 既存の他サーバーを壊さずにマージ＋バックアップ作成
            with open(cfg, "w", encoding="utf-8", newline="\n") as f:
                json.dump({"mcpServers": {"other": {"command": "echo", "args": ["hi"]}}, "theme": "light"}, f)

            r_real = subprocess.run(
                [
                    sys.executable,
                    MCP,
                    "init",
                    "--target",
                    "claude-desktop",
                    "--config",
                    cfg,
                    "--strict-hitl",
                    "--json",
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                env=env,
                check=False,
            )
            self.assertEqual(r_real.returncode, 0, r_real.stderr)
            res = json.loads(r_real.stdout)["results"][0]
            self.assertIsNotNone(res["backup_path"])
            self.assertTrue(os.path.isfile(res["backup_path"]))

            with open(cfg, encoding="utf-8") as f:
                merged = json.load(f)
            self.assertEqual(merged["theme"], "light")
            self.assertIn("other", merged["mcpServers"])
            self.assertIn("nihongo", merged["mcpServers"])
            self.assertIn("--strict-hitl", merged["mcpServers"]["nihongo"]["args"])

            # 3. 壊れた JSON ファイルは上書きせずエラーで止める
            broken = os.path.join(d, "broken.json")
            with open(broken, "w", encoding="utf-8") as f:
                f.write("{invalid json")
            r_bad = subprocess.run(
                [sys.executable, MCP, "init", "--target", "cursor", "--config", broken],
                capture_output=True,
                text=True,
                encoding="utf-8",
                env=env,
                check=False,
            )
            self.assertNotEqual(r_bad.returncode, 0)
            with open(broken, encoding="utf-8") as f:
                self.assertEqual(f.read(), "{invalid json")

    def test_persona_audit_regression_fixes(self) -> None:
        """3ペルソナ実戦監査で発見したバグ・UX穴の再発防止テスト。"""
        with tempfile.TemporaryDirectory() as d:
            srv = mcp_mod.NihongoMcpServer(home=d)

            # 1. Markdown URL 周辺編集で誤爆しない & 15時→15時頃 の期限ぼかしを検知する
            r_url = srv.handle_request({
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "check_meaning_diff",
                    "arguments": {
                        "orig": "詳細は[nihongo](https://github.com/AnIT012/nihongo)を参照してください。",
                        "draft": "詳細は[nihongo](https://github.com/AnIT012/nihongo)をご覧ください。",
                    },
                },
            })
            assert r_url is not None
            self.assertTrue(r_url["result"]["structuredContent"]["clean"])

            r_hedge = srv.handle_request({
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "check_meaning_diff",
                    "arguments": {
                        "orig": "資料は明日15時までに送ってください。",
                        "draft": "資料は明日15時頃までにお送りください。",
                    },
                },
            })
            assert r_hedge is not None
            self.assertFalse(r_hedge["result"]["structuredContent"]["clean"])
            self.assertIn("頃", "\n".join(r_hedge["result"]["structuredContent"]["findings"]))

            # 2. 業務記号 ✓ ★ は絵文字として誤爆しない
            r_sym = srv.handle_request({
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "check_meaning_diff",
                    "arguments": {
                        "orig": "確認項目です。",
                        "draft": "✓ 確認項目です。★重要",
                        "scene": "formal",
                    },
                },
            })
            assert r_sym is not None
            self.assertNotIn("絵文字", "\n".join(r_sym["result"]["structuredContent"]["findings"]))

            # 3. 禁止表現に「・」「、」が含まれても括弧内は分割破壊されない
            p_ui = inbox_mod.propose_entry(scene="common", kind="forbidden", value="UI・UX", storage=srv.storage)
            inbox_mod.approve_entries([p_ui["entry"]["id"]], storage=srv.storage)
            parsed = cli_mod.parse_profile_text(srv.storage.read_profile_text() or "", scene="work")
            self.assertIn("UI・UX", parsed)
            self.assertNotIn("UI", parsed)

            # 4. 全角電話・現行 OpenAI / Anthropic キーは PII ガードで確実に弾かれる
            for bad_val in (
                "０９０－１２３４－５６７８",
                "ｔａｒｏ＠ｅｘａｍｐｌｅ．ｃｏｍ",
                "sk-proj-1234567890abcdef12345678",
                "sk-ant-api03-1234567890abcdef1234",
            ):
                with self.assertRaises(ValueError, msg=f"should block: {bad_val}"):
                    inbox_mod.propose_entry(scene="common", kind="rule", value=bad_val, storage=srv.storage)

            # 5. list_inbox の日本語ラベル＋index、action='batch' で「1と2承認・3却下」1発処理、却下ゾンビ防止
            a1 = inbox_mod.propose_entry(scene="common", kind="forbidden", value="ご査収のほど", storage=srv.storage)["entry"]["id"]
            a2 = inbox_mod.propose_entry(scene="work", kind="tone", value="了解は短く返す", storage=srv.storage)["entry"]["id"]
            a3 = inbox_mod.propose_entry(scene="work", kind="tone", value="語尾に絵文字を足す", storage=srv.storage)["entry"]["id"]

            r_list = srv.handle_request({"jsonrpc": "2.0", "id": 4, "method": "tools/call", "params": {"name": "list_inbox", "arguments": {}}})
            assert r_list is not None
            items = r_list["result"]["structuredContent"]["items"]
            self.assertEqual([it["index"] for it in items], [1, 2, 3])
            self.assertEqual(items[0]["scene_label"], "共通")
            self.assertEqual(items[0]["kind_label"], "NG表現")

            # batch は confirmed_by_user=False なら dry-run で止まる
            r_batch_dry = srv.handle_request({
                "jsonrpc": "2.0",
                "id": 5,
                "method": "tools/call",
                "params": {
                    "name": "review_inbox_entry",
                    "arguments": {"action": "batch", "approve_ids": [a1, a2], "reject_ids": [a3], "confirmed_by_user": False},
                },
            })
            assert r_batch_dry is not None
            self.assertTrue(r_batch_dry["result"]["structuredContent"]["requires_user_confirmation"])

            # confirmed_by_user=True で1発完了
            r_batch_ok = srv.handle_request({
                "jsonrpc": "2.0",
                "id": 6,
                "method": "tools/call",
                "params": {
                    "name": "review_inbox_entry",
                    "arguments": {"action": "batch", "approve_ids": [a1, a2], "reject_ids": [a3], "confirmed_by_user": True},
                },
            })
            assert r_batch_ok is not None
            batch_data = r_batch_ok["result"]["structuredContent"]
            self.assertEqual(batch_data["approved_count"], 2)
            self.assertEqual(batch_data["rejected_count"], 1)

            # 却下済み候補の再提案はゾンビ復活しない
            res_zombie = inbox_mod.propose_entry(scene="work", kind="tone", value="語尾に絵文字を足す", storage=srv.storage)
            self.assertFalse(res_zombie["created"])
            self.assertTrue(res_zombie["previously_rejected"])

            # 6. BOM 付き UTF-8 JSON でも init が成功し PYTHONUTF8=1 が入る
            bom_cfg = os.path.join(d, "bom_config.json")
            with open(bom_cfg, "wb") as f:
                f.write(b"\xef\xbb\xbf" + b'{"mcpServers": {}}\n')
            res_init = mcp_mod.init_mcp_config(target="claude-desktop", config_path=bom_cfg)
            self.assertEqual(res_init["entry"]["env"]["PYTHONUTF8"], "1")

            # 7. CLI --home と reject --all
            inbox_mod.propose_entry(scene="work", kind="tone", value="テスト用仮候補", storage=srv.storage)
            r_cli_rej = run_cli(["inbox", "reject", "--all", "--home", d, "--json"])
            self.assertEqual(r_cli_rej.returncode, 0, r_cli_rej.stderr)
            self.assertEqual(json.loads(r_cli_rej.stdout)["rejected_count"], 1)

            # 8. 日本語直結の API キー・トークンが PII ガードで弾かれる
            for jp_secret in (
                "キーはsk-proj-AbCdEfGhIjKlMnOpQrStです",
                "トークンはsk-ant-api03-1234567890abcdefを使う",
                "鍵はgithub_pat_11ABCDEFABCDEFGHIJ_abcdefです",
                "アクセスキーはAKIAIOSFODNN7EXAMPLEです",
            ):
                with self.assertRaises(ValueError, msg=f"should block JP-adjacent secret: {jp_secret}"):
                    inbox_mod.propose_entry(scene="common", kind="rule", value=jp_secret, storage=srv.storage)

            # 9. confirmed_by_user: "false"（文字列）では HITL ゲートを突破できない
            str_bool_id = inbox_mod.propose_entry(scene="work", kind="tone", value="文字列false検証用", storage=srv.storage)["entry"]["id"]
            r_str_false = srv.handle_request({
                "jsonrpc": "2.0",
                "id": 9,
                "method": "tools/call",
                "params": {
                    "name": "review_inbox_entry",
                    "arguments": {"action": "approve", "ids": [str_bool_id], "confirmed_by_user": "false"},
                },
            })
            assert r_str_false is not None
            self.assertTrue(r_str_false["result"]["structuredContent"]["requires_user_confirmation"])
            self.assertTrue(r_str_false["result"]["structuredContent"]["dry_run"])

            # 10. すでに profile.md に承認済みの項目は再提案しても重複追加されない
            dup_in_prof = inbox_mod.propose_entry(scene="common", kind="forbidden", value="ご査収のほど", storage=srv.storage)
            self.assertFalse(dup_in_prof["created"])
            self.assertTrue(dup_in_prof["already_in_profile"])

            # 11. BOM 付き inbox.jsonl / profile.md が消失せず読める
            bom_dir = os.path.join(d, "bom_home")
            os.makedirs(bom_dir, exist_ok=True)
            with open(os.path.join(bom_dir, "inbox.jsonl"), "wb") as f:
                f.write(
                    b"\xef\xbb\xbf"
                    + json.dumps({"id": "inb_bom_1", "status": "pending", "scene": "common", "kind": "rule", "value": "BOM生存テスト"}, ensure_ascii=False).encode("utf-8")
                    + b"\n"
                )
            with open(os.path.join(bom_dir, "profile.md"), "wb") as f:
                f.write(b"\xef\xbb\xbf" + "## [common]\n- 絶対に言わない表現：「取り急ぎ」\n".encode("utf-8"))
            loaded = inbox_mod.load_inbox(storage=inbox_mod.LocalFileStorage(home=bom_dir))
            self.assertEqual(len(loaded), 1)
            self.assertEqual(loaded[0]["id"], "inb_bom_1")
            prof_bom = inbox_mod.read_profile(storage=inbox_mod.LocalFileStorage(home=bom_dir))
            self.assertIn("common", prof_bom["sections"])


if __name__ == "__main__":
    unittest.main()
