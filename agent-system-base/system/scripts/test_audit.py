"""Subprocess tests for audit.py (isolated roots via AUDIT_NO_DEFAULT_ROOT)."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_AUDIT = _REPO / "system" / "scripts" / "audit.py"


class TestAuditScript(unittest.TestCase):
    def test_planted_tasks_json_fails(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "tasks.json").write_text("[]", encoding="utf-8")
            env = {**os.environ, "AUDIT_NO_DEFAULT_ROOT": "1"}
            r = subprocess.run(
                [sys.executable, str(_AUDIT), "--roots", str(root)],
                cwd=str(_REPO),
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(r.returncode, 1, msg=r.stdout + r.stderr)
            self.assertIn("AUDIT: FAIL", r.stdout)
            self.assertIn("tasks.json", r.stdout)

    def test_allowlist_tasks_json_clean(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "tasks.json").write_text("[]", encoding="utf-8")
            env = {**os.environ, "AUDIT_NO_DEFAULT_ROOT": "1"}
            r = subprocess.run(
                [sys.executable, str(_AUDIT), "--roots", str(root), "--allowlist", "tasks.json"],
                cwd=str(_REPO),
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(r.returncode, 0, msg=r.stdout + r.stderr)
            self.assertIn("AUDIT: OK", r.stdout)


if __name__ == "__main__":
    unittest.main()
