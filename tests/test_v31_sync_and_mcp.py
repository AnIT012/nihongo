"""v3.1 拡張機能（2層プロファイル・同期フォルダ検出・チャット内完結MCP）のテスト。"""
from __future__ import annotations

import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(HERE, ".."))
SCRIPTS_DIR = os.path.join(REPO_ROOT, "nihongo", "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

import inbox as inbox_mod  # noqa: E402
import mcp_server as mcp_mod  # noqa: E402


class LayeredProfileAndSyncTests(unittest.TestCase):
    def test_layered_profile_merges_global_and_project(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            global_home = os.path.join(d, "global_home")
            proj_root = os.path.join(d, "client_proj")
            proj_sub = os.path.join(proj_root, "docs", "drafts")
            os.makedirs(global_home, exist_ok=True)
            os.makedirs(os.path.join(proj_root, ".nihongo"), exist_ok=True)
            os.makedirs(proj_sub, exist_ok=True)

            global_prof = os.path.join(global_home, "profile.md")
            proj_prof = os.path.join(proj_root, ".nihongo", "profile.md")
            with open(global_prof, "w", encoding="utf-8", newline="\n") as f:
                f.write("# 私の書き方\n\n## [common]\n- 絶対に言わない表現：「いただけますと幸いです」\n")
            with open(proj_prof, "w", encoding="utf-8", newline="\n") as f:
                f.write("# 案件ルール\n\n## [common]\n- 絶対に言わない表現：「ご査収のほど」\n\n## [formal]\n- 口調・記号：語尾は丁寧語で統一\n")

            found = inbox_mod.find_project_profile(proj_sub, global_profile_path=global_prof)
            self.assertEqual(os.path.realpath(found or ""), os.path.realpath(proj_prof))

            srv = mcp_mod.NihongoMcpServer(home=global_home)
            prof_res = srv._tool_get_profile({"project_dir": proj_sub})
            self.assertEqual(len(prof_res["layers"]), 2)
            self.assertIn("いただけますと幸いです", prof_res["forbidden"])
            self.assertIn("ご査収のほど", prof_res["forbidden"])

            chk = srv._tool_check_meaning_diff({
                "orig": "",
                "draft": "資料をご査収のほど、ご確認いただけますと幸いです。",
                "scene": "formal",
                "project_dir": proj_sub,
            })
            self.assertFalse(chk["clean"])
            joined = "\n".join(chk["findings"])
            self.assertIn("ご査収のほど", joined)
            self.assertIn("いただけますと幸いです", joined)

    def test_detect_sync_folders_finds_cloud_roots(self) -> None:
        with tempfile.TemporaryDirectory() as fake_home:
            os.makedirs(os.path.join(fake_home, "Dropbox"))
            os.makedirs(os.path.join(fake_home, "Google Drive", "My Drive"))
            found = inbox_mod.detect_sync_folders(home_dir=fake_home)
            providers = {item["provider"] for item in found}
            self.assertIn("Dropbox", providers)
            self.assertIn("Google Drive", providers)

    def test_security_audit_regressions_inbox_and_layers(self) -> None:
        # 1. reject_entries blocks PII in reason
        with tempfile.TemporaryDirectory() as d:
            store = inbox_mod.LocalFileStorage(home=d)
            p = inbox_mod.propose_entry(scene="common", kind="forbidden", value="ご査収のほど", storage=store)
            with self.assertRaises(ValueError):
                inbox_mod.reject_entries([p["entry"]["id"]], reason="連絡先 test@example.com", storage=store)

        # 2. Tagless project overlay + ### subheading preserved in 2-layer merge
        base = "# 私の書き方\n\n## [common]\n- 絶対に言わない表現：「いただけますと幸いです」\n\n## [work]\n### PR向け\n- 短めに書く\n"
        overlay = "- 絶対に言わない表現：「ご査収のほど」\n"
        merged = inbox_mod.merge_profile_texts(base, overlay)
        self.assertIn("ご査収のほど", merged)
        self.assertIn("いただけますと幸いです", merged)
        self.assertIn("### PR向け", merged)
        self.assertIn("- 短めに書く", merged)

        # 3. Non-existent / whitespace project_dir handled safely
        self.assertIsNone(inbox_mod.find_project_profile("   "))
        self.assertIsNone(inbox_mod.find_project_profile("/nonexistent_nihongo_dir_12345"))

    def test_structured_profile_parse_and_remove(self) -> None:
        raw = (
            "# 私の書き方\n\n"
            "## [common]\n"
            "- 一人称：私\n"
            "- 絶対に言わない表現：「いただけますと幸いです」、「もし、よろしければ」、（例：〜）\n"
            "- 書く時の考え方：理由の後ろは読点を打たない。短く書く\n\n"
            "## [work]\n"
            "- 場面：社内チャット・PR\n"
            "- 口調・記号：簡潔なです・ます\n"
        )
        parsed = inbox_mod.parse_profile_structured(raw)
        self.assertEqual(parsed["common"]["first_person"], "私")
        self.assertEqual(
            parsed["common"]["forbidden"],
            ["いただけますと幸いです", "もし、よろしければ"],
        )
        self.assertEqual(
            parsed["common"]["rules"],
            ["理由の後ろは読点を打たない", "短く書く"],
        )
        self.assertEqual(parsed["work"]["rules"], ["簡潔なです・ます"])
        self.assertEqual(parsed["formal"]["forbidden"], [])

        with tempfile.TemporaryDirectory() as d:
            store = inbox_mod.LocalFileStorage(home=d)
            p1 = inbox_mod.propose_entry(scene="common", kind="forbidden", value="ご査収のほど", storage=store)
            p2 = inbox_mod.propose_entry(scene="common", kind="forbidden", value="恐れ入りますが", storage=store)
            p3 = inbox_mod.propose_entry(scene="work", kind="first_person", value="私", storage=store)
            inbox_mod.approve_entries(
                [p1["entry"]["id"], p2["entry"]["id"], p3["entry"]["id"]],
                storage=store,
            )

            # Surgical removal preserves remaining forbidden expression and other fields
            rem = inbox_mod.remove_forbidden_from_profile(
                scene="common", value="ご査収のほど", storage=store
            )
            self.assertTrue(rem["removed"])
            after = inbox_mod.parse_profile_structured(store.read_profile_text())
            self.assertEqual(after["common"]["forbidden"], ["恐れ入りますが"])
            self.assertEqual(after["common"]["first_person"], "私")

            # Removing the last forbidden item leaves empty list cleanly
            rem2 = inbox_mod.remove_forbidden_from_profile(
                scene="common", value="恐れ入りますが", storage=store
            )
            self.assertTrue(rem2["removed"])
            after2 = inbox_mod.parse_profile_structured(store.read_profile_text())
            self.assertEqual(after2["common"]["forbidden"], [])

            # Removing nonexistent item returns removed=False without crashing
            rem3 = inbox_mod.remove_forbidden_from_profile(
                scene="common", value="存在しない表現", storage=store
            )
            self.assertFalse(rem3["removed"])


class InChatMcpWorkflowTests(unittest.TestCase):
    def test_in_chat_profile_summary_inbox_approval_and_forbidden_removal(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            srv = mcp_mod.NihongoMcpServer(home=d)

            empty_prof = srv._tool_get_profile({})
            self.assertIn("まだ作成されていません", empty_prof["display_markdown"])

            p1 = srv._tool_propose_profile_entry({
                "scene": "common",
                "kind": "forbidden",
                "value": "いただけますと幸いです",
                "reason": "結びが硬すぎる",
            })
            p2 = srv._tool_propose_profile_entry({
                "scene": "common",
                "kind": "forbidden",
                "value": "恐れ入りますが",
            })
            listed = srv._tool_list_inbox({})
            self.assertEqual(listed["count"], 2)
            self.assertIn("承認待ちの候補（2件）", listed["display_markdown"])
            self.assertIn("いただけますと幸いです", listed["display_markdown"])

            appr = srv._tool_review_inbox_entry({
                "action": "approve",
                "ids": [p1["entry"]["id"], p2["entry"]["id"]],
                "confirmed_by_user": True,
            })
            self.assertEqual(appr["approved_count"], 2)

            prof = srv._tool_get_profile({})
            self.assertIn("今のあなたの日本語ルール", prof["display_markdown"])
            self.assertIn("「いただけますと幸いです」", prof["display_markdown"])
            self.assertIn("いただけますと幸いです", prof["structured"]["common"]["forbidden"])

            dry = srv._tool_remove_profile_forbidden({
                "scene": "common",
                "value": "いただけますと幸いです",
            })
            self.assertTrue(dry["dry_run"])
            self.assertTrue(dry["requires_user_confirmation"])
            self.assertIn("いただけますと幸いです", srv._tool_get_profile({})["forbidden"])

            rem = srv._tool_remove_profile_forbidden({
                "scene": "common",
                "value": "いただけますと幸いです",
                "confirmed_by_user": True,
            })
            self.assertTrue(rem["removed"])
            after = srv._tool_get_profile({})
            self.assertNotIn("いただけますと幸いです", after["forbidden"])
            self.assertIn("恐れ入りますが", after["forbidden"])

    def test_strict_hitl_hides_and_blocks_remove_profile_forbidden(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            srv = mcp_mod.NihongoMcpServer(home=d, strict_hitl=True)
            names = [t["name"] for t in srv._exposed_tools()]
            self.assertNotIn("review_inbox_entry", names)
            self.assertNotIn("remove_profile_forbidden", names)
            with self.assertRaises(PermissionError):
                srv._tool_remove_profile_forbidden({
                    "scene": "common",
                    "value": "ご査収のほど",
                    "confirmed_by_user": True,
                })


if __name__ == "__main__":
    unittest.main()
