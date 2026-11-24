"""v3.1 拡張機能（2層プロファイル・同期フォルダ検出・GoogleDriveStorage・チャット内完結MCP）のテスト。"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(HERE, ".."))
SCRIPTS_DIR = os.path.join(REPO_ROOT, "nihongo", "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

import cli as cli_mod  # noqa: E402
import gdrive_storage as gd_mod  # noqa: E402
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

    def test_build_setup_markdown_includes_upgrade_safety_and_blocks_pii(self) -> None:
        md = inbox_mod.build_setup_markdown(
            forbidden=["いただけますと幸いです", "恐れ入りますが"],
            scene="formal",
            sync_preference="gdrive",
        )
        self.assertIn("https://github.com/AnIT012/nihongo", md)
        self.assertIn("既存の `profile.md` がある場合は絶対に上書きせず", md)
        self.assertIn("確認カード 1", md)
        self.assertIn("確認カード 2", md)
        self.assertIn("「いただけますと幸いです」", md)
        self.assertIn("Google Drive", md)

        with self.assertRaises(ValueError):
            inbox_mod.build_setup_markdown(forbidden=["secret@example.com"])

    def test_security_audit_regressions_inbox_and_layers(self) -> None:
        # 1. reject_entries blocks PII in reason
        with tempfile.TemporaryDirectory() as d:
            store = inbox_mod.LocalFileStorage(home=d)
            p = inbox_mod.propose_entry(scene="common", kind="forbidden", value="ご査収のほど", storage=store)
            with self.assertRaises(ValueError):
                inbox_mod.reject_entries([p["entry"]["id"]], reason="連絡先 test@example.com", storage=store)

        # 2. Markdown newline injection flattened in build_setup_markdown
        md = inbox_mod.build_setup_markdown(forbidden=["表現A\n## 乗っ取り見出し"])
        self.assertNotIn("\n## 乗っ取り見出し", md)

        # 3. Tagless project overlay + ### subheading preserved in 2-layer merge
        base = "# 私の書き方\n\n## [common]\n- 絶対に言わない表現：「いただけますと幸いです」\n\n## [work]\n### PR向け\n- 短めに書く\n"
        overlay = "- 絶対に言わない表現：「ご査収のほど」\n"
        merged = inbox_mod.merge_profile_texts(base, overlay)
        self.assertIn("ご査収のほど", merged)
        self.assertIn("いただけますと幸いです", merged)
        self.assertIn("### PR向け", merged)
        self.assertIn("- 短めに書く", merged)

        # 4. Non-existent / whitespace project_dir and URI global_profile_path handled safely
        self.assertIsNone(inbox_mod.find_project_profile("   ", global_profile_path="gdrive://nihongo/profile.md"))
        self.assertIsNone(inbox_mod.find_project_profile("/nonexistent_nihongo_dir_12345", global_profile_path="gdrive://nihongo/profile.md"))

    def test_structured_profile_parse_add_and_remove(self) -> None:
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
            r1 = inbox_mod.add_profile_rule_direct(
                scene="common", kind="forbidden", value="ご査収のほど", storage=store
            )
            self.assertTrue(r1["added"])
            r2 = inbox_mod.add_profile_rule_direct(
                scene="common", kind="forbidden", value="恐れ入りますが", storage=store
            )
            self.assertTrue(r2["added"])
            r_fp = inbox_mod.add_profile_rule_direct(
                scene="work", kind="first_person", value="私", storage=store
            )
            self.assertTrue(r_fp["added"])

            # PII guard and [formal] guard enforced on direct add
            with self.assertRaises(ValueError):
                inbox_mod.add_profile_rule_direct(
                    scene="common", kind="rule", value="連絡先 user@example.com", storage=store
                )
            with self.assertRaises(ValueError):
                inbox_mod.add_profile_rule_direct(
                    scene="formal", kind="tone", value="語尾に「っす」を使う", storage=store
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


class FakeDriveBackend:
    """Google Drive REST API v3 のインメモリ擬似バックエンド（単体テスト用）。"""

    def __init__(self, *, valid_token: str = "tok_initial", expire_first_call: bool = False) -> None:
        self.valid_token = valid_token
        self.expire_first_call = expire_first_call
        self.expired_once = False
        self.files: dict[str, dict[str, object]] = {}
        self.next_id = 1
        self.calls: list[tuple[str, str]] = []

    def transport(
        self,
        method: str,
        url: str,
        headers: dict[str, str],
        body: bytes | None,
        timeout: float,
    ) -> tuple[int, bytes]:
        self.calls.append((method, url))
        if url == gd_mod.OAUTH_TOKEN_URL:
            self.valid_token = "tok_refreshed"
            return (200, json.dumps({"access_token": self.valid_token, "expires_in": 3600}).encode("utf-8"))

        auth = headers.get("Authorization", "")
        if self.expire_first_call and not self.expired_once:
            self.expired_once = True
            return (401, b'{"error":"expired"}')
        if auth != f"Bearer {self.valid_token}":
            return (401, b'{"error":"unauthorized"}')

        parsed = urllib.parse.urlparse(url)
        qs = urllib.parse.parse_qs(parsed.query)

        # GET file content
        if method == "GET" and parsed.path.startswith("/drive/v3/files/") and qs.get("alt") == ["media"]:
            fid = parsed.path.rsplit("/", 1)[-1]
            if fid not in self.files:
                return (404, b"not found")
            return (200, bytes(self.files[fid]["content"]))  # type: ignore[arg-type]

        # GET list/search
        if method == "GET" and parsed.path == "/drive/v3/files":
            q = (qs.get("q") or [""])[0]
            matches = []
            for fid, meta in self.files.items():
                name = str(meta["name"])
                if f"name = '{name}'" not in q:
                    continue
                if gd_mod.FOLDER_MIME in q and meta["mimeType"] != gd_mod.FOLDER_MIME:
                    continue
                parents = meta.get("parents") or []
                if "'root' in parents" in q and "root" not in parents:
                    continue
                if "in parents" in q and "'root' in parents" not in q and not any(f"'{p}' in parents" in q for p in parents):
                    continue
                matches.append({"id": fid, "name": name})
            return (200, json.dumps({"files": matches}).encode("utf-8"))

        # POST create folder
        if method == "POST" and parsed.path == "/drive/v3/files":
            meta = json.loads((body or b"{}").decode("utf-8"))
            fid = f"fid_{self.next_id}"
            self.next_id += 1
            self.files[fid] = {
                "name": meta["name"],
                "mimeType": meta.get("mimeType", "text/plain"),
                "parents": meta.get("parents", []),
                "content": b"",
            }
            return (200, json.dumps({"id": fid}).encode("utf-8"))

        # POST multipart upload
        if method == "POST" and parsed.path == "/upload/drive/v3/files":
            ctype = headers.get("Content-Type", "")
            boundary = ctype.split("boundary=", 1)[1].encode("ascii")
            parts = (body or b"").split(b"--" + boundary)
            meta_raw = parts[1].split(b"\r\n\r\n", 1)[1]
            if meta_raw.endswith(b"\r\n"):
                meta_raw = meta_raw[:-2]
            file_raw = parts[2].split(b"\r\n\r\n", 1)[1]
            if file_raw.endswith(b"\r\n"):
                file_raw = file_raw[:-2]
            meta = json.loads(meta_raw.decode("utf-8"))
            fid = f"fid_{self.next_id}"
            self.next_id += 1
            self.files[fid] = {
                "name": meta["name"],
                "mimeType": "text/plain",
                "parents": meta.get("parents", []),
                "content": file_raw,
            }
            return (200, json.dumps({"id": fid}).encode("utf-8"))

        # PATCH media upload
        if method == "PATCH" and parsed.path.startswith("/upload/drive/v3/files/"):
            fid = parsed.path.rsplit("/", 1)[-1]
            if fid not in self.files:
                return (404, b"not found")
            self.files[fid]["content"] = body or b""
            return (200, json.dumps({"id": fid}).encode("utf-8"))

        return (400, b"unsupported")


class GoogleDriveStorageTests(unittest.TestCase):
    def test_end_to_end_hitl_mcp_over_gdrive_storage(self) -> None:
        backend = FakeDriveBackend()
        store = gd_mod.GoogleDriveStorage(
            access_token="tok_initial",
            http_transport=backend.transport,
        )
        self.assertIsInstance(store, inbox_mod.ProfileStorage)
        self.assertEqual(store.profile_location, "gdrive://nihongo/profile.md")

        srv = mcp_mod.NihongoMcpServer(storage=store)
        p = srv._tool_propose_profile_entry({
            "scene": "common",
            "kind": "forbidden",
            "value": "いただけますと幸いです",
            "reason": "硬すぎるため",
        })
        self.assertTrue(p["created"])
        self.assertIsNone(store.read_profile_text())

        entry_id = p["entry"]["id"]
        appr = srv._tool_review_inbox_entry({
            "action": "approve",
            "ids": [entry_id],
            "confirmed_by_user": True,
        })
        self.assertEqual(appr["approved_count"], 1)

        prof = srv._tool_get_profile({})
        self.assertTrue(prof["exists"])
        self.assertIn("いただけますと幸いです", prof["forbidden"])

    def test_oauth_refresh_on_401_and_no_token_leak(self) -> None:
        import time as _time

        backend = FakeDriveBackend(expire_first_call=True)
        store = gd_mod.GoogleDriveStorage(
            client_id="cid_secret",
            client_secret="csec_secret_do_not_leak",
            refresh_token="rtok_secret_do_not_leak",
            http_transport=backend.transport,
        )
        # Simulate a cached token that was revoked/expired server-side -> 401 triggers 1 auto-refresh
        store._cached_token = "tok_stale"
        store._cached_token_expiry = _time.monotonic() + 600
        store.write_profile_text("# 私の書き方\n")
        self.assertEqual(store.read_profile_text(), "# 私の書き方\n")
        refresh_calls = [u for m, u in backend.calls if u == gd_mod.OAUTH_TOKEN_URL]
        self.assertEqual(len(refresh_calls), 1)

        # 失敗時にもトークン文字列が例外へ漏れないこと
        def failing_transport(m, u, h, b, t):
            return (403, b"forbidden")

        bad_store = gd_mod.GoogleDriveStorage(
            access_token="SUPER_SECRET_BEARER_TOKEN_12345",
            http_transport=failing_transport,
        )
        with self.assertRaises(gd_mod.GoogleDriveStorageError) as ctx:
            bad_store.read_profile_text()
        self.assertNotIn("SUPER_SECRET_BEARER_TOKEN_12345", str(ctx.exception))

    def test_gdrive_owner_root_scope_and_stale_404_recovery(self) -> None:
        backend = FakeDriveBackend()
        # Attacker's shared folder named 'nihongo' NOT in root must be ignored
        backend.files["attacker_fid"] = {
            "name": "nihongo",
            "mimeType": gd_mod.FOLDER_MIME,
            "parents": ["shared_external_parent"],
            "content": b"",
        }
        store = gd_mod.GoogleDriveStorage(access_token="tok_initial", http_transport=backend.transport)
        store.write_profile_text("# v1\n")
        self.assertNotEqual(store._folder_id_cache, "attacker_fid")
        # Confirm query strictly enforced 'root' in parents and 'me' in owners
        search_urls = [u for m, u in backend.calls if m == "GET" and "/drive/v3/files?" in u]
        self.assertTrue(any("root" in urllib.parse.unquote(u) and "me" in urllib.parse.unquote(u) for u in search_urls))

        # Simulate stale file deleted remotely -> PATCH 404 recovers cleanly by recreating
        old_fid = store._file_id_cache["profile.md"]
        del backend.files[old_fid]
        store.write_profile_text("# v2\n")
        self.assertEqual(store.read_profile_text(), "# v2\n")


class InChatMcpWorkflowTests(unittest.TestCase):
    def test_in_chat_profile_summary_inbox_approval_and_forbidden_removal(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            srv = mcp_mod.NihongoMcpServer(home=d)

            # 1. Empty profile returns friendly Japanese summary
            empty_prof = srv._tool_get_profile({})
            self.assertIn("まだ作成されていません", empty_prof["display_markdown"])

            # 2. Propose two entries -> list_inbox includes readable display_markdown
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

            # 3. Approve both in chat (confirmed_by_user=True)
            appr = srv._tool_review_inbox_entry({
                "action": "approve",
                "ids": [p1["entry"]["id"], p2["entry"]["id"]],
                "confirmed_by_user": True,
            })
            self.assertEqual(appr["approved_count"], 2)

            # 4. get_profile returns structured 4-scene dict and display_markdown
            prof = srv._tool_get_profile({})
            self.assertIn("今のあなたの日本語ルール", prof["display_markdown"])
            self.assertIn("「いただけますと幸いです」", prof["display_markdown"])
            self.assertIn("いただけますと幸いです", prof["structured"]["common"]["forbidden"])

            # 5. remove_profile_forbidden requires confirmed_by_user=True (HITL guard)
            dry = srv._tool_remove_profile_forbidden({
                "scene": "common",
                "value": "いただけますと幸いです",
            })
            self.assertTrue(dry["dry_run"])
            self.assertTrue(dry["requires_user_confirmation"])
            self.assertIn("いただけますと幸いです", srv._tool_get_profile({})["forbidden"])

            # 6. Confirmed removal surgically removes 1 expression and keeps the other
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
