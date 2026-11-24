"""Bonus PR テスト: `nihongo-check doctor`, `profile init [--project]`, `diff/git --auto-profile`。"""
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


def run_cli(args: list[str], cwd: str | None = None) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    return subprocess.run(
        [sys.executable, CLI, *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
        check=False,
    )


class DoctorAndProjectInitTests(unittest.TestCase):
    def test_profile_init_global_and_project_never_clobbers_existing(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            home = os.path.join(d, "home")
            proj = os.path.join(d, "my_research")
            os.makedirs(proj, exist_ok=True)

            r1 = run_cli(["profile", "init", "--home", home, "--json"])
            self.assertEqual(r1.returncode, 0, r1.stderr)
            d1 = json.loads(r1.stdout)
            self.assertTrue(d1["created"])
            self.assertTrue(os.path.isfile(os.path.join(home, "profile.md")))

            # Put custom text into profile.md and verify re-running init does NOT overwrite
            with open(os.path.join(home, "profile.md"), "a", encoding="utf-8") as f:
                f.write("\n- カスタム保護テスト\n")
            r2 = run_cli(["profile", "init", "--home", home, "--json"])
            self.assertEqual(r2.returncode, 0, r2.stderr)
            self.assertFalse(json.loads(r2.stdout)["created"])
            self.assertIn("カスタム保護テスト", open(os.path.join(home, "profile.md"), encoding="utf-8").read())

            # Create project overlay .nihongo/profile.md
            r3 = run_cli(["profile", "init", "--project", proj, "--json"])
            self.assertEqual(r3.returncode, 0, r3.stderr)
            d3 = json.loads(r3.stdout)
            self.assertTrue(d3["created"])
            self.assertEqual(d3["layer"], "project")
            self.assertTrue(os.path.isfile(os.path.join(proj, ".nihongo", "profile.md")))

    def test_diff_auto_profile_applies_both_global_and_project_layers(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            home = os.path.join(d, "home")
            proj = os.path.join(d, "client_a")
            os.makedirs(home, exist_ok=True)
            os.makedirs(os.path.join(proj, ".nihongo"), exist_ok=True)

            with open(os.path.join(home, "profile.md"), "w", encoding="utf-8") as f:
                f.write("# 私の書き方\n\n## [common]\n- 絶対に言わない表現：「いただけますと幸いです」\n")
            with open(os.path.join(proj, ".nihongo", "profile.md"), "w", encoding="utf-8") as f:
                f.write("# 案件A\n\n## [common]\n- 絶対に言わない表現：「ご査収のほど」\n")

            orig = os.path.join(proj, "orig.md")
            draft = os.path.join(proj, "draft.md")
            with open(orig, "w", encoding="utf-8") as f:
                f.write("資料を送ります。\n")
            with open(draft, "w", encoding="utf-8") as f:
                f.write("資料をご査収のほど、ご確認いただけますと幸いです。\n")

            res = run_cli(["diff", orig, draft, "--auto-profile", "--home", home, "--json"])
            self.assertEqual(res.returncode, 1)
            payload = json.loads(res.stdout)
            joined = "\n".join(payload["findings"])
            self.assertIn("ご査収のほど", joined)
            self.assertIn("いただけますと幸いです", joined)

    def test_doctor_reports_layers_inbox_and_mcp_clients(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            home = os.path.join(d, "home")
            proj = os.path.join(d, "proj")
            os.makedirs(home, exist_ok=True)
            os.makedirs(os.path.join(proj, ".nihongo"), exist_ok=True)
            with open(os.path.join(home, "profile.md"), "w", encoding="utf-8") as f:
                f.write("## [common]\n- 絶対に言わない表現：「恐れ入りますが」\n")
            with open(os.path.join(proj, ".nihongo", "profile.md"), "w", encoding="utf-8") as f:
                f.write("## [common]\n- 絶対に言わない表現：「何卒」\n")

            res = run_cli(["doctor", "--home", home, "--project", proj, "--json"])
            self.assertEqual(res.returncode, 0, res.stderr)
            report = json.loads(res.stdout)
            self.assertTrue(report["global_profile_exists"])
            self.assertEqual(len(report["active_layers"]), 2)
            self.assertEqual(report["forbidden_count"], 2)
            self.assertEqual(len(report["mcp_clients"]), 4)

            # Plain text human output works cleanly too
            res_txt = run_cli(["doctor", "--home", home, "--project", proj])
            self.assertEqual(res_txt.returncode, 0, res_txt.stderr)
            self.assertIn("nihongo-check doctor", res_txt.stdout)
            self.assertIn("2層適用中", res_txt.stdout)


if __name__ == "__main__":
    unittest.main()
