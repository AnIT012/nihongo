#!/usr/bin/env python3
"""nihongo のローカル承認 UI サーバー（標準ライブラリのみ・外部通信ゼロ）。

使い方:
    nihongo-check ui
    nihongo-check ui --port 8765 --no-browser

セキュリティ原則:
- 127.0.0.1 のみにバインドし、外部ネットワークからは接続不可とする。
- Host / Origin ヘッダ検証とプロセス毎のランダム CSRF トークンで DNS リバインディングと CSRF を防ぐ。
- CSP により外部リソース読み込みと外部送信を禁止する。
- profile.md への手動保存・受信箱追加はすべて inbox.py の PII ガードとアトミック書き込みを経由する。
"""
from __future__ import annotations

import hmac
import http.server
import json
import os
import secrets
import sys
import threading
import time
import urllib.parse
import webbrowser
from typing import Any

if __package__:
    from . import cli as cli_mod
    from . import inbox as inbox_mod
    from . import revert_broken, trim_commas, ui_template
else:
    _SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    if _SCRIPT_DIR not in sys.path:
        sys.path.insert(0, _SCRIPT_DIR)
    import cli as cli_mod  # noqa: E402
    import inbox as inbox_mod  # noqa: E402
    import revert_broken  # noqa: E402
    import trim_commas  # noqa: E402
    import ui_template  # noqa: E402

MAX_BODY_BYTES = 256 * 1024

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


def _load_web_md_fallback() -> str | None:
    """リポジトリ内の nihongo/WEB.md があれば読み込む。"""
    cand = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "WEB.md"))
    if os.path.isfile(cand):
        try:
            with open(cand, encoding="utf-8-sig") as f:
                return f.read().strip()
        except OSError:
            return None
    return None


def _render_ui_html(csrf_token: str) -> str:
    return ui_template.render_ui_html(csrf_token)


class NihongoUiServer(http.server.ThreadingHTTPServer):
    """ローカル承認 UI 用の軽量 HTTP サーバー（127.0.0.1 専用）。"""

    allow_reuse_address = os.name != "nt"

    def __init__(
        self,
        *,
        host: str = "127.0.0.1",
        port: int = 8765,
        home: str | None = None,
        profile_path: str | None = None,
        inbox_path: str | None = None,
        project_dir: str | None = None,
        storage: inbox_mod.ProfileStorage | None = None,
    ) -> None:
        if host not in ("127.0.0.1", "localhost"):
            raise ValueError("セキュリティ保護のため、ローカル承認 UI は 127.0.0.1 のみで起動します。")
        self.storage: inbox_mod.ProfileStorage = (
            storage
            if storage is not None
            else inbox_mod.LocalFileStorage(
                home=home,
                profile_path=profile_path,
                inbox_path=inbox_path,
            )
        )
        self.project_dir = project_dir
        self.state_lock = threading.RLock()
        self.csrf_token = secrets.token_urlsafe(32)
        self.html_bytes = _render_ui_html(self.csrf_token).encode("utf-8")
        super().__init__(("127.0.0.1", int(port)), _UiRequestHandler)


class _UiRequestHandler(http.server.BaseHTTPRequestHandler):
    server: NihongoUiServer

    def log_message(self, format: str, *args: Any) -> None:
        # 標準エラー出力を汚さない
        return

    def _allowed_hosts(self) -> set[str]:
        port = self.server.server_address[1]
        allowed = {f"127.0.0.1:{port}", f"localhost:{port}"}
        if port == 80:
            allowed.update({"127.0.0.1", "localhost"})
        return allowed

    def _check_host(self) -> bool:
        host = (self.headers.get("Host") or "").strip().lower()
        return host in self._allowed_hosts()

    def _check_origin_and_csrf(self) -> str | None:
        origin = (self.headers.get("Origin") or "").strip().lower()
        if origin:
            parsed = urllib.parse.urlparse(origin)
            if parsed.scheme != "http" or parsed.netloc not in self._allowed_hosts():
                return "不正な Origin からのリクエストを拒否しました。"
        token = (self.headers.get("X-Nihongo-CSRF") or "").strip()
        if not token or not hmac.compare_digest(token, self.server.csrf_token):
            return "CSRF トークンが一致しません。ページを再読み込みしてください。"
        return None

    def _send_headers(self, status: int, content_type: str, length: int, *, close: bool = False) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(length))
        if close:
            self.send_header("Connection", "close")
            self.close_connection = True
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self' 'unsafe-inline'; connect-src 'self'; img-src 'self' data:; frame-ancestors 'none'",
        )
        self.end_headers()

    def _send_json(self, status: int, payload: dict[str, Any], *, close: bool = False) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self._send_headers(status, "application/json; charset=utf-8", len(body), close=close)
        self.wfile.write(body)

    def _read_json_body(self) -> tuple[dict[str, Any] | None, int | None, str | None]:
        raw_len = self.headers.get("Content-Length")
        if raw_len is None:
            return ({}, None, None)
        try:
            length = int(raw_len)
        except ValueError:
            return (None, 400, "Content-Length が不正です。")
        if length < 0 or length > MAX_BODY_BYTES:
            return (None, 413, "リクエストサイズが大きすぎます。")
        raw = self.rfile.read(length) if length > 0 else b"{}"
        try:
            data = json.loads(raw.decode("utf-8"))
        except Exception:
            return (None, 400, "JSON の形式が正しくありません。")
        if not isinstance(data, dict):
            return (None, 400, "JSON オブジェクトを送信してください。")
        return (data, None, None)

    def _enrich_items(self, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for item in items:
            sc = str(item.get("scene", "common"))
            kd = str(item.get("kind", "rule"))
            c = dict(item)
            c["scene_label"] = _SCENE_LABELS.get(sc, sc)
            c["kind_label"] = _KIND_LABELS.get(kd, kd)
            out.append(c)
        return out

    def do_GET(self) -> None:
        if not self._check_host():
            self._send_json(403, {"error": "不正な Host ヘッダのため拒否しました。"})
            return

        path = urllib.parse.urlparse(self.path).path
        if path == "/favicon.ico":
            self._send_headers(204, "image/x-icon", 0)
            return
        if path in ("/", "/index.html"):
            body = self.server.html_bytes
            self._send_headers(200, "text/html; charset=utf-8", len(body))
            self.wfile.write(body)
            return

        if path == "/api/state":
            try:
                with self.server.state_lock:
                    prof = inbox_mod.read_profile(
                        storage=self.server.storage,
                        project_dir=self.server.project_dir,
                        include_project=True,
                    )
                    all_items = inbox_mod.list_inbox(status="all", storage=self.server.storage)
                pending = [x for x in all_items if x.get("status") == "pending"]
                history = [x for x in all_items if x.get("status") != "pending"][-20:][::-1]
                self._send_json(
                    200,
                    {
                        "version": cli_mod.__version__,
                        "profile": prof,
                        "default_template": inbox_mod.DEFAULT_PROFILE_TEMPLATE,
                        "pending_inbox": self._enrich_items(pending),
                        "history_inbox": self._enrich_items(history),
                        "sync_folders": inbox_mod.detect_sync_folders(),
                    },
                )
            except Exception as exc:
                self._send_json(500, {"error": f"状態の読み込みに失敗しました: {exc}"})
            return

        self._send_json(404, {"error": "Not Found"})

    def do_POST(self) -> None:
        if not self._check_host():
            self._send_json(403, {"error": "不正な Host ヘッダのため拒否しました。"})
            return
        csrf_err = self._check_origin_and_csrf()
        if csrf_err:
            self._send_json(403, {"error": csrf_err})
            return

        data, err_status, err_msg = self._read_json_body()
        if err_status is not None or data is None:
            self._send_json(err_status or 400, {"error": err_msg or "Bad Request"}, close=(err_status == 413))
            return

        path = urllib.parse.urlparse(self.path).path
        try:
            if path == "/api/inbox/propose":
                with self.server.state_lock:
                    res = inbox_mod.propose_entry(
                        scene=str(data.get("scene") or "common"),
                        kind=str(data.get("kind") or "rule"),
                        value=str(data.get("value") or ""),
                        reason=str(data.get("reason") or ""),
                        source="local-ui",
                        storage=self.server.storage,
                    )
                self._send_json(200, res)
                return

            if path == "/api/inbox/approve":
                raw_ids = data.get("ids")
                if raw_ids is not None and not isinstance(raw_ids, list):
                    raise ValueError("ids は文字列の配列で指定してください。")
                ids = [str(x) for x in (raw_ids or [])]
                approve_all = data.get("approve_all") is True
                force = data.get("force") is True
                with self.server.state_lock:
                    res = inbox_mod.approve_entries(
                        ids,
                        approve_all=approve_all,
                        force=force,
                        storage=self.server.storage,
                    )
                self._send_json(200, res)
                return

            if path == "/api/inbox/reject":
                raw_ids = data.get("ids")
                if raw_ids is not None and not isinstance(raw_ids, list):
                    raise ValueError("ids は文字列の配列で指定してください。")
                ids = [str(x) for x in (raw_ids or [])]
                reject_all = data.get("reject_all") is True
                reason = str(data.get("reason") or "")
                with self.server.state_lock:
                    res = inbox_mod.reject_entries(
                        ids,
                        reject_all=reject_all,
                        reason=reason,
                        storage=self.server.storage,
                    )
                self._send_json(200, res)
                return

            if path == "/api/profile/save":
                if "content" not in data or not isinstance(data["content"], str):
                    raise ValueError("content は文字列で指定してください。")
                with self.server.state_lock:
                    res = inbox_mod.save_profile_direct(data["content"], storage=self.server.storage)
                self._send_json(200, res)
                return

            if path == "/api/check":
                t0 = time.perf_counter()
                orig = str(data.get("orig") or "")
                draft = str(data.get("draft") or "")
                request = str(data.get("request") or "")
                scene = data.get("scene")
                if scene not in ("casual", "work", "formal"):
                    scene = None

                prof = inbox_mod.read_profile(
                    storage=self.server.storage,
                    project_dir=self.server.project_dir,
                    include_project=True,
                )
                forbidden = cli_mod.parse_profile_text(prof["raw"], scene=scene) if prof["exists"] else []
                findings = revert_broken.remaining(orig, draft, request)
                if forbidden or scene:
                    findings = findings + cli_mod.check_profile_drift(orig, draft, forbidden, scene=scene)
                formatted = [cli_mod._format_finding(x) for x in findings]
                elapsed_ms = max(1, int(round((time.perf_counter() - t0) * 1000)))
                self._send_json(
                    200,
                    {
                        "clean": len(formatted) == 0,
                        "count": len(formatted),
                        "findings": formatted,
                        "elapsed_ms": elapsed_ms,
                        "layers": prof["layers"],
                    },
                )
                return

            if path == "/api/setup/export":
                scene = str(data.get("scene") or "work")
                sync_pref = str(data.get("sync_preference") or "local")
                prof = inbox_mod.read_profile(
                    storage=self.server.storage,
                    project_dir=self.server.project_dir,
                    include_project=True,
                )
                forbidden = cli_mod.parse_profile_text(prof["raw"]) if prof["exists"] else []
                md = inbox_mod.build_setup_markdown(
                    forbidden=forbidden,
                    scene=scene,
                    sync_preference=sync_pref,
                    web_fallback_text=_load_web_md_fallback(),
                )
                self._send_json(200, {"markdown": md, "forbidden_count": len(forbidden)})
                return

            self._send_json(404, {"error": "Not Found"})
        except ValueError as exc:
            self._send_json(400, {"error": str(exc)})
        except Exception as exc:
            self._send_json(500, {"error": f"処理中にエラーが発生しました: {exc}"})


def run_ui_server(
    *,
    port: int = 8765,
    home: str | None = None,
    profile_path: str | None = None,
    inbox_path: str | None = None,
    project_dir: str | None = None,
    open_browser: bool = True,
) -> int:
    server = NihongoUiServer(
        port=port,
        home=home,
        profile_path=profile_path,
        inbox_path=inbox_path,
        project_dir=project_dir,
    )
    actual_port = server.server_address[1]
    url = f"http://127.0.0.1:{actual_port}/"
    print(f"nihongo ローカル承認 UI を起動しました: {url}", flush=True)
    print("終了するには Ctrl+C を押してください（この画面は 127.0.0.1 のみで動作します）。", flush=True)
    if open_browser:
        try:
            webbrowser.open(url)
        except Exception:
            pass
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nローカル承認 UI を停止しました。")
    finally:
        server.server_close()
    return 0
