"""Tests for project_service (registry)."""

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
import project_service  # noqa: E402

_real_connect = db_mod.connect


class TestProjectService(unittest.TestCase):
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

        self._patcher = unittest.mock.patch.object(project_service.db, "connect", _patched_connect)
        self._patcher.start()

    def tearDown(self) -> None:
        self._patcher.stop()

    def test_create_list_get_by_slug(self) -> None:
        slug = f"proj_{uuid.uuid4().hex[:10]}"
        p = project_service.create_project("My Project", slug)
        self.assertEqual(p["name"], "My Project")
        self.assertEqual(p["slug"], slug)
        self.assertIsNone(p.get("root_path"))

        listed = project_service.list_projects()
        self.assertTrue(any(x["id"] == p["id"] for x in listed))

        by_id = project_service.get_project(p["id"])
        assert by_id is not None
        self.assertEqual(by_id["slug"], slug)

        by_slug = project_service.get_project_by_slug(slug)
        assert by_slug is not None
        self.assertEqual(by_slug["id"], p["id"])

    def test_set_project_root(self) -> None:
        slug = f"r_{uuid.uuid4().hex[:10]}"
        p = project_service.create_project("R", slug)
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: tmp.exists() and os.rmdir(tmp))
        updated = project_service.set_project_root(p["id"], str(tmp))
        assert updated is not None
        self.assertEqual(updated["root_path"], str(tmp))

    def test_invalid_slug(self) -> None:
        with self.assertRaises(ValueError):
            project_service.create_project("X", "Bad Slug")

    def test_upsert_same_slug_updates(self) -> None:
        slug = f"up_{uuid.uuid4().hex[:10]}"
        a, created = project_service.upsert_project("One", slug, root_path="/tmp/a")
        self.assertTrue(created)
        self.assertEqual(a["name"], "One")
        self.assertEqual(a["root_path"], "/tmp/a")
        b, created2 = project_service.upsert_project("Two", slug, root_path="/tmp/b")
        self.assertFalse(created2)
        self.assertEqual(b["id"], a["id"])
        self.assertEqual(b["name"], "Two")
        self.assertEqual(b["root_path"], "/tmp/b")


if __name__ == "__main__":
    unittest.main()
