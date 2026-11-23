#!/usr/bin/env python3
"""ユーザー自身の Google Drive を保存先にする ProfileStorage 実装（標準ライブラリのみ）。

設計原則:
- 運営者サーバーや共有データベースは一切持たず、ユーザー本人の Google Drive と直接通信する。
- `inbox.ProfileStorage` の 4 メソッド契約（read/write profile & inbox）をそのまま満たす。
- 既定はマイドライブ直下（'root' in parents and 'me' in owners）の `nihongo` フォルダ。
  他者から共有された同名フォルダ（Shared with me）は検索対象から厳密に除外する。
- `app_data_only=True` を指定すると Google Drive の非表示領域 `appDataFolder` に保存する。
- 外部パッケージ依存ゼロ（Python 3.10+ の `urllib.request` のみ）。
"""
from __future__ import annotations

import http.client
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from typing import Any, Callable

DRIVE_FILES_API = "https://www.googleapis.com/drive/v3/files"
DRIVE_UPLOAD_API = "https://www.googleapis.com/upload/drive/v3/files"
OAUTH_TOKEN_URL = "https://oauth2.googleapis.com/token"
FOLDER_MIME = "application/vnd.google-apps.folder"
DEFAULT_TIMEOUT = 15.0

HttpTransport = Callable[[str, str, dict[str, str], bytes | None, float], tuple[int, bytes]]


class GoogleDriveStorageError(RuntimeError):
    """Google Drive 読み書き時の例外（認証トークンはメッセージへ絶対に出力しない）。"""


def _default_http_transport(
    method: str,
    url: str,
    headers: dict[str, str],
    body: bytes | None,
    timeout: float,
) -> tuple[int, bytes]:
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return (int(resp.status), resp.read())
    except urllib.error.HTTPError as exc:
        payload = b""
        try:
            payload = exc.read()
        except Exception:
            pass
        return (int(exc.code), payload)
    except urllib.error.URLError as exc:
        raise GoogleDriveStorageError(f"Google Drive への接続に失敗しました: {exc.reason}") from exc
    except (TimeoutError, http.client.HTTPException, OSError) as exc:
        raise GoogleDriveStorageError(f"Google Drive 通信中にエラーが発生しました: {type(exc).__name__}") from exc


def _escape_drive_query(value: str) -> str:
    return value.replace("\\", "\\\\").replace("'", "\\'")


def _parse_json_object(body: bytes, context: str) -> dict[str, Any]:
    try:
        data = json.loads(body.decode("utf-8"))
    except Exception as exc:
        raise GoogleDriveStorageError(f"Google Drive 応答の JSON 解析に失敗しました（{context}）。") from exc
    if not isinstance(data, dict):
        raise GoogleDriveStorageError(f"Google Drive 応答形式が不正です（{context}）。")
    return data


class GoogleDriveStorage:
    """Google Drive REST API v3 を使った ProfileStorage 実装。"""

    def __init__(
        self,
        *,
        access_token: str | None = None,
        token_provider: Callable[[], str] | None = None,
        client_id: str | None = None,
        client_secret: str | None = None,
        refresh_token: str | None = None,
        folder_name: str = "nihongo",
        profile_filename: str = "profile.md",
        inbox_filename: str = "inbox.jsonl",
        app_data_only: bool = False,
        timeout: float = DEFAULT_TIMEOUT,
        http_transport: HttpTransport | None = None,
    ) -> None:
        self._explicit_access_token = (access_token or "").strip() or None
        self._env_access_token = os.environ.get("NIHONGO_GDRIVE_ACCESS_TOKEN", "").strip() or None
        self._token_provider = token_provider
        self._client_id = (client_id or os.environ.get("NIHONGO_GDRIVE_CLIENT_ID", "")).strip() or None
        self._client_secret = (client_secret or os.environ.get("NIHONGO_GDRIVE_CLIENT_SECRET", "")).strip() or None
        self._refresh_token = (refresh_token or os.environ.get("NIHONGO_GDRIVE_REFRESH_TOKEN", "")).strip() or None

        self._cached_token: str | None = None
        self._cached_token_expiry: float = 0.0

        self.folder_name = folder_name.strip() or "nihongo"
        self.profile_filename = profile_filename.strip() or "profile.md"
        self.inbox_filename = inbox_filename.strip() or "inbox.jsonl"
        self.app_data_only = app_data_only
        self.timeout = float(timeout)
        self._transport: HttpTransport = http_transport or _default_http_transport

        self._folder_id_cache: str | None = None
        self._file_id_cache: dict[str, str] = {}

    @property
    def profile_location(self) -> str:
        prefix = "gdrive://appDataFolder" if self.app_data_only else f"gdrive://{self.folder_name}"
        return f"{prefix}/{self.profile_filename}"

    @property
    def inbox_location(self) -> str:
        prefix = "gdrive://appDataFolder" if self.app_data_only else f"gdrive://{self.folder_name}"
        return f"{prefix}/{self.inbox_filename}"

    def _has_refresh_creds(self) -> bool:
        return bool(self._refresh_token and self._client_id and self._client_secret)

    def _get_access_token(self) -> tuple[str, bool]:
        """(token, freshly_refreshed) を返す。"""
        if self._token_provider is not None:
            tok = (self._token_provider() or "").strip()
            if not tok:
                raise GoogleDriveStorageError("Google Drive アクセストークンを取得できませんでした。")
            return (tok, False)

        if self._explicit_access_token:
            return (self._explicit_access_token, False)

        if self._cached_token and time.monotonic() < self._cached_token_expiry - 30:
            return (self._cached_token, False)

        if self._has_refresh_creds():
            return (self._refresh_oauth_token(), True)

        if self._env_access_token:
            return (self._env_access_token, False)

        raise GoogleDriveStorageError(
            "Google Drive の認証情報が設定されていません。"
            "NIHONGO_GDRIVE_ACCESS_TOKEN または OAuth リフレッシュトークンを設定してください。"
        )

    def _refresh_oauth_token(self) -> str:
        form = urllib.parse.urlencode({
            "client_id": self._client_id or "",
            "client_secret": self._client_secret or "",
            "refresh_token": self._refresh_token or "",
            "grant_type": "refresh_token",
        }).encode("utf-8")
        status, body = self._transport(
            "POST",
            OAUTH_TOKEN_URL,
            {"Content-Type": "application/x-www-form-urlencoded"},
            form,
            self.timeout,
        )
        if status != 200:
            raise GoogleDriveStorageError(
                f"Google OAuth トークンの更新に失敗しました（HTTP {status}）。再認証を確認してください。"
            )
        data = _parse_json_object(body, "oauth_refresh")
        token = str(data.get("access_token") or "").strip()
        if not token:
            raise GoogleDriveStorageError("Google OAuth 応答に access_token が含まれていません。")
        try:
            expires_in = float(data.get("expires_in") or 3600)
        except (TypeError, ValueError):
            expires_in = 3600.0
        self._cached_token = token
        self._cached_token_expiry = time.monotonic() + max(60.0, expires_in)
        return token

    def _api_request(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        body: bytes | None = None,
    ) -> tuple[int, bytes]:
        token, freshly_refreshed = self._get_access_token()
        req_headers = {"Authorization": f"Bearer {token}"}
        if headers:
            req_headers.update(headers)
        status, resp_body = self._transport(method, url, req_headers, body, self.timeout)
        if (
            status == 401
            and not freshly_refreshed
            and self._token_provider is None
            and not self._explicit_access_token
            and self._has_refresh_creds()
        ):
            # キャッシュ済みトークンの期限切れ時のみ 1 回だけ自動リフレッシュして再試行
            self._cached_token = None
            token = self._refresh_oauth_token()
            req_headers["Authorization"] = f"Bearer {token}"
            status, resp_body = self._transport(method, url, req_headers, body, self.timeout)
        return (status, resp_body)

    def _spaces(self) -> str:
        return "appDataFolder" if self.app_data_only else "drive"

    def _ensure_parent_id(self) -> str:
        if self.app_data_only:
            return "appDataFolder"
        if self._folder_id_cache:
            return self._folder_id_cache

        # マイドライブ直下かつ自分が所有者のフォルダのみに限定（共有フォルダ乗っ取り防止）
        q = (
            f"name = '{_escape_drive_query(self.folder_name)}' "
            f"and mimeType = '{FOLDER_MIME}' "
            "and 'root' in parents and 'me' in owners and trashed = false"
        )
        qs = urllib.parse.urlencode({
            "q": q,
            "spaces": "drive",
            "orderBy": "createdTime asc",
            "fields": "files(id,name)",
            "pageSize": "5",
        })
        status, body = self._api_request("GET", f"{DRIVE_FILES_API}?{qs}")
        if status != 200:
            raise GoogleDriveStorageError(f"Google Drive フォルダ検索に失敗しました（HTTP {status}）。")
        files = _parse_json_object(body, "folder_search").get("files") or []
        if files:
            self._folder_id_cache = str(files[0]["id"])
            return self._folder_id_cache

        # マイドライブ直下に新規作成
        meta = json.dumps({
            "name": self.folder_name,
            "mimeType": FOLDER_MIME,
            "parents": ["root"],
        }).encode("utf-8")
        c_status, c_body = self._api_request(
            "POST",
            f"{DRIVE_FILES_API}?fields=id",
            headers={"Content-Type": "application/json; charset=UTF-8"},
            body=meta,
        )
        if c_status not in (200, 201):
            raise GoogleDriveStorageError(f"Google Drive フォルダ作成に失敗しました（HTTP {c_status}）。")
        created_id = str(_parse_json_object(c_body, "folder_create").get("id") or "")
        if not created_id:
            raise GoogleDriveStorageError("Google Drive フォルダ ID を取得できませんでした。")
        self._folder_id_cache = created_id
        return created_id

    def _find_file_id(self, filename: str, *, bypass_cache: bool = False) -> str | None:
        if not bypass_cache and filename in self._file_id_cache:
            return self._file_id_cache[filename]

        parent_id = self._ensure_parent_id()
        owner_clause = "" if self.app_data_only else " and 'me' in owners"
        q = (
            f"name = '{_escape_drive_query(filename)}' "
            f"and '{_escape_drive_query(parent_id)}' in parents"
            f"{owner_clause} and trashed = false"
        )
        qs = urllib.parse.urlencode({
            "q": q,
            "spaces": self._spaces(),
            "orderBy": "createdTime asc",
            "fields": "files(id,name)",
            "pageSize": "5",
        })
        status, body = self._api_request("GET", f"{DRIVE_FILES_API}?{qs}")
        if status == 404 and not self.app_data_only and self._folder_id_cache:
            self._folder_id_cache = None
            parent_id = self._ensure_parent_id()
            q = (
                f"name = '{_escape_drive_query(filename)}' "
                f"and '{_escape_drive_query(parent_id)}' in parents"
                f"{owner_clause} and trashed = false"
            )
            qs = urllib.parse.urlencode({
                "q": q,
                "spaces": self._spaces(),
                "orderBy": "createdTime asc",
                "fields": "files(id,name)",
                "pageSize": "5",
            })
            status, body = self._api_request("GET", f"{DRIVE_FILES_API}?{qs}")
        if status != 200:
            raise GoogleDriveStorageError(f"Google Drive ファイル検索に失敗しました（HTTP {status}）。")
        files = _parse_json_object(body, "file_search").get("files") or []
        if not files:
            self._file_id_cache.pop(filename, None)
            return None
        file_id = str(files[0]["id"])
        self._file_id_cache[filename] = file_id
        return file_id

    def _read_text_file(self, filename: str) -> str | None:
        was_cached = filename in self._file_id_cache
        file_id = self._find_file_id(filename)
        if not file_id:
            return None
        url = f"{DRIVE_FILES_API}/{urllib.parse.quote(file_id, safe='')}?alt=media"
        status, body = self._api_request("GET", url)
        if status == 404 and was_cached:
            # 他端末で作り直されていた場合に備えキャッシュを破棄して1回だけ再検索
            self._file_id_cache.pop(filename, None)
            file_id = self._find_file_id(filename, bypass_cache=True)
            if not file_id:
                return None
            url = f"{DRIVE_FILES_API}/{urllib.parse.quote(file_id, safe='')}?alt=media"
            status, body = self._api_request("GET", url)
        if status == 404:
            self._file_id_cache.pop(filename, None)
            return None
        if status != 200:
            raise GoogleDriveStorageError(f"Google Drive ファイル読み込みに失敗しました（HTTP {status}）。")
        try:
            return body.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise GoogleDriveStorageError("Google Drive ファイルが UTF-8 ではありません。") from exc

    def _create_multipart(self, filename: str, parent_id: str, data_bytes: bytes, mime_type: str) -> tuple[int, bytes]:
        boundary = f"nihongo_{uuid.uuid4().hex}"
        meta = json.dumps({"name": filename, "parents": [parent_id]}).encode("utf-8")
        multipart = (
            f"--{boundary}\r\n"
            "Content-Type: application/json; charset=UTF-8\r\n\r\n"
        ).encode("utf-8") + meta + (
            f"\r\n--{boundary}\r\n"
            f"Content-Type: {mime_type}; charset=UTF-8\r\n\r\n"
        ).encode("utf-8") + data_bytes + f"\r\n--{boundary}--\r\n".encode("utf-8")

        url = f"{DRIVE_UPLOAD_API}?uploadType=multipart&fields=id"
        return self._api_request(
            "POST",
            url,
            headers={"Content-Type": f"multipart/related; boundary={boundary}"},
            body=multipart,
        )

    def _write_text_file(self, filename: str, content: str, *, mime_type: str) -> None:
        data_bytes = content.encode("utf-8")
        file_id = self._find_file_id(filename)
        if file_id:
            url = f"{DRIVE_UPLOAD_API}/{urllib.parse.quote(file_id, safe='')}?uploadType=media"
            status, _ = self._api_request(
                "PATCH",
                url,
                headers={"Content-Type": f"{mime_type}; charset=UTF-8"},
                body=data_bytes,
            )
            if status in (200, 201):
                return
            if status != 404:
                raise GoogleDriveStorageError(f"Google Drive ファイル更新に失敗しました（HTTP {status}）。")
            # キャッシュ済み ID が削除されていた場合は破棄して再作成へフォールバック
            self._file_id_cache.pop(filename, None)

        parent_id = self._ensure_parent_id()
        status, body = self._create_multipart(filename, parent_id, data_bytes, mime_type)
        if status == 404 and not self.app_data_only and self._folder_id_cache:
            self._folder_id_cache = None
            parent_id = self._ensure_parent_id()
            status, body = self._create_multipart(filename, parent_id, data_bytes, mime_type)
        if status not in (200, 201):
            raise GoogleDriveStorageError(f"Google Drive ファイル作成に失敗しました（HTTP {status}）。")
        created_id = str(_parse_json_object(body, "file_create").get("id") or "")
        if created_id:
            self._file_id_cache[filename] = created_id

    def read_profile_text(self) -> str | None:
        return self._read_text_file(self.profile_filename)

    def write_profile_text(self, content: str) -> None:
        self._write_text_file(self.profile_filename, content, mime_type="text/markdown")

    def read_inbox_text(self) -> str | None:
        return self._read_text_file(self.inbox_filename)

    def write_inbox_text(self, content: str) -> None:
        self._write_text_file(self.inbox_filename, content, mime_type="application/x-ndjson")
