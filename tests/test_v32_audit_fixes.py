import json
import os
import sys
import tempfile
import unittest
from unittest import mock

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SCRIPTS_DIR = os.path.join(ROOT, "nihongo", "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

import check_meaning  # noqa: E402
import cli as cli_mod  # noqa: E402
import inbox as inbox_mod  # noqa: E402
import mcp_server as mcp_mod  # noqa: E402


class TestV32AuditFixes(unittest.TestCase):
    def test_config_json_unifies_home_and_precedence(self):
        with tempfile.TemporaryDirectory() as td:
            cfg = os.path.join(td, "config.json")
            sync_dir = os.path.join(td, "Dropbox", "nihongo")
            env_dir = os.path.join(td, "EnvHome")
            explicit_dir = os.path.join(td, "ExplicitHome")
            with mock.patch.dict(os.environ, {"NIHONGO_CONFIG": cfg, "NIHONGO_HOME": ""}, clear=False):
                inbox_mod.save_configured_home(sync_dir)
                self.assertEqual(os.path.normcase(inbox_mod.get_nihongo_home()), os.path.normcase(os.path.abspath(sync_dir)))
                # explicit --home overrides config.json
                self.assertEqual(
                    os.path.normcase(inbox_mod.get_nihongo_home(explicit_dir)),
                    os.path.normcase(os.path.abspath(explicit_dir)),
                )
                # NIHONGO_HOME overrides config.json
                with mock.patch.dict(os.environ, {"NIHONGO_HOME": env_dir}, clear=False):
                    self.assertEqual(
                        os.path.normcase(inbox_mod.get_nihongo_home()),
                        os.path.normcase(os.path.abspath(env_dir)),
                    )

    def test_migrate_profile_to_home_never_overwrites(self):
        with tempfile.TemporaryDirectory() as td:
            src = os.path.join(td, "local")
            dst = os.path.join(td, "dropbox_nihongo")
            os.makedirs(src, exist_ok=True)
            with open(os.path.join(src, "profile.md"), "w", encoding="utf-8") as f:
                f.write("# 私の書き方\n- 絶対に言わない表現：「元の設定」\n")

            res1 = inbox_mod.migrate_profile_to_home(dst, source_home=src)
            self.assertEqual(res1["copied"], ["profile.md"])
            with open(os.path.join(dst, "profile.md"), encoding="utf-8") as f:
                self.assertIn("元の設定", f.read())

            # Modify destination and re-run migration: must NOT overwrite destination
            with open(os.path.join(dst, "profile.md"), "w", encoding="utf-8") as f:
                f.write("# 私の書き方\n- 絶対に言わない表現：「新しい設定」\n")
            res2 = inbox_mod.migrate_profile_to_home(dst, source_home=src)
            self.assertEqual(res2["copied"], [])
            self.assertEqual(res2["skipped"], ["profile.md"])
            with open(os.path.join(dst, "profile.md"), encoding="utf-8") as f:
                self.assertIn("新しい設定", f.read())

    def test_init_mcp_config_unchanged_creates_no_duplicate_bak(self):
        with tempfile.TemporaryDirectory() as td:
            cfg = os.path.join(td, "mcp.json")
            res1 = mcp_mod.init_mcp_config(target="cursor", config_path=cfg)
            self.assertFalse(res1["unchanged"])
            self.assertIsNone(res1["backup_path"])

            # Running again with identical args must be unchanged and create zero .bak files
            res2 = mcp_mod.init_mcp_config(target="cursor", config_path=cfg)
            self.assertTrue(res2["unchanged"])
            self.assertIsNone(res2["backup_path"])
            baks = [n for n in os.listdir(td) if n.endswith(".bak")]
            self.assertEqual(baks, [])

    def test_remove_mcp_config_preserves_other_servers(self):
        with tempfile.TemporaryDirectory() as td:
            cfg = os.path.join(td, "mcp.json")
            with open(cfg, "w", encoding="utf-8") as f:
                json.dump({"mcpServers": {"other": {"command": "node", "args": []}}}, f)

            mcp_mod.init_mcp_config(target="cursor", config_path=cfg)
            rm = mcp_mod.remove_mcp_config(target="cursor", config_path=cfg)
            self.assertTrue(rm["removed"])
            self.assertIsNotNone(rm["backup_path"])
            with open(cfg, encoding="utf-8") as f:
                data = json.load(f)
            self.assertNotIn("nihongo", data["mcpServers"])
            self.assertIn("other", data["mcpServers"])

    def test_windows_store_claude_desktop_detection(self):
        with tempfile.TemporaryDirectory() as td:
            appdata = os.path.join(td, "Roaming")
            localapp = os.path.join(td, "Local")
            store_dir = os.path.join(localapp, "Packages", "Claude_pzs8sxrjxfjjc", "LocalCache", "Roaming", "Claude")
            os.makedirs(store_dir, exist_ok=True)
            with mock.patch.dict(os.environ, {"APPDATA": appdata, "LOCALAPPDATA": localapp}, clear=False):
                resolved = mcp_mod.resolve_client_config_path("claude-desktop", platform="win32")
                self.assertEqual(
                    os.path.normcase(resolved),
                    os.path.normcase(os.path.join(store_dir, "claude_desktop_config.json")),
                )

    def test_check_meaning_kudasai_kanji_no_false_positive(self):
        orig = "資料をご確認ください。"
        draft = "資料をご確認下さい。"
        findings = check_meaning.check(orig, draft)
        self.assertEqual(findings, [])

    def test_doctor_detects_home_mismatch(self):
        with tempfile.TemporaryDirectory() as td:
            cli_home = os.path.join(td, "cli_home")
            mcp_home = os.path.join(td, "dropbox_home")
            os.makedirs(cli_home, exist_ok=True)
            cfg = os.path.join(td, "antigravity_mcp.json")
            mcp_mod.init_mcp_config(target="antigravity", config_path=cfg, home=mcp_home)

            def fake_resolve(target, **_kw):
                return cfg if target == "antigravity" else os.path.join(td, f"missing_{target}.json")

            def fake_installed(target, **_kw):
                return target == "antigravity"

            ns = cli_mod.build_parser().parse_args(["doctor", "--home", cli_home, "--json"])
            import io
            buf = io.StringIO()
            with mock.patch.object(mcp_mod, "resolve_client_config_path", side_effect=fake_resolve), \
                 mock.patch.object(mcp_mod, "is_client_installed", side_effect=fake_installed), \
                 mock.patch("sys.stdout", buf):
                rc = cli_mod.cmd_doctor(ns)
            self.assertEqual(rc, 0)
            rep = json.loads(buf.getvalue())
            self.assertEqual(len(rep["home_mismatches"]), 1)
            self.assertEqual(rep["home_mismatches"][0]["target"], "antigravity")


if __name__ == "__main__":
    unittest.main()
