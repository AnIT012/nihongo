"""v3.1.0 リリース前のエッジケース一斉監査で発見・修正した8件の回帰テスト。"""
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

import check_meaning as cm_mod  # noqa: E402
import gdrive_storage as gd_mod  # noqa: E402
import inbox as inbox_mod  # noqa: E402
import mcp_server as mcp_mod  # noqa: E402
import revert_broken as rb_mod  # noqa: E402
from test_v31_sync_and_mcp import FakeDriveBackend  # noqa: E402


class EdgeCaseRegressionTests(unittest.TestCase):
    def test_01_mcp_check_meaning_diff_empty_orig_has_no_false_positives(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            srv = mcp_mod.NihongoMcpServer(home=d)
            # Clean newly written formal email with orig="" must pass cleanly
            res_clean = srv._tool_check_meaning_diff({
                "orig": "",
                "draft": "明日の15時に会議があります。必ずご確認ください。不備はありません。",
                "scene": "formal",
            })
            self.assertTrue(res_clean["clean"], res_clean["findings"])
            self.assertEqual(res_clean["count"], 0)

            # Still catches formal scene violations and forbidden words when orig=""
            res_bad = srv._tool_check_meaning_diff({
                "orig": "",
                "draft": "確認お願いしますっす！",
                "scene": "formal",
            })
            self.assertFalse(res_bad["clean"])

    def test_02_propose_and_apply_do_not_false_dedup_on_template_or_longer_words(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            store = inbox_mod.LocalFileStorage(home=d)
            store.write_profile_text(inbox_mod.DEFAULT_PROFILE_TEMPLATE)

            # "私" appears in "# 私の書き方", "絵文字" appears in [formal] description -> must NOT block!
            r_fp = inbox_mod.propose_entry(
                scene="common", kind="first_person", value="私", storage=store
            )
            self.assertTrue(r_fp["created"], r_fp)

            r_emoji = inbox_mod.propose_entry(
                scene="formal", kind="forbidden", value="絵文字", storage=store
            )
            self.assertTrue(r_emoji["created"], r_emoji)

            # Shorter forbidden expression "ご査収" must NOT be blocked by longer "ご査収のほど"
            r_long = inbox_mod.add_profile_rule_direct(
                scene="common", kind="forbidden", value="ご査収のほど", storage=store
            )
            self.assertTrue(r_long["added"])
            r_short_prop = inbox_mod.propose_entry(
                scene="common", kind="forbidden", value="ご査収", storage=store
            )
            self.assertTrue(r_short_prop["created"], r_short_prop)
            appr = inbox_mod.approve_entries([r_short_prop["entry"]["id"]], storage=store)
            self.assertEqual(appr["approved_count"], 1)
            self.assertTrue(appr["profile_updated"])
            parsed = inbox_mod.parse_profile_structured(store.read_profile_text())
            self.assertIn("ご査収のほど", parsed["common"]["forbidden"])
            self.assertIn("ご査収", parsed["common"]["forbidden"])

    def test_03_parse_profile_structured_preserves_colons_and_quoted_periods(self) -> None:
        raw = (
            "# 私の書き方\n\n"
            "## [common]\n"
            "- 14:00以降の会議は入れない\n"
            "- URLは https://example.com を使う\n"
            "- 結論先出し：1文目で答えを書く\n"
            "- 書く時の考え方：語尾に「。」を付けない。短く書く\n"
        )
        parsed = inbox_mod.parse_profile_structured(raw)
        rules = parsed["common"]["rules"]
        self.assertIn("14:00以降の会議は入れない", rules)
        self.assertIn("URLは https://example.com を使う", rules)
        self.assertIn("結論先出し：1文目で答えを書く", rules)
        self.assertIn("語尾に「。」を付けない", rules)
        self.assertIn("短く書く", rules)

    def test_04_revert_broken_reverts_added_degree_words(self) -> None:
        orig = "開始は15時です。"
        draft = "開始は15時頃です。"
        fixed, log = rb_mod.one_pass(orig, draft)
        self.assertEqual(fixed, orig)
        self.assertTrue(len(log) >= 1)

    def test_05_revert_broken_reinserts_deleted_sentence_with_time_or_fullwidth(self) -> None:
        orig_time = "最初の案内です。\n15:00からシステム保守と移行作業を実施します。\n最後の案内です。"
        draft_time = "最初の案内です。\n最後の案内です。"
        fixed_time, _ = rb_mod.one_pass(orig_time, draft_time)
        self.assertIn("15:00からシステム保守と移行作業を実施します。", fixed_time)

        orig_fw = "最初の案内です。\n（注）データ移行とアカウント権限の確認を実施します。\n最後の案内です。"
        draft_fw = "最初の案内です。\n最後の案内です。"
        fixed_fw, _ = rb_mod.one_pass(orig_fw, draft_fw)
        self.assertIn("（注）データ移行とアカウント権限の確認を実施します。", fixed_fw)

    def test_06_check_meaning_norm_handles_zero_padded_times_seconds_and_ipv4_ports(self) -> None:
        # Zero-padded time matches Japanese 9時 / 午前9時
        self.assertEqual(cm_mod.check("09:00に開始します。", "午前9時に開始します。"), [])
        self.assertEqual(cm_mod.check("09:05に開始します。", "9時5分に開始します。"), [])

        # HH:MM:SS and IPv4 URL with 2-digit port must NOT be corrupted
        self.assertEqual(cm_mod.norm("10:30:00"), "10:30:00")
        self.assertEqual(cm_mod.norm("http://127.0.0.1:80/api"), "http://127.0.0.1:80/api")
        self.assertEqual(
            cm_mod.check("詳細は http://127.0.0.1:80/api です。", "詳細は http://127.0.0.1:80/api です。"),
            [],
        )

    def test_07_gdrive_write_researches_after_cached_404_instead_of_duplicating(self) -> None:
        backend = FakeDriveBackend()
        store = gd_mod.GoogleDriveStorage(access_token="tok_initial", http_transport=backend.transport)
        store.write_profile_text("# v1\n")
        old_fid = store._file_id_cache["profile.md"]
        folder_id = store._folder_id_cache

        # Another device deletes old_fid and creates a fresh remote profile.md
        del backend.files[old_fid]
        backend.files["fid_remote_new"] = {
            "name": "profile.md",
            "mimeType": "text/markdown",
            "parents": [folder_id],
            "content": b"# remote v2\n",
        }

        # Device A writes -> must re-search and PATCH fid_remote_new, NOT create a duplicate file
        store.write_profile_text("# local v3\n")
        profile_files = [
            fid for fid, meta in backend.files.items() if meta["name"] == "profile.md"
        ]
        self.assertEqual(profile_files, ["fid_remote_new"])
        self.assertEqual(store.read_profile_text(), "# local v3\n")

    def test_08_mcp_null_optional_args_and_atomic_batch_pii_validation(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            srv = mcp_mod.NihongoMcpServer(home=d)
            p1 = srv._tool_propose_profile_entry({"scene": "common", "kind": "forbidden", "value": "表現A"})
            p2 = srv._tool_propose_profile_entry({"scene": "common", "kind": "forbidden", "value": "表現B"})
            id1, id2 = p1["entry"]["id"], p2["entry"]["id"]

            # JSON null for request/reason must not become literal "None"
            chk = srv._tool_check_meaning_diff({"orig": "確認します。", "draft": "確認します。", "request": None})
            self.assertTrue(chk["clean"])

            # Invalid PII in batch reject reason must fail BEFORE approving id1 into profile.md
            with self.assertRaises(ValueError):
                srv._tool_review_inbox_entry({
                    "action": "batch",
                    "approve_ids": [id1],
                    "reject_ids": [id2],
                    "reason": "test@example.com",
                    "confirmed_by_user": True,
                })
            self.assertFalse(srv._tool_get_profile({})["exists"])

            # Reject with reason=None stores empty string, not "None"
            srv._tool_review_inbox_entry({
                "action": "reject",
                "ids": [id2],
                "reason": None,
                "confirmed_by_user": True,
            })
            hist = inbox_mod.list_inbox(status="rejected", storage=srv.storage)
            self.assertEqual(hist[0]["decision_note"], "")


if __name__ == "__main__":
    unittest.main()
