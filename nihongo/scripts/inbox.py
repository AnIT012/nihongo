#!/usr/bin/env python3
"""HITL（Human-in-the-Loop）型の個人プロフィール受信箱（inbox）と profile.md 管理モジュール。

設計原則:
- `~/.nihongo/profile.md` を唯一の正（Single Source of Truth）として保つ。
- 自動化するのは候補を `inbox.jsonl` に拾うところまで（propose は profile.md を一切書き換えない）。
- `profile.md` への反映は必ず本人承認（approve）を経由する。
- 標準ライブラリだけで動作する。
"""
from __future__ import annotations

import datetime as _dt
import json
import os
import re
import tempfile
import unicodedata
import uuid
from typing import Any, Protocol, runtime_checkable

VALID_SCENES = ("common", "casual", "work", "formal")
VALID_KINDS = ("forbidden", "rule", "tone", "first_person")
VALID_STATUSES = ("pending", "approved", "rejected")

DEFAULT_PROFILE_TEMPLATE = """# 私の書き方

## [common]
- 一人称：
- 絶対に言わない表現：
- 書く時の考え方：

## [casual]
- 場面：友達・身内・雑談
- 口調・記号：

## [work]
- 場面：社内チャット・PR・同僚
- 口調・記号：

## [formal]
- 場面：目上・社外メール・公式お知らせ（[casual] の崩しや絵文字は持ち込まない）
- 口調・記号：
"""

_SECTION_DEFAULTS: dict[str, str] = {
    "common": "- 一人称：\n- 絶対に言わない表現：\n- 書く時の考え方：",
    "casual": "- 場面：友達・身内・雑談\n- 口調・記号：",
    "work": "- 場面：社内チャット・PR・同僚\n- 口調・記号：",
    "formal": "- 場面：目上・社外メール・公式お知らせ（[casual] の崩しや絵文字は持ち込まない）\n- 口調・記号：",
}

_HEADING_RE = re.compile(r"^\s*(#{1,6})\s+(.+?)\s*$")
_SCENE_TAG_RE = re.compile(r"\[(common|casual|work|formal)\]", re.IGNORECASE)

# PII / 個人情報ガード（NFKC 正規化後にメール・電話・秘密鍵/トークンを拒否）
_DASH_TRANS = str.maketrans({
    "\u2212": "-",  # MINUS SIGN
    "\u2010": "-",  # HYPHEN
    "\u2011": "-",  # NON-BREAKING HYPHEN
    "\u2012": "-",  # FIGURE DASH
    "\u2013": "-",  # EN DASH
    "\u2014": "-",  # EM DASH
    "\u2015": "-",  # HORIZONTAL BAR
    "\u30fc": "-",  # KATAKANA-HIRAGANA PROLONGED SOUND MARK (全角電話番号誤入力対策)
})
_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_PHONE_RE = re.compile(
    r"(?<!\d)(?:"
    r"\+81[-\s]?\d{1,4}[-\s]?\d{1,4}[-\s]?\d{3,4}"
    r"|0\d{1,4}[-\s(]+\d{1,4}[-\s)]+\d{3,4}"
    r"|0[789]0\d{8}"
    r"|0\d{9}"
    r")(?!\d)"
)
_SECRET_RE = re.compile(
    r"(?:"
    r"(?<![A-Za-z0-9_])sk-(?:proj-|ant-)?[A-Za-z0-9_-]{16,}"
    r"|(?<![A-Za-z0-9_])ghp_[A-Za-z0-9]{20,}"
    r"|(?<![A-Za-z0-9_])github_pat_[A-Za-z0-9_]{20,}"
    r"|(?<![A-Za-z0-9_])AKIA[0-9A-Z]{16}(?![A-Za-z0-9])"
    r"|(?<![A-Za-z0-9_])xox[baprs]-[A-Za-z0-9-]{10,}"
    r"|(?<![A-Za-z0-9_])AIza[0-9A-Za-z\-_]{20,}"
    r"|-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----"
    r")"
)
MAX_VALUE_LEN = 500

# formal 場面の崩しガード
_CASUAL_SSU_RE = re.compile(r"っす(?![ぐうる])")
_CASUAL_LAUGH_RE = re.compile(
    r"(?:(?<![A-Za-z0-9./])[wｗ]{2,}(?![A-Za-z0-9./])|(?<![A-Za-z0-9])[wｗ](?=$|[\s。、！？!?\n]))"
)
_EMOJI_RE = re.compile(r"[\U0001F300-\U0001FAFF\u2728\u2764\u2763\u2757\u2753\u2600\u2601\u2614\u26A1\u2615]")


def get_nihongo_home(home: str | None = None) -> str:
    """nihongo のデータディレクトリ（既定: ~/.nihongo、環境変数 NIHONGO_HOME で上書き可）。"""
    if home:
        return os.path.abspath(os.path.expanduser(home))
    env_home = os.environ.get("NIHONGO_HOME", "").strip()
    if env_home:
        return os.path.abspath(os.path.expanduser(env_home))
    return os.path.abspath(os.path.expanduser("~/.nihongo"))


def default_profile_path(home: str | None = None) -> str:
    return os.path.join(get_nihongo_home(home), "profile.md")


def default_inbox_path(home: str | None = None) -> str:
    return os.path.join(get_nihongo_home(home), "inbox.jsonl")


@runtime_checkable
class ProfileStorage(Protocol):
    """profile.md と inbox.jsonl の保存先を抽象化する最小インターフェース（4メソッド）。

    ローカルファイル（LocalFileStorage）だけでなく、将来 Google Drive などの
    ユーザー自身のクラウドストレージへ差し替えても HITL ロジックをそのまま再利用できる。
    """

    @property
    def profile_location(self) -> str: ...

    @property
    def inbox_location(self) -> str: ...

    def read_profile_text(self) -> str | None: ...

    def write_profile_text(self, content: str) -> None: ...

    def read_inbox_text(self) -> str | None: ...

    def write_inbox_text(self, content: str) -> None: ...


class LocalFileStorage:
    """既定の保存先（~/.nihongo/profile.md と ~/.nihongo/inbox.jsonl）。"""

    def __init__(
        self,
        *,
        home: str | None = None,
        profile_path: str | None = None,
        inbox_path: str | None = None,
    ) -> None:
        self._profile_path = (
            os.path.abspath(os.path.expanduser(profile_path))
            if profile_path
            else default_profile_path(home)
        )
        self._inbox_path = (
            os.path.abspath(os.path.expanduser(inbox_path))
            if inbox_path
            else default_inbox_path(home)
        )

    @property
    def profile_location(self) -> str:
        return self._profile_path

    @property
    def inbox_location(self) -> str:
        return self._inbox_path

    def read_profile_text(self) -> str | None:
        if not os.path.isfile(self._profile_path):
            return None
        with open(self._profile_path, encoding="utf-8-sig") as f:
            return f.read()

    def write_profile_text(self, content: str) -> None:
        _atomic_write_utf8(self._profile_path, content)

    def read_inbox_text(self) -> str | None:
        if not os.path.isfile(self._inbox_path):
            return None
        with open(self._inbox_path, encoding="utf-8-sig") as f:
            return f.read()

    def write_inbox_text(self, content: str) -> None:
        _atomic_write_utf8(self._inbox_path, content)


def _resolve_storage(
    storage: ProfileStorage | None = None,
    *,
    profile_path: str | None = None,
    inbox_path: str | None = None,
) -> ProfileStorage:
    if storage is not None:
        return storage
    return LocalFileStorage(profile_path=profile_path, inbox_path=inbox_path)


def _utc_now_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _normalize_newlines(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def _atomic_write_utf8(path: str, content: str) -> None:
    parent = os.path.dirname(os.path.abspath(path))
    os.makedirs(parent, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(prefix=".nihongo_tmp_", dir=parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, path)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def _check_pii(texts: list[str]) -> str | None:
    """メールアドレス・電話番号・APIキー等の個人情報が混ざっていれば理由を返す（NFKC正規化対応）。"""
    for raw in texts:
        if not raw:
            continue
        norm = unicodedata.normalize("NFKC", raw).translate(_DASH_TRANS)
        if _EMAIL_RE.search(norm):
            return "メールアドレスが含まれているため記録できません（個人情報保護）。"
        if _PHONE_RE.search(norm):
            return "電話番号と思われる数字列が含まれているため記録できません（個人情報保護）。"
        if _SECRET_RE.search(norm):
            return "APIキー・秘密鍵と思われる文字列が含まれているため記録できません。"
    return None


def _check_formal_boundary(scene: str, kind: str, value: str) -> str | None:
    """formal 場面への崩し表現混入を警告する（forbidden での禁止指定は許可）。"""
    if scene != "formal" or kind == "forbidden":
        return None
    if _CASUAL_SSU_RE.search(value) or _CASUAL_LAUGH_RE.search(value) or _EMOJI_RE.search(value):
        return "[場面ガード] [formal] 場面にくだけた語尾や絵文字を含める候補です。本当に公式・目上向けか確認してください。"
    return None


def _normalize_value(value: str) -> str:
    cleaned = _normalize_newlines(value).strip()
    cleaned = re.sub(r"\s*\n\s*", " ", cleaned)
    return cleaned


def _strip_outer_quotes(text: str) -> str:
    """先頭と末尾が対になっている引用符だけを外す（文中の「」は壊さない）。"""
    v = text.strip(" \t\u3000")
    pairs = (("「", "」"), ("『", "』"), ('"', '"'), ("'", "'"), ("“", "”"))
    changed = True
    while changed and len(v) >= 2:
        changed = False
        for left, right in pairs:
            if v.startswith(left) and v.endswith(right):
                v = v[len(left) : len(v) - len(right)].strip(" \t\u3000")
                changed = True
                break
    return v


def _format_forbidden_item(value: str) -> str:
    v = _strip_outer_quotes(value)
    if not v:
        return ""
    return f"「{v}」"


def load_inbox(
    inbox_path: str | None = None,
    *,
    storage: ProfileStorage | None = None,
) -> list[dict[str, Any]]:
    store = _resolve_storage(storage, inbox_path=inbox_path)
    raw = store.read_inbox_text()
    if not raw:
        return []
    entries: list[dict[str, Any]] = []
    for line in _normalize_newlines(raw).split("\n"):
        stripped = line.strip()
        if not stripped:
            continue
        try:
            obj = json.loads(stripped)
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict) and "id" in obj:
            entries.append(obj)
    return entries


def save_inbox(
    entries: list[dict[str, Any]],
    inbox_path: str | None = None,
    *,
    storage: ProfileStorage | None = None,
) -> str:
    store = _resolve_storage(storage, inbox_path=inbox_path)
    lines = [json.dumps(item, ensure_ascii=False) for item in entries]
    content = ("\n".join(lines) + "\n") if lines else ""
    store.write_inbox_text(content)
    return store.inbox_location


def _make_entry_id(existing_ids: set[str]) -> str:
    date_tag = _dt.datetime.now().strftime("%Y%m%d")
    for _ in range(20):
        cand = f"inb_{date_tag}_{uuid.uuid4().hex[:6]}"
        if cand not in existing_ids:
            return cand
    return f"inb_{date_tag}_{uuid.uuid4().hex[:10]}"


def _dedup_key(scene: str, kind: str, value: str) -> tuple[str, str, str]:
    norm = unicodedata.normalize("NFKC", _normalize_value(value)).strip("「」『』\"' ")
    return (scene.lower(), kind.lower(), norm)


def propose_entry(
    *,
    scene: str,
    kind: str,
    value: str,
    reason: str = "",
    example_before: str = "",
    example_after: str = "",
    source: str = "chat",
    allow_resubmit: bool = False,
    inbox_path: str | None = None,
    profile_path: str | None = None,
    storage: ProfileStorage | None = None,
) -> dict[str, Any]:
    """追記候補を inbox.jsonl に登録する。profile.md は絶対に書き換えない（HITL原則）。"""
    store = _resolve_storage(storage, profile_path=profile_path, inbox_path=inbox_path)
    scene_norm = scene.strip().lower()
    kind_norm = kind.strip().lower()
    if scene_norm not in VALID_SCENES:
        raise ValueError(f"不正な scene です: {scene!r}（{', '.join(VALID_SCENES)} から指定）")
    if kind_norm not in VALID_KINDS:
        raise ValueError(f"不正な kind です: {kind!r}（{', '.join(VALID_KINDS)} から指定）")

    val = _normalize_value(value)
    if not val:
        raise ValueError("value（追記したい内容）が空です。")
    if len(val) > MAX_VALUE_LEN:
        raise ValueError(f"value が長すぎます（上限 {MAX_VALUE_LEN} 文字）。1行の短いルールに絞ってください。")

    if kind_norm == "first_person" and scene_norm != "common":
        scene_norm = "common"

    pii_err = _check_pii([val, reason, example_before, example_after, source])
    if pii_err:
        raise ValueError(pii_err)

    warning = _check_formal_boundary(scene_norm, kind_norm, val)

    entries = load_inbox(storage=store)
    target_key = _dedup_key(scene_norm, kind_norm, val)

    # すでに pending に同一候補がある場合は重複登録せず既存を返す
    for existing in entries:
        ex_key = _dedup_key(
            str(existing.get("scene", "")),
            str(existing.get("kind", "")),
            str(existing.get("value", "")),
        )
        if ex_key != target_key:
            continue
        st = existing.get("status")
        if st == "pending":
            return {
                "created": False,
                "duplicate": True,
                "previously_rejected": False,
                "entry": existing,
                "warning": warning,
                "message": f"同一の候補がすでに保留中です（ID: {existing['id']}）。",
            }
        if st == "rejected" and not allow_resubmit:
            return {
                "created": False,
                "duplicate": False,
                "previously_rejected": True,
                "entry": existing,
                "warning": warning,
                "message": f"過去に却下済みの候補のため再登録しませんでした（ID: {existing['id']}）。",
            }

    # profile.md にすでに同じ表現が含まれている場合は重複登録しない
    already_in_profile = False
    existing_profile = store.read_profile_text()
    if existing_profile is not None:
        p_text = unicodedata.normalize("NFKC", existing_profile)
        needle = unicodedata.normalize("NFKC", _strip_outer_quotes(val))
        if needle and needle in p_text:
            already_in_profile = True
    if already_in_profile and not allow_resubmit:
        return {
            "created": False,
            "duplicate": False,
            "previously_rejected": False,
            "already_in_profile": True,
            "entry": None,
            "warning": warning,
            "message": f"「{val}」はすでに profile.md に登録済みのため、受信箱へ重複追加しませんでした。",
        }

    existing_ids = {str(e.get("id", "")) for e in entries}
    entry: dict[str, Any] = {
        "id": _make_entry_id(existing_ids),
        "status": "pending",
        "scene": scene_norm,
        "kind": kind_norm,
        "value": val,
        "reason": _normalize_value(reason),
        "example_before": _normalize_value(example_before),
        "example_after": _normalize_value(example_after),
        "source": _normalize_value(source) or "chat",
        "created_at": _utc_now_iso(),
        "decided_at": None,
        "decision_note": "",
    }
    if warning:
        entry["warning"] = warning

    entries.append(entry)
    saved_path = save_inbox(entries, storage=store)
    return {
        "created": True,
        "duplicate": False,
        "already_in_profile": already_in_profile,
        "inbox_path": saved_path,
        "entry": entry,
        "warning": warning,
        "message": (
            f"受信箱（inbox）に候補を保存しました（ID: {entry['id']}）。"
            "profile.md はまだ変更されていません。本人承認後に反映されます。"
        ),
    }


def list_inbox(
    *,
    status: str | None = "pending",
    scene: str | None = None,
    inbox_path: str | None = None,
    storage: ProfileStorage | None = None,
) -> list[dict[str, Any]]:
    entries = load_inbox(inbox_path, storage=storage)
    out: list[dict[str, Any]] = []
    for item in entries:
        if status and status != "all" and item.get("status") != status:
            continue
        if scene and item.get("scene") != scene.lower():
            continue
        out.append(item)
    return out


def _find_section_bounds(lines: list[str], scene: str) -> tuple[int, int] | None:
    """`## [scene]` セクションの (見出し行index, セクション終端index) を返す。"""
    start_idx: int | None = None
    start_level = 2
    for i, line in enumerate(lines):
        m = _HEADING_RE.match(line)
        if not m:
            continue
        level = len(m.group(1))
        tag_m = _SCENE_TAG_RE.search(m.group(2))
        if start_idx is None:
            if tag_m and tag_m.group(1).lower() == scene:
                start_idx = i
                start_level = level
        else:
            if level <= start_level:
                return (start_idx, i)
    if start_idx is not None:
        return (start_idx, len(lines))
    return None


def _target_field_label(scene: str, kind: str) -> str:
    if kind == "forbidden":
        return "絶対に言わない表現"
    if kind == "first_person":
        return "一人称"
    if kind == "tone":
        return "口調・記号" if scene != "common" else "書く時の考え方"
    # kind == "rule"
    return "書く時の考え方" if scene == "common" else "口調・記号"


def apply_entry_to_profile_text(profile_text: str, entry: dict[str, Any]) -> tuple[str, bool, str]:
    """承認済みの 1 エントリを profile.md テキストへ外科的に反映する。

    Returns:
        (updated_text, changed, summary_line)
    """
    scene = str(entry.get("scene", "common")).lower()
    kind = str(entry.get("kind", "rule")).lower()
    value = _normalize_value(str(entry.get("value", "")))
    if not value:
        return (profile_text, False, "値が空のためスキップしました。")

    text = _normalize_newlines(profile_text)
    if not text.strip():
        text = DEFAULT_PROFILE_TEMPLATE
    lines = text.split("\n")

    bounds = _find_section_bounds(lines, scene)
    if bounds is None:
        # 末尾に空行を挟んで該当セクションを追加
        while lines and lines[-1] == "":
            lines.pop()
        if lines:
            lines.append("")
        lines.append(f"## [{scene}]")
        lines.extend(_SECTION_DEFAULTS[scene].split("\n"))
        lines.append("")
        bounds = _find_section_bounds(lines, scene)
        assert bounds is not None

    sec_start, sec_end = bounds
    label = _target_field_label(scene, kind)
    field_re = re.compile(rf"^(\s*[-*・]\s*(?:\*\*)?{re.escape(label)}(?:\*\*)?\s*[：:])(.*)$")

    # 既存フィールド行を探す
    field_idx: int | None = None
    for idx in range(sec_start + 1, sec_end):
        if field_re.match(lines[idx]):
            field_idx = idx
            break

    if kind == "forbidden":
        formatted = _format_forbidden_item(value)
        sep = "、"
    elif kind == "first_person":
        formatted = value
        sep = "／"
    else:
        formatted = value
        sep = "。"

    if field_idx is not None:
        m = field_re.match(lines[field_idx])
        assert m is not None
        prefix, rhs = m.group(1), m.group(2).strip()
        rhs_norm = unicodedata.normalize("NFKC", rhs)
        needle_norm = unicodedata.normalize("NFKC", value.strip("「」『』\"' "))
        if needle_norm and needle_norm in rhs_norm:
            return ("\n".join(lines).rstrip("\n") + "\n", False, f"[{scene}] {label} にはすでに含まれています。")

        if not rhs:
            new_rhs = formatted
        else:
            if sep == "。" and rhs.endswith(("。", "！", "!", "？", "?")):
                new_rhs = f"{rhs}{formatted}"
            elif sep == "、" and rhs.endswith(("、", ",")):
                new_rhs = f"{rhs}{formatted}"
            else:
                new_rhs = f"{rhs}{sep}{formatted}"
        lines[field_idx] = f"{prefix}{new_rhs}"
    else:
        # フィールド行が無ければセクション末尾（空行の直前）に追加
        insert_at = sec_end
        while insert_at > sec_start + 1 and lines[insert_at - 1].strip() == "":
            insert_at -= 1
        lines.insert(insert_at, f"- {label}：{formatted}")

    updated = "\n".join(lines).rstrip("\n") + "\n"
    return (updated, True, f"[{scene}] {label} に「{value}」を反映しました。")


def approve_entries(
    entry_ids: list[str] | None = None,
    *,
    approve_all: bool = False,
    dry_run: bool = False,
    force: bool = False,
    inbox_path: str | None = None,
    profile_path: str | None = None,
    storage: ProfileStorage | None = None,
) -> dict[str, Any]:
    """指定 ID（または --all）の保留候補を承認し、profile.md に反映する（唯一の profile.md 書き込み口）。"""
    store = _resolve_storage(storage, profile_path=profile_path, inbox_path=inbox_path)
    entries = load_inbox(storage=store)
    p_path = store.profile_location
    existing_profile = store.read_profile_text()
    current_text = existing_profile if existing_profile is not None else ""

    id_set = set(entry_ids or [])
    if not approve_all and not id_set:
        raise ValueError("承認する ID を指定するか、approve_all=True を指定してください。")

    matched: list[dict[str, Any]] = []
    not_found: list[str] = []
    skipped_warnings: list[dict[str, Any]] = []
    results: list[dict[str, Any]] = []

    by_id = {str(e.get("id", "")): e for e in entries}
    if not approve_all:
        for req_id in entry_ids or []:
            if req_id not in by_id:
                not_found.append(req_id)

    working_text = current_text
    now_iso = _utc_now_iso()
    any_profile_change = False

    for item in entries:
        item_id = str(item.get("id", ""))
        if approve_all:
            if item.get("status") != "pending":
                continue
        else:
            if item_id not in id_set:
                continue

        if item.get("status") != "pending":
            results.append({
                "id": item_id,
                "status": item.get("status"),
                "applied": False,
                "message": f"すでに {item.get('status')} です。",
            })
            continue

        warning = _check_formal_boundary(
            str(item.get("scene", "")),
            str(item.get("kind", "")),
            str(item.get("value", "")),
        )
        if warning and not force:
            skipped_warnings.append({"id": item_id, "warning": warning})
            results.append({
                "id": item_id,
                "status": "pending",
                "applied": False,
                "blocked_by_guard": True,
                "message": warning + "（強制反映する場合は force=True / --force を指定）",
            })
            continue

        matched.append(item)
        working_text, changed, summary = apply_entry_to_profile_text(working_text, item)
        if changed:
            any_profile_change = True
        if not dry_run:
            item["status"] = "approved"
            item["decided_at"] = now_iso
            item["decision_note"] = summary
        results.append({
            "id": item_id,
            "status": "approved" if not dry_run else "pending (dry-run)",
            "applied": changed,
            "message": summary,
        })

    if not dry_run and matched:
        if any_profile_change or existing_profile is None:
            store.write_profile_text(working_text)
        save_inbox(entries, storage=store)

    return {
        "dry_run": dry_run,
        "profile_path": p_path,
        "approved_count": len(matched),
        "profile_updated": any_profile_change and not dry_run,
        "not_found": not_found,
        "blocked_by_guard": skipped_warnings,
        "results": results,
        "preview_profile": working_text if dry_run else None,
    }


def reject_entries(
    entry_ids: list[str] | None = None,
    *,
    reject_all: bool = False,
    reason: str = "",
    inbox_path: str | None = None,
    storage: ProfileStorage | None = None,
) -> dict[str, Any]:
    """指定 ID（または reject_all=True）の保留候補を却下する（profile.md には一切触れない）。"""
    id_set = set(entry_ids or [])
    if not reject_all and not id_set:
        raise ValueError("却下する ID を指定するか、reject_all=True を指定してください。")
    store = _resolve_storage(storage, inbox_path=inbox_path)
    entries = load_inbox(storage=store)
    by_id = {str(e.get("id", "")): e for e in entries}
    not_found = [] if reject_all else [req_id for req_id in (entry_ids or []) if req_id not in by_id]

    now_iso = _utc_now_iso()
    rejected: list[str] = []
    results: list[dict[str, Any]] = []
    note = _normalize_value(reason)

    for item in entries:
        item_id = str(item.get("id", ""))
        if reject_all:
            if item.get("status") != "pending":
                continue
        elif item_id not in id_set:
            continue
        if item.get("status") != "pending":
            results.append({
                "id": item_id,
                "status": item.get("status"),
                "rejected": False,
                "message": f"すでに {item.get('status')} です。",
            })
            continue
        item["status"] = "rejected"
        item["decided_at"] = now_iso
        item["decision_note"] = note
        rejected.append(item_id)
        results.append({
            "id": item_id,
            "status": "rejected",
            "rejected": True,
            "message": "却下しました（profile.md は変更していません）。",
        })

    if rejected:
        save_inbox(entries, storage=store)

    return {
        "rejected_count": len(rejected),
        "not_found": not_found,
        "results": results,
    }


def read_profile(
    *,
    profile_path: str | None = None,
    inbox_path: str | None = None,
    scene: str | None = None,
    storage: ProfileStorage | None = None,
) -> dict[str, Any]:
    """profile.md の生テキスト・セクション別内容・保留中 inbox 件数を返す。"""
    store = _resolve_storage(storage, profile_path=profile_path, inbox_path=inbox_path)
    p_path = store.profile_location
    loaded = store.read_profile_text()
    exists = loaded is not None
    raw = _normalize_newlines(loaded) if loaded is not None else ""

    sections: dict[str, str] = {}
    if raw:
        lines = raw.split("\n")
        for sc in VALID_SCENES:
            bounds = _find_section_bounds(lines, sc)
            if bounds is not None:
                s, e = bounds
                sections[sc] = "\n".join(lines[s:e]).strip()

    pending_count = len(list_inbox(status="pending", storage=store))

    filtered_markdown = raw
    if scene:
        sc = scene.strip().lower()
        if sc not in VALID_SCENES:
            raise ValueError(f"不正な scene です: {scene!r}")
        parts: list[str] = []
        if "common" in sections:
            parts.append(sections["common"])
        if sc != "common" and sc in sections:
            parts.append(sections[sc])
        filtered_markdown = "\n\n".join(parts)

    return {
        "exists": exists,
        "profile_path": p_path,
        "scene": scene.lower() if scene else None,
        "pending_inbox_count": pending_count,
        "sections": sections,
        "markdown": filtered_markdown,
        "raw": raw,
    }
