"""v3.1 拡張機能（2層プロファイル・同期フォルダ検出・GoogleDriveStorage・ローカル承認 UI）のテスト。"""
from __future__ import annotations

import http.client
import json
import os
import sys
import tempfile
import threading
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
import ui_server as ui_mod  # noqa: E402


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


class LocalUiServerTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.home = os.path.join(self._tmp.name, "nihongo_home")
        self.server = ui_mod.NihongoUiServer(port=0, home=self.home)
        self.port = self.server.server_address[1]
        self.csrf = self.server.csrf_token
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=3)
        self._tmp.cleanup()

    def _request(
        self,
        method: str,
        path: str,
        *,
        body: dict | None = None,
        headers: dict[str, str] | None = None,
    ) -> tuple[int, dict[str, str], bytes]:
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        req_headers = {"Host": f"127.0.0.1:{self.port}"}
        payload: bytes | None = None
        if body is not None:
            payload = json.dumps(body, ensure_ascii=False).encode("utf-8")
            req_headers["Content-Type"] = "application/json"
        if headers:
            req_headers.update(headers)
        conn.request(method, path, body=payload, headers=req_headers)
        resp = conn.getresponse()
        raw = resp.read()
        resp_headers = {k.lower(): v for k, v in resp.getheaders()}
        conn.close()
        return (resp.status, resp_headers, raw)

    def test_refuses_non_loopback_bind(self) -> None:
        with self.assertRaises(ValueError):
            ui_mod.NihongoUiServer(host="0.0.0.0", port=0, home=self.home)

    def test_security_headers_dns_rebinding_and_csrf_guards(self) -> None:
        status, headers, raw = self._request("GET", "/")
        self.assertEqual(status, 200)
        self.assertIn("default-src 'self'", headers.get("content-security-policy", ""))
        self.assertEqual(headers.get("x-frame-options"), "DENY")
        self.assertEqual(headers.get("x-content-type-options"), "nosniff")
        self.assertIn("nihongo", raw.decode("utf-8"))

        # DNS rebinding Host block
        bad_host_status, _, _ = self._request("GET", "/api/state", headers={"Host": "evil.example.com"})
        self.assertEqual(bad_host_status, 403)

        # Missing CSRF token blocked
        no_csrf_status, _, _ = self._request("POST", "/api/inbox/propose", body={"scene": "common", "kind": "forbidden", "value": "test"})
        self.assertEqual(no_csrf_status, 403)

        # Evil Origin blocked even with valid CSRF
        bad_origin_status, _, _ = self._request(
            "POST",
            "/api/inbox/propose",
            body={"scene": "common", "kind": "forbidden", "value": "test"},
            headers={"X-Nihongo-CSRF": self.csrf, "Origin": "http://evil.example.com"},
        )
        self.assertEqual(bad_origin_status, 403)

        # Direct profile save blocks PII and rejects missing content (no accidental wipe)
        pii_status, _, _ = self._request(
            "POST",
            "/api/profile/save",
            body={"content": "# 私の書き方\n連絡先: user@example.com\n"},
            headers={"X-Nihongo-CSRF": self.csrf},
        )
        self.assertEqual(pii_status, 400)

        missing_content_status, _, _ = self._request(
            "POST",
            "/api/profile/save",
            body={},
            headers={"X-Nihongo-CSRF": self.csrf},
        )
        self.assertEqual(missing_content_status, 400)

        # Non-list ids rejected cleanly with 400
        bad_ids_status, _, _ = self._request(
            "POST",
            "/api/inbox/approve",
            body={"ids": "not_a_list"},
            headers={"X-Nihongo-CSRF": self.csrf},
        )
        self.assertEqual(bad_ids_status, 400)

        # Port-less Origin rejected on non-80 port
        portless_origin_status, _, _ = self._request(
            "POST",
            "/api/inbox/propose",
            body={"scene": "common", "kind": "forbidden", "value": "test"},
            headers={"X-Nihongo-CSRF": self.csrf, "Origin": "http://localhost"},
        )
        self.assertEqual(portless_origin_status, 403)

        # Oversized body blocked with 413 before reading payload
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        conn.putrequest("POST", "/api/profile/save")
        conn.putheader("Host", f"127.0.0.1:{self.port}")
        conn.putheader("Content-Type", "application/json")
        conn.putheader("X-Nihongo-CSRF", self.csrf)
        conn.putheader("Content-Length", str(ui_mod.MAX_BODY_BYTES + 10))
        conn.endheaders()
        resp = conn.getresponse()
        resp.read()
        conn.close()
        self.assertEqual(resp.status, 413)

        # [formal] guard warning requires force=True even via UI API
        st, _, raw = self._request(
            "POST",
            "/api/inbox/propose",
            body={"scene": "formal", "kind": "tone", "value": "語尾に「っす」を使う"},
            headers={"X-Nihongo-CSRF": self.csrf},
        )
        self.assertEqual(st, 200)
        warn_id = json.loads(raw)["entry"]["id"]
        st, _, raw = self._request(
            "POST",
            "/api/inbox/approve",
            body={"ids": [warn_id], "force": False},
            headers={"X-Nihongo-CSRF": self.csrf},
        )
        self.assertEqual(st, 200)
        self.assertEqual(json.loads(raw)["approved_count"], 0)
        self.assertEqual(len(json.loads(raw)["blocked_by_guard"]), 1)

    def test_full_ui_api_workflow(self) -> None:
        h = {"X-Nihongo-CSRF": self.csrf}
        # 1. Propose
        st, _, raw = self._request(
            "POST",
            "/api/inbox/propose",
            body={"scene": "common", "kind": "forbidden", "value": "いただけますと幸いです", "reason": "硬すぎる"},
            headers=h,
        )
        self.assertEqual(st, 200)
        entry_id = json.loads(raw)["entry"]["id"]

        # 2. Check state
        st, _, raw = self._request("GET", "/api/state")
        self.assertEqual(st, 200)
        state = json.loads(raw)
        self.assertEqual(len(state["pending_inbox"]), 1)
        self.assertEqual(state["pending_inbox"][0]["kind_label"], "NG表現")

        # 3. Approve
        st, _, raw = self._request("POST", "/api/inbox/approve", body={"ids": [entry_id]}, headers=h)
        self.assertEqual(st, 200)
        self.assertEqual(json.loads(raw)["approved_count"], 1)

        # 4. Run 0-token check via API
        st, _, raw = self._request(
            "POST",
            "/api/check",
            body={
                "orig": "資料は明日15時までに必ず送ってください。",
                "draft": "資料は明日15時頃までにご送付いただけますと幸いです。",
                "scene": "formal",
            },
            headers=h,
        )
        self.assertEqual(st, 200)
        chk = json.loads(raw)
        self.assertFalse(chk["clean"])
        joined = "\n".join(chk["findings"])
        self.assertIn("いただけますと幸いです", joined)
        self.assertIn("必ず", joined)

        # 5. Export 1-file setup markdown
        st, _, raw = self._request("POST", "/api/setup/export", body={"scene": "formal", "sync_preference": "gdrive"}, headers=h)
        self.assertEqual(st, 200)
        exp = json.loads(raw)
        self.assertIn("いただけますと幸いです", exp["markdown"])
        self.assertIn("確認カード 1", exp["markdown"])


if __name__ == "__main__":
    unittest.main()
