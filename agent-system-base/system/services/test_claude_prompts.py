"""Tests for claude_prompts."""

from __future__ import annotations

import sys
from pathlib import Path

_SERVICES_DIR = Path(__file__).resolve().parent
if str(_SERVICES_DIR) not in sys.path:
    sys.path.insert(0, str(_SERVICES_DIR))

import unittest

import claude_prompts  # noqa: E402


class TestBuildPrompts(unittest.TestCase):
    def test_deterministic_sections(self) -> None:
        task = {
            "id": 42,
            "title": "Do the thing",
            "description": "Details here",
            "type": "chore",
            "priority": "normal",
            "source": "manual",
            "status": "in_progress",
        }
        ctx = {
            "project": {"name": "Proj", "slug": "proj", "root_path": "/tmp/x"},
            "root_exists": True,
        }
        system, user = claude_prompts.build_prompts(task, ctx)
        self.assertIn("Proj", system)
        self.assertIn("proj", system)
        self.assertIn("Do the thing", user)
        self.assertIn("Details here", user)


if __name__ == "__main__":
    unittest.main()
