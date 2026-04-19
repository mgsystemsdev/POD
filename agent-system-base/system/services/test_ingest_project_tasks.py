"""Tests for ingest_project_tasks loader, parser, and ingest_parsed_tasks."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
import unittest.mock
import uuid
from contextlib import contextmanager
from pathlib import Path

_SERVICES_DIR = Path(__file__).resolve().parent
if str(_SERVICES_DIR) not in sys.path:
    sys.path.insert(0, str(_SERVICES_DIR))

import db as db_mod  # noqa: E402
import ingest_project_tasks as ipt  # noqa: E402
import task_service  # noqa: E402

_real_connect = db_mod.connect


class TestReadProjectMarkdownFiles(unittest.TestCase):
    def test_reads_present_files_and_notes_missing(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            (tmp / "AGENTS.md").write_text("a\n", encoding="utf-8")
            (tmp / "TASKS.md").write_text("x", encoding="utf-8")
            contents, issues = ipt.read_project_markdown_files(tmp)
            self.assertEqual(set(contents.keys()), {"AGENTS.md", "TASKS.md"})
            self.assertIn("missing: WORKFLOW.md", issues)
            self.assertEqual(contents["AGENTS.md"], "a\n")
            chars = sum(len(s) for s in contents.values())
            self.assertEqual(chars, 3)  # "a\n" + "x"


class TestParseTasks(unittest.TestCase):
    def test_idempotent_and_order(self) -> None:
        fm = {
            "TASKS.md": "- bullet one\n* bullet two\n",
            "AGENTS.md": "## Heading A\n\nFirst para.\n\n### Heading B\n\nSecond para.\n",
        }
        a = ipt.parse_tasks(fm)
        b = ipt.parse_tasks(fm)
        self.assertEqual(a, b)
        self.assertEqual(len(a), 4)
        # Sorted filenames: AGENTS.md (2 headings) then TASKS.md (2 bullets)
        self.assertEqual(a[0]["title"], "Heading A")
        self.assertEqual(a[0]["description"], "First para.")
        self.assertEqual(a[1]["title"], "Heading B")
        self.assertEqual(a[1]["description"], "Second para.")
        self.assertEqual(a[2]["title"], "bullet one")
        self.assertIsNone(a[2]["description"])
        self.assertEqual(a[3]["title"], "bullet two")
        self.assertEqual(a[0]["created_at"], "2026-01-01T00:00:00Z")
        self.assertEqual(a[3]["created_at"], "2026-01-01T00:00:03Z")
        for row in a:
            self.assertEqual(row["priority"], "normal")
            self.assertEqual(row["type"], "feature")
            self.assertEqual(row["created_at"], row["updated_at"])


class TestIngestParsedTasks(unittest.TestCase):
    def setUp(self) -> None:
        fd, self._db_path = tempfile.mkstemp(suffix=".sqlite")
        os.close(fd)
        self.addCleanup(lambda: os.path.exists(self._db_path) and os.unlink(self._db_path))

        @contextmanager
        def _patched_connect(*, database: str | None = None, uri: bool = False):
            if database is None:
                with _real_connect(database=self._db_path) as conn:
                    yield conn
            else:
                with _real_connect(database=database, uri=uri) as conn:
                    yield conn

        self._patcher = unittest.mock.patch.object(task_service.db, "connect", _patched_connect)
        self._patcher.start()
        self.addCleanup(self._patcher.stop)

        self._project_id = self._insert_project()

    def _insert_project(self) -> int:
        now = "2026-01-01T00:00:00Z"
        slug = f"ing_{uuid.uuid4().hex[:12]}"
        with _real_connect(database=self._db_path) as conn:
            cur = conn.execute(
                "INSERT INTO projects (name, slug, root_path, created_at, updated_at) VALUES (?,?,?,?,?)",
                ("Ingest Test", slug, None, now, now),
            )
            conn.commit()
            return int(cur.lastrowid)

    def _sample_candidates(self) -> list[dict]:
        return [
            {
                "title": "From Markdown",
                "description": None,
                "priority": "normal",
                "type": "feature",
                "created_at": "2026-01-01T00:00:10Z",
                "updated_at": "2026-01-01T00:00:10Z",
            }
        ]

    def test_preview_no_db_inserts(self) -> None:
        r = ipt.ingest_parsed_tasks(self._project_id, self._sample_candidates(), apply=False)
        self.assertEqual(r.would_insert, 1)
        self.assertEqual(r.inserted, 0)
        self.assertEqual(r.skipped, 0)
        self.assertEqual(len(task_service.list_tasks(project_id=self._project_id)), 0)

    def test_apply_twice_idempotent(self) -> None:
        c = self._sample_candidates()
        r1 = ipt.ingest_parsed_tasks(self._project_id, c, apply=True)
        self.assertEqual(r1.would_insert, 0)
        self.assertEqual(r1.inserted, 1)
        self.assertEqual(r1.skipped, 0)
        r2 = ipt.ingest_parsed_tasks(self._project_id, c, apply=True)
        self.assertEqual(r2.inserted, 0)
        self.assertEqual(r2.skipped, 1)
        rows = task_service.list_tasks(project_id=self._project_id)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["source"], "project_import")


if __name__ == "__main__":
    unittest.main()
