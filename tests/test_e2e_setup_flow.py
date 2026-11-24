import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SCRIPTS_DIR = os.path.join(ROOT, "nihongo", "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

import cli as cli_mod  # noqa: E402
import inbox as inbox_mod  # noqa: E402
import mcp_server as mcp_mod  # noqa: E402


class TestE2ESetupFlow(unittest.TestCase):
    """導入ガイドの一気通貫E2E（既存profile保護・未確認受信箱の非巻き込み・同期保存先統一・MCP往復）。"""

    def test_end_to_end_sync_setup_id_only_approve_and_mcp_roundtrip(self):
        with tempfile.TemporaryDirectory() as td:
            local_home = os.path.join(td, "local_home")
            sync_home = os.path.join(td, "Dropbox", "nihongo")
            cfg_pointer = os.path.join(local_home, "config.json")
            mcp_cfg = os.path.join(td, "antigravity_mcp.json")
            os.makedirs(local_home, exist_ok=True)

            # 1. Existing local profile + unrelated pre-existing pending inbox item
            existing_p = inbox_mod.default_profile_path(local_home)
            with open(existing_p, "w", encoding="utf-8") as f:
                f.write(inbox_mod.DEFAULT_PROFILE_TEMPLATE.replace("- 絶対に言わない表現：", "- 絶対に言わない表現：「既存のNG」", 1))

            pre_existing = inbox_mod.propose_entry(
                scene="casual",
                kind="tone",
                value="語尾は「だね」寄り",
                source="preexisting",
                inbox_path=inbox_mod.default_inbox_path(local_home),
                profile_path=existing_p,
            )

            # 2. Switch to Dropbox sync home via migration + config.json pointer + MCP init
            with mock.patch.dict(os.environ, {"NIHONGO_CONFIG": cfg_pointer, "NIHONGO_HOME": ""}, clear=False):
                mig = inbox_mod.migrate_profile_to_home(sync_home, source_home=local_home)
                self.assertIn("profile.md", mig["copied"])
                self.assertIn("inbox.jsonl", mig["copied"])
                inbox_mod.save_configured_home(sync_home)

                init_res = mcp_mod.init_mcp_config(target="antigravity", config_path=mcp_cfg, home=sync_home)
                self.assertFalse(init_res["unchanged"])
                # Re-running identical init must be no-op with zero .bak
                init_res2 = mcp_mod.init_mcp_config(target="antigravity", config_path=mcp_cfg, home=sync_home)
                self.assertTrue(init_res2["unchanged"])
                self.assertIsNone(init_res2["backup_path"])

                # 3. Propose a new forbidden word and approve ONLY its returned ID
                new_entry = inbox_mod.propose_entry(
                    scene="formal",
                    kind="forbidden",
                    value="ご査収のほど",
                    source="setup-md",
                )
                new_id = new_entry["entry"]["id"]
                pre_id = pre_existing["entry"]["id"]
                approved = inbox_mod.approve_entries(entry_ids=[new_id])
                self.assertEqual(approved["approved_count"], 1)
                self.assertEqual(approved["results"][0]["id"], new_id)

                # Verify existing profile rule preserved, new rule added, and unrelated pending entry STILL pending
                prof = inbox_mod.read_profile()
                self.assertIn("既存のNG", prof["raw"])
                self.assertIn("ご査収のほど", prof["raw"])
                self.assertNotIn("語尾は「だね」寄り", prof["raw"])
                pending = [e for e in inbox_mod.load_inbox() if e.get("status") == "pending"]
                self.assertEqual([e["id"] for e in pending], [pre_id])

                # 4. Doctor sees unified home with 0 mismatches
                def fake_resolve(target, **_kw):
                    return mcp_cfg if target == "antigravity" else os.path.join(td, f"absent_{target}.json")

                def fake_installed(target, **_kw):
                    return target == "antigravity"

                ns = cli_mod.build_parser().parse_args(["doctor", "--json"])
                buf = io.StringIO()
                with mock.patch.object(mcp_mod, "resolve_client_config_path", side_effect=fake_resolve), \
                     mock.patch.object(mcp_mod, "is_client_installed", side_effect=fake_installed), \
                     mock.patch("sys.stdout", buf):
                    rc = cli_mod.cmd_doctor(ns)
                self.assertEqual(rc, 0)
                doc = json.loads(buf.getvalue())
                self.assertEqual(doc["home_mismatches"], [])
                self.assertEqual(os.path.normcase(doc["home"]), os.path.normcase(os.path.abspath(sync_home)))

                # 5. Live MCP stdio subprocess roundtrip reads the exact unified sync home without --home flag
                env = os.environ.copy()
                env["PYTHONUTF8"] = "1"
                env["NIHONGO_CONFIG"] = cfg_pointer
                env.pop("NIHONGO_HOME", None)
                reqs = "\n".join([
                    json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05"}}),
                    json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "get_profile", "arguments": {}}}),
                    json.dumps({"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "check_meaning_diff", "arguments": {"orig": "資料を送ります。", "draft": "資料をご査収のほどお願いいたします。", "scene": "formal"}}}),
                ]) + "\n"
                proc = subprocess.run(
                    [sys.executable, os.path.join(SCRIPTS_DIR, "mcp_server.py")],
                    input=reqs,
                    text=True,
                    encoding="utf-8",
                    capture_output=True,
                    env=env,
                    timeout=15,
                )
                self.assertEqual(proc.returncode, 0, proc.stderr)
                resps = [json.loads(line) for line in proc.stdout.splitlines() if line.strip()]
                self.assertEqual(len(resps), 3)
                prof_payload = json.loads(resps[1]["result"]["content"][0]["text"])
                self.assertIn("ご査収のほど", prof_payload["display_markdown"])
                diff_payload = json.loads(resps[2]["result"]["content"][0]["text"])
                self.assertFalse(diff_payload["clean"])
                self.assertTrue(any("ご査収のほど" in f for f in diff_payload["findings"]))


if __name__ == "__main__":
    unittest.main()
