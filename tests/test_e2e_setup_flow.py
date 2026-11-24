import glob
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SCRIPTS_DIR = os.path.join(ROOT, "nihongo", "scripts")
DOCS_HTML = os.path.join(ROOT, "docs", "index.html")


def _cli_cmd(name: str) -> list[str]:
    """CI でインストール済みコマンドを検証する時は PATH 上の実行ファイルを、通常テスト時は常にこのリポジトリのスクリプトを使う。"""
    if os.environ.get("NIHONGO_E2E_USE_INSTALLED") == "1":
        exe = shutil.which(name)
        if exe:
            return [exe]
    script = "cli.py" if name == "nihongo-check" else "mcp_server.py"
    return [sys.executable, os.path.join(SCRIPTS_DIR, script)]


def _isolated_env(home_dir: str) -> dict[str, str]:
    """本物のユーザー設定や profile.md に一切触れずに全サブプロセスを実行するための隔離環境を作る。"""
    env = os.environ.copy()
    env["HOME"] = home_dir
    env["USERPROFILE"] = home_dir
    env["APPDATA"] = os.path.join(home_dir, "AppData", "Roaming")
    env["LOCALAPPDATA"] = os.path.join(home_dir, "AppData", "Local")
    env["PYTHONUTF8"] = "1"
    env.pop("NIHONGO_HOME", None)
    env.pop("NIHONGO_CONFIG", None)
    return env


def _run(cmd: list[str], *, env: dict[str, str], stdin_text: str | None = None, cwd: str | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        input=stdin_text,
        text=True,
        encoding="utf-8",
        capture_output=True,
        env=env,
        cwd=cwd or ROOT,
        timeout=20,
    )


class TestE2ESetupFlow(unittest.TestCase):
    """空の隔離環境で setup.md のコマンド列を端から端まで実サブプロセスで通す E2E テスト（モックなし）。"""

    def test_setup_md_commands_end_to_end_real_subprocesses(self):
        with tempfile.TemporaryDirectory() as td:
            fake_home = os.path.join(td, "home")
            sync_home = os.path.join(fake_home, "Dropbox", "nihongo")
            os.makedirs(os.path.join(fake_home, ".nihongo"), exist_ok=True)
            os.makedirs(os.path.join(fake_home, "AppData", "Roaming"), exist_ok=True)
            os.makedirs(os.path.join(fake_home, "AppData", "Local"), exist_ok=True)
            env = _isolated_env(fake_home)

            # 0. 前提条件を再現:
            #    (a) 導入済みクライアント（Claude Code）に他の MCP サーバー設定がある（未導入アプリは作られないことも後で確認）
            claude_cfg_path = os.path.join(fake_home, ".claude.json")
            with open(claude_cfg_path, "w", encoding="utf-8") as f:
                json.dump({"mcpServers": {"other-server": {"command": "echo", "args": ["ok"]}}}, f, ensure_ascii=False)

            #    (b) 既存の ~/.nihongo/profile.md がある
            r_init_prof = _run(_cli_cmd("nihongo-check") + ["profile", "init"], env=env)
            self.assertEqual(r_init_prof.returncode, 0, r_init_prof.stdout + r_init_prof.stderr)
            local_profile = os.path.join(fake_home, ".nihongo", "profile.md")
            with open(local_profile, "r", encoding="utf-8") as f:
                prof_txt = f.read()
            with open(local_profile, "w", encoding="utf-8") as f:
                f.write(prof_txt.replace("- 絶対に言わない表現：", "- 絶対に言わない表現：「既存のNG」", 1))

            #    (c) 受信箱に前から無関係な未確認候補が1件溜まっている
            r_pre = _run(
                _cli_cmd("nihongo-check")
                + ["inbox", "propose", "--scene", "casual", "--kind", "tone", "--value", "語尾は「だね」寄り", "--source", "preexisting", "--json"],
                env=env,
            )
            self.assertEqual(r_pre.returncode, 0, r_pre.stdout + r_pre.stderr)
            pre_id = json.loads(r_pre.stdout)["entry"]["id"]

            # 1. 事前チェック: nihongo-check --version
            r_ver = _run(_cli_cmd("nihongo-check") + ["--version"], env=env)
            self.assertEqual(r_ver.returncode, 0, r_ver.stdout + r_ver.stderr)
            self.assertIn("3.", r_ver.stdout + r_ver.stderr)

            # 2. 同期フォルダを選んで MCP 登録（setup.md のコマンドそのまま）
            r_init1 = _run(_cli_cmd("nihongo-mcp") + ["init", "--target", "all", "--home", sync_home], env=env)
            self.assertEqual(r_init1.returncode, 0, r_init1.stdout + r_init1.stderr)

            # 既存 profile.md と inbox.jsonl が同期フォルダへ移行され、config.json が保存されている
            self.assertTrue(os.path.isfile(os.path.join(sync_home, "profile.md")))
            self.assertTrue(os.path.isfile(os.path.join(sync_home, "inbox.jsonl")))
            self.assertTrue(os.path.isfile(os.path.join(fake_home, ".nihongo", "config.json")))
            # 未導入の Antigravity 設定ファイルが勝手に作られていない
            self.assertFalse(os.path.exists(os.path.join(fake_home, ".gemini", "antigravity", "mcp_config.json")))

            # 同じ init を再実行しても変更なし扱いで .bak が増えない
            baks_before = sorted(glob.glob(claude_cfg_path + ".*.bak"))
            r_init2 = _run(_cli_cmd("nihongo-mcp") + ["init", "--target", "all", "--home", sync_home], env=env)
            self.assertEqual(r_init2.returncode, 0, r_init2.stdout + r_init2.stderr)
            baks_after = sorted(glob.glob(claude_cfg_path + ".*.bak"))
            self.assertEqual(baks_before, baks_after)

            # 3. 初期ルール反映: propose が返した ID だけを approve（NIHONGO_HOME 未設定のまま config.json 経由で同期先に効く）
            r_prop = _run(
                _cli_cmd("nihongo-check")
                + ["inbox", "propose", "--scene", "formal", "--kind", "forbidden", "--value", "ご査収のほど", "--json"],
                env=env,
            )
            self.assertEqual(r_prop.returncode, 0, r_prop.stdout + r_prop.stderr)
            new_id = json.loads(r_prop.stdout)["entry"]["id"]

            r_appr = _run(_cli_cmd("nihongo-check") + ["inbox", "approve", new_id], env=env)
            self.assertEqual(r_appr.returncode, 0, r_appr.stdout + r_appr.stderr)

            with open(os.path.join(sync_home, "profile.md"), "r", encoding="utf-8") as f:
                synced_prof = f.read()
            self.assertIn("既存のNG", synced_prof)
            self.assertIn("ご査収のほど", synced_prof)
            self.assertNotIn("語尾は「だね」寄り", synced_prof)

            # 前からあった無関係な未確認候補は pending のまま残っている
            r_list = _run(_cli_cmd("nihongo-check") + ["inbox", "list", "--json"], env=env)
            self.assertEqual(r_list.returncode, 0, r_list.stdout + r_list.stderr)
            pending_ids = [e["id"] for e in json.loads(r_list.stdout)["items"] if e.get("status") == "pending"]
            self.assertEqual(pending_ids, [pre_id])

            # 4. 診断: nihongo-check doctor --json で保存先統一・不一致ゼロを確認
            r_doc = _run(_cli_cmd("nihongo-check") + ["doctor", "--json"], env=env)
            self.assertEqual(r_doc.returncode, 0, r_doc.stdout + r_doc.stderr)
            doc = json.loads(r_doc.stdout)
            self.assertEqual(os.path.normcase(doc["home"]), os.path.normcase(os.path.abspath(sync_home)))
            self.assertEqual(doc["home_mismatches"], [])
            clients_by_target = {c["target"]: c for c in doc["mcp_clients"]}
            self.assertTrue(clients_by_target["claude-code"]["nihongo_configured"])
            self.assertFalse(clients_by_target["antigravity"]["installed"])

            # 5. 動作確認: 0トークン diff --auto-profile（同期先NG検出＋必ず脱落検出＋ください→下さい誤検知なし）
            orig_md = os.path.join(td, "orig.md")
            draft_md = os.path.join(td, "draft.md")
            with open(orig_md, "w", encoding="utf-8") as f:
                f.write("15時までに必ず確認してください。\n")
            with open(draft_md, "w", encoding="utf-8") as f:
                f.write("15時までに資料をご査収のほどご確認下さい。\n")
            r_diff = _run(
                _cli_cmd("nihongo-check") + ["diff", "--auto-profile", "--scene", "formal", "--json", orig_md, draft_md],
                env=env,
            )
            self.assertEqual(r_diff.returncode, 1, r_diff.stdout + r_diff.stderr)
            diff_data = json.loads(r_diff.stdout)
            joined = "\n".join(diff_data["findings"])
            self.assertIn("ご査収のほど", joined)
            self.assertIn("必ず", joined)
            self.assertNotIn("お願い", joined)

            # 6. MCP 自己診断と、.claude.json に書き込まれた実コマンドそのままでの本物 stdio 往復
            r_self = _run(_cli_cmd("nihongo-mcp") + ["--self-test"], env=env)
            self.assertEqual(r_self.returncode, 0, r_self.stdout + r_self.stderr)

            with open(claude_cfg_path, "r", encoding="utf-8") as f:
                claude_cfg = json.load(f)
            nihongo_entry = claude_cfg["mcpServers"]["nihongo"]
            mcp_spawn_cmd = [nihongo_entry["command"], *nihongo_entry.get("args", [])]
            reqs = "\n".join([
                json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05"}}),
                json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "get_profile", "arguments": {}}}),
                json.dumps({"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "check_meaning_diff", "arguments": {"orig": "資料を送ります。", "draft": "資料をご査収のほどお願いいたします。", "scene": "formal"}}}),
            ]) + "\n"
            r_mcp = _run(mcp_spawn_cmd, env=env, stdin_text=reqs)
            self.assertEqual(r_mcp.returncode, 0, r_mcp.stderr)
            resps = [json.loads(line) for line in r_mcp.stdout.splitlines() if line.strip()]
            self.assertEqual(len(resps), 3)
            prof_payload = json.loads(resps[1]["result"]["content"][0]["text"])
            self.assertIn("既存のNG", prof_payload["display_markdown"])
            self.assertIn("ご査収のほど", prof_payload["display_markdown"])
            diff_payload = json.loads(resps[2]["result"]["content"][0]["text"])
            self.assertFalse(diff_payload["clean"])
            self.assertTrue(any("ご査収のほど" in x for x in diff_payload["findings"]))

            # 7. 解除コマンド: --remove で他の MCP サーバー設定を壊さずに nihongo だけ外れる
            r_rem = _run(_cli_cmd("nihongo-mcp") + ["init", "--target", "all", "--remove"], env=env)
            self.assertEqual(r_rem.returncode, 0, r_rem.stdout + r_rem.stderr)
            with open(claude_cfg_path, "r", encoding="utf-8") as f:
                after_rem = json.load(f)
            self.assertNotIn("nihongo", after_rem["mcpServers"])
            self.assertIn("other-server", after_rem["mcpServers"])

    def test_setup_md_template_in_lp_stays_aligned(self):
        """LP が生成する nihongo-setup.md の手順に危険コマンド（--all / python3 固定）が戻っていないことを確認。"""
        with open(DOCS_HTML, "r", encoding="utf-8") as f:
            html = f.read()
        self.assertIn("nihongo-check --version", html)
        self.assertIn("nihongo-mcp init --target all", html)
        self.assertIn("nihongo-check inbox approve <ID>", html)
        self.assertIn("nihongo-mcp --self-test", html)
        self.assertIn("nihongo-check doctor", html)
        self.assertIn("nihongo-mcp init --target all --remove", html)
        self.assertNotIn("inbox approve --all", html)


if __name__ == "__main__":
    unittest.main()
