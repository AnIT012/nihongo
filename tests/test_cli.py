"""cli.py のテスト。python -m unittest discover -s tests -q で動く（標準ライブラリだけ）。"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(HERE, ".."))
CLI = os.path.join(REPO_ROOT, "nihongo", "scripts", "cli.py")
SCRIPTS_DIR = os.path.join(REPO_ROOT, "nihongo", "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

import cli as cli_mod  # noqa: E402


def run_cli(
    args: list[str],
    cwd: str | None = None,
    stdin_text: str | None = None,
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    return subprocess.run(
        [sys.executable, CLI, *args],
        cwd=cwd,
        input=stdin_text,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
        check=False,
    )


def run_git(args: list[str], cwd: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    )


def write_utf8(path: str, text: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def read_utf8(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


class CliDiffTests(unittest.TestCase):
    def test_diff_clean_exits_zero(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            orig = os.path.join(d, "orig.md")
            draft = os.path.join(d, "draft.md")
            write_utf8(orig, "申請の締め切りは午後3時です。窓口は西口です。\n")
            write_utf8(draft, "申請の締め切りは15時、窓口は西口です。\n")

            res = run_cli(["diff", orig, draft])
            self.assertEqual(res.returncode, 0, res.stderr)
            self.assertIn("見直す候補はありません", res.stdout)

    def test_diff_detects_changed_number_and_promise(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            orig = os.path.join(d, "orig.md")
            draft = os.path.join(d, "draft.md")
            write_utf8(orig, "再送は最大2回までです。来週公開する予定です。\n")
            write_utf8(draft, "再送は最大3回までです。来週公開します。\n")

            res = run_cli(["diff", orig, draft])
            self.assertEqual(res.returncode, 1)
            self.assertIn("[数値・日時]", res.stdout)
            self.assertIn("[確度・必須度]", res.stdout)

    def test_diff_allows_requested_edit_via_file_and_inline(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            orig = os.path.join(d, "orig.md")
            draft = os.path.join(d, "draft.md")
            req_file = os.path.join(d, "req.md")
            req_text = "お問い合わせ番号4821-0093を［非公開］に置き換えてください。"
            write_utf8(orig, "お問い合わせ番号は4821-0093です。\n")
            write_utf8(draft, "お問い合わせ番号は［非公開］です。\n")
            write_utf8(req_file, req_text)

            res_file = run_cli(["diff", orig, draft, "--request", req_file])
            self.assertEqual(res_file.returncode, 0, res_file.stdout + res_file.stderr)

            res_inline = run_cli(["diff", orig, draft, "--request", req_text])
            self.assertEqual(res_inline.returncode, 0, res_inline.stdout + res_inline.stderr)

    def test_diff_json_output(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            orig = os.path.join(d, "orig.md")
            draft = os.path.join(d, "draft.md")
            write_utf8(orig, "再送は最大2回までです。\n")
            write_utf8(draft, "再送は最大3回までです。\n")

            res = run_cli(["diff", orig, draft, "--json"])
            self.assertEqual(res.returncode, 1)
            data = json.loads(res.stdout)
            self.assertFalse(data["clean"])
            self.assertGreaterEqual(data["count"], 1)
            self.assertEqual(data["count"], len(data["findings"]))
            self.assertTrue(any("[数値・日時]" in item for item in data["findings"]))


class CliFixTests(unittest.TestCase):
    def test_fix_restores_broken_number_and_trims_comma(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            orig = os.path.join(d, "orig.md")
            draft = os.path.join(d, "draft.md")
            out = os.path.join(d, "out.md")
            write_utf8(orig, "再送は最大2回までです。資料を、明日送ります。\n")
            write_utf8(draft, "再送は最大3回までです。資料を、明日送ります。\n")

            res = run_cli(["fix", orig, draft, out])
            self.assertEqual(res.returncode, 0, res.stderr)
            result = read_utf8(out)
            self.assertIn("2回", result)
            self.assertNotIn("3回", result)
            self.assertIn("資料を明日送ります。", result)
            self.assertNotIn("資料を、明日送ります。", result)

    def test_fix_no_trim_commas(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            orig = os.path.join(d, "orig.md")
            draft = os.path.join(d, "draft.md")
            out = os.path.join(d, "out.md")
            write_utf8(orig, "再送は最大2回までです。資料を、明日送ります。\n")
            write_utf8(draft, "再送は最大3回までです。資料を、明日送ります。\n")

            res = run_cli(["fix", orig, draft, out, "--no-trim-commas"])
            self.assertEqual(res.returncode, 0, res.stderr)
            result = read_utf8(out)
            self.assertIn("2回", result)
            self.assertIn("資料を、明日送ります。", result)

    def test_fix_fail_on_remaining(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            orig = os.path.join(d, "orig.md")
            draft = os.path.join(d, "draft.md")
            out = os.path.join(d, "out.md")
            # 発信者・権威の追加は自動差し戻し対象外なので残存候補になる
            write_utf8(orig, "システムメンテナンスのお知らせです。\n")
            write_utf8(draft, "【緊急】システムメンテナンスのお知らせです。\n")

            res_ok = run_cli(["fix", orig, draft, out])
            self.assertEqual(res_ok.returncode, 0, res_ok.stderr)
            self.assertIn("残っている候補", res_ok.stdout)

            res_fail = run_cli(["fix", orig, draft, out, "--fail-on-remaining"])
            self.assertEqual(res_fail.returncode, 1)
            self.assertIn("[発信者・権威]", res_fail.stdout)


class CliGitTests(unittest.TestCase):
    def _init_repo(self, root: str, files: dict[str, str]) -> None:
        run_git(["init"], cwd=root)
        run_git(["config", "user.name", "Test User"], cwd=root)
        run_git(["config", "user.email", "test@example.com"], cwd=root)
        for rel, content in files.items():
            write_utf8(os.path.join(root, rel), content)
        run_git(["add", "."], cwd=root)
        run_git(["commit", "-m", "initial"], cwd=root)

    def test_git_detects_drift_and_hook_exits_two(self) -> None:
        with tempfile.TemporaryDirectory() as repo:
            self._init_repo(repo, {
                "docs/guide.md": "再送は最大2回までです。来週公開する予定です。\n",
            })
            write_utf8(
                os.path.join(repo, "docs/guide.md"),
                "再送は最大3回までです。来週公開します。\n",
            )

            res = run_cli(["git"], cwd=repo)
            self.assertEqual(res.returncode, 1)
            self.assertIn("docs/guide.md", res.stdout)
            self.assertIn("[数値・日時]", res.stdout)

            res_json = run_cli(["git", "--json"], cwd=repo)
            self.assertEqual(res_json.returncode, 1)
            data = json.loads(res_json.stdout)
            self.assertFalse(data["clean"])
            self.assertEqual(data["flagged"], 1)
            self.assertEqual(data["files"][0]["path"], "docs/guide.md")

            res_hook = run_cli(["git", "--hook"], cwd=repo, stdin_text="")
            self.assertEqual(res_hook.returncode, 2)
            self.assertIn("docs/guide.md", res_hook.stderr)
            self.assertIn("[数値・日時]", res_hook.stderr)

    def test_git_clean_edit_exits_zero(self) -> None:
        with tempfile.TemporaryDirectory() as repo:
            self._init_repo(repo, {
                "notes.md": "申請の締め切りは午後3時です。窓口は西口です。\n",
            })
            write_utf8(
                os.path.join(repo, "notes.md"),
                "申請の締め切りは15時、窓口は西口です。\n",
            )

            res = run_cli(["git"], cwd=repo)
            self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
            self.assertIn("見直す候補はありません", res.stdout)

            res_hook = run_cli(["git", "--hook"], cwd=repo, stdin_text="")
            self.assertEqual(res_hook.returncode, 0, res_hook.stderr)
            self.assertEqual(res_hook.stderr, "")

    def test_git_hook_stdin_targets_specific_file_and_handles_invalid_stdin(self) -> None:
        with tempfile.TemporaryDirectory() as repo:
            self._init_repo(repo, {
                "clean.md": "申請の締め切りは午後3時です。\n",
                "broken.md": "再送は最大2回までです。\n",
            })
            clean_path = os.path.join(repo, "clean.md")
            broken_path = os.path.join(repo, "broken.md")
            write_utf8(clean_path, "申請の締め切りは15時です。\n")
            write_utf8(broken_path, "再送は最大5回までです。\n")

            # clean.md だけを対象にしたフック呼び出しは終了 0
            payload_clean = json.dumps({"tool_input": {"file_path": clean_path}})
            res_clean = run_cli(["git", "--hook"], cwd=repo, stdin_text=payload_clean)
            self.assertEqual(res_clean.returncode, 0, res_clean.stderr)

            # broken.md を対象にしたフック呼び出しは終了 2
            payload_broken = json.dumps({"tool_input": {"file_path": broken_path}})
            res_broken = run_cli(["git", "--hook"], cwd=repo, stdin_text=payload_broken)
            self.assertEqual(res_broken.returncode, 2)
            self.assertIn("broken.md", res_broken.stderr)

            # 対象外拡張子（.py）なら即座に終了 0
            payload_py = json.dumps({"tool_input": {"file_path": os.path.join(repo, "app.py")}})
            res_py = run_cli(["git", "--hook"], cwd=repo, stdin_text=payload_py)
            self.assertEqual(res_py.returncode, 0, res_py.stderr)

            # 壊れた JSON でも落ちずにリポジトリ全体の変更を確認できる
            res_bad_json = run_cli(["git", "--hook"], cwd=repo, stdin_text="{not-json")
            self.assertEqual(res_bad_json.returncode, 2)
            self.assertIn("broken.md", res_bad_json.stderr)

    def test_git_untracked_and_non_utf8_do_not_crash(self) -> None:
        with tempfile.TemporaryDirectory() as repo:
            self._init_repo(repo, {
                "existing.md": "開始は10時です。\n",
            })
            untracked = os.path.join(repo, "new_doc.md")
            write_utf8(untracked, "新しく追加した文書です。数値は99件です。\n")

            res = run_cli(["git"], cwd=repo)
            self.assertEqual(res.returncode, 0, res.stdout + res.stderr)

            payload_new = json.dumps({"file_path": untracked})
            res_hook = run_cli(["git", "--hook"], cwd=repo, stdin_text=payload_new)
            self.assertEqual(res_hook.returncode, 0, res_hook.stderr)

            # 既存ファイルを非 UTF-8 バイト列にしてもクラッシュせずスキップする
            with open(os.path.join(repo, "existing.md"), "wb") as f:
                f.write(b"\xff\xfe\x80\x81")
            res_bin = run_cli(["git"], cwd=repo)
            self.assertEqual(res_bin.returncode, 0, res_bin.stdout + res_bin.stderr)

    def test_git_staged_mode(self) -> None:
        with tempfile.TemporaryDirectory() as repo:
            self._init_repo(repo, {
                "doc.md": "開始は午後3時です。最大2回まで。\n",
            })
            doc_path = os.path.join(repo, "doc.md")
            # ステージには意味が変わらない修正を入れ、作業ツリーには壊れた修正を入れる
            write_utf8(doc_path, "開始は15時です。最大2回まで。\n")
            run_git(["add", "doc.md"], cwd=repo)
            write_utf8(doc_path, "開始は15時です。最大9回まで。\n")

            res_staged_ok = run_cli(["git", "--staged"], cwd=repo)
            self.assertEqual(res_staged_ok.returncode, 0, res_staged_ok.stdout + res_staged_ok.stderr)

            res_worktree_ng = run_cli(["git"], cwd=repo)
            self.assertEqual(res_worktree_ng.returncode, 1)

            # 壊れた修正をステージしたら --staged でも検出する
            run_git(["add", "doc.md"], cwd=repo)
            res_staged_ng = run_cli(["git", "--staged"], cwd=repo)
            self.assertEqual(res_staged_ng.returncode, 1)


class CliProfileAndSceneTests(unittest.TestCase):
    SAMPLE_PROFILE = (
        "# 私の書き方\n\n"
        "## [common]\n"
        "- 一人称：僕\n"
        "- 絶対に言わない表現：させていただきます / ご査収のほど（例：過剰な敬語）\n\n"
        "## [formal]\n"
        "- 場面：目上・社外\n"
    )

    def test_diff_profile_detects_new_forbidden_and_ignores_existing(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            prof = os.path.join(d, "profile.md")
            orig = os.path.join(d, "orig.md")
            draft_ng = os.path.join(d, "draft_ng.md")
            draft_ok = os.path.join(d, "draft_ok.md")
            write_utf8(prof, self.SAMPLE_PROFILE)
            write_utf8(orig, "資料を送ります。\n")
            write_utf8(draft_ng, "資料を送付させていただきます。\n")
            write_utf8(draft_ok, "資料をお送りします。\n")

            res_ng = run_cli(["diff", orig, draft_ng, "--profile", prof])
            self.assertEqual(res_ng.returncode, 1)
            self.assertIn("させていただきます", res_ng.stdout)

            res_ok = run_cli(["diff", orig, draft_ok, "--profile", prof])
            self.assertEqual(res_ok.returncode, 0, res_ok.stdout + res_ok.stderr)

            # 原文に元からある避ける表現は増分ではないので検知しない
            orig_existing = os.path.join(d, "orig_ex.md")
            write_utf8(orig_existing, "資料を送付させていただきます。\n")
            res_ex = run_cli(["diff", orig_existing, draft_ng, "--profile", prof])
            self.assertEqual(res_ex.returncode, 0, res_ex.stdout + res_ex.stderr)

    def test_diff_scene_formal_detects_casual_leaks(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            orig = os.path.join(d, "orig.md")
            draft_ssu = os.path.join(d, "ssu.md")
            draft_w = os.path.join(d, "w.md")
            draft_emoji = os.path.join(d, "emoji.md")
            draft_ok = os.path.join(d, "ok.md")
            write_utf8(orig, "明日の15時に集合です。\n")
            write_utf8(draft_ssu, "明日の15時に集合っす。\n")
            write_utf8(draft_w, "明日の15時に集合ですw\n")
            write_utf8(draft_emoji, "明日の15時に集合です🚀\n")
            write_utf8(draft_ok, "明日の15時に集合します。\n")

            self.assertEqual(run_cli(["diff", orig, draft_ssu, "--scene", "formal"]).returncode, 1)
            self.assertEqual(run_cli(["diff", orig, draft_w, "--scene", "formal"]).returncode, 1)
            self.assertEqual(run_cli(["diff", orig, draft_emoji, "--scene", "formal"]).returncode, 1)
            self.assertEqual(run_cli(["diff", orig, draft_ok, "--scene", "formal"]).returncode, 0)

    def test_git_hook_blocks_profile_and_formal_leak(self) -> None:
        with tempfile.TemporaryDirectory() as repo:
            prof = os.path.join(repo, "profile.md")
            write_utf8(prof, self.SAMPLE_PROFILE)
            run_git(["init"], cwd=repo)
            run_git(["config", "user.name", "Test"], cwd=repo)
            run_git(["config", "user.email", "test@example.com"], cwd=repo)
            doc = os.path.join(repo, "notice.md")
            write_utf8(doc, "明日の15時に開始します。\n")
            run_git(["add", "notice.md"], cwd=repo)
            run_git(["commit", "-m", "init"], cwd=repo)

            write_utf8(doc, "明日の15時に開始させていただきます🚀\n")
            res = run_cli(["git", "--profile", prof, "--scene", "formal", "--hook"], cwd=repo, stdin_text="")
            self.assertEqual(res.returncode, 2)
            self.assertIn("させていただきます", res.stderr)
            self.assertIn("絵文字", res.stderr)

    def test_missing_profile_behavior(self) -> None:
        with tempfile.TemporaryDirectory() as repo:
            missing = os.path.join(repo, "no_such_profile.md")
            orig = os.path.join(repo, "orig.md")
            draft = os.path.join(repo, "draft.md")
            write_utf8(orig, "明日の15時です。\n")
            write_utf8(draft, "明日の15時です。\n")

            # 通常 diff では存在しない profile 指定で exit 2
            res_diff = run_cli(["diff", orig, draft, "--profile", missing])
            self.assertEqual(res_diff.returncode, 2)

            # --hook では未作成の profile を安全にスキップして落ちない
            run_git(["init"], cwd=repo)
            run_git(["config", "user.name", "Test"], cwd=repo)
            run_git(["config", "user.email", "test@example.com"], cwd=repo)
            run_git(["add", "orig.md"], cwd=repo)
            run_git(["commit", "-m", "init"], cwd=repo)
            res_hook = run_cli(["git", "--profile", missing, "--hook"], cwd=repo, stdin_text="")
            self.assertEqual(res_hook.returncode, 0, res_hook.stdout + res_hook.stderr)


class PackagingAndExamplesTests(unittest.TestCase):
    def test_claude_code_hook_json_is_valid(self) -> None:
        hook_path = os.path.join(REPO_ROOT, "examples", "hooks", "claude-code-hook.json")
        data = json.loads(read_utf8(hook_path))
        self.assertIn("hooks", data)
        self.assertIn("PostToolUse", data["hooks"])

    def test_pyproject_metadata(self) -> None:
        pyproject_path = os.path.join(REPO_ROOT, "pyproject.toml")
        content = read_utf8(pyproject_path)
        self.assertIn('version = "3.1.0"', content)
        self.assertIn('requires-python = ">=3.10"', content)
        self.assertIn('nihongo-check = "nihongo_check.cli:main"', content)
        self.assertIn('packages = ["nihongo_check"]', content)


if __name__ == "__main__":
    unittest.main()
