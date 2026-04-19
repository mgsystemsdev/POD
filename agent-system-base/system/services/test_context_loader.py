"""Tests for context_loader."""

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

import context_loader  # noqa: E402
import db as db_mod  # noqa: E402
import project_service  # noqa: E402

_real_connect = db_mod.connect


class TestContextLoader(unittest.TestCase):
    def setUp(self) -> None:
        fd, self._db_path = tempfile.mkstemp(suffix=".sqlite")
        os.close(fd)
        self.addCleanup(lambda: os.path.exists(self._db_path) and os.unlink(self._db_path))

        @contextmanager
        def _patched_db(*, database: str | None = None, uri: bool = False):
            if database is None:
                with _real_connect(database=self._db_path) as conn:
                    yield conn
            else:
                with _real_connect(database=database, uri=uri) as conn:
                    yield conn

        self._patcher = unittest.mock.patch.object(project_service.db, "connect", _patched_db)
        self._patcher.start()

    def tearDown(self) -> None:
        self._patcher.stop()

    def test_load_by_slug_with_root(self) -> None:
        slug = f"ctx_{uuid.uuid4().hex[:10]}"
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: tmp.exists() and os.rmdir(tmp))
        project_service.create_project("Ctx", slug, root_path=str(tmp))
        out = context_loader.load_project_context(slug=slug)
        self.assertEqual(out["project"]["slug"], slug)
        self.assertEqual(out["root"], tmp.resolve())
        self.assertTrue(out["root_exists"])

    def test_missing_project(self) -> None:
        with self.assertRaises(LookupError):
            context_loader.load_project_context(slug="does_not_exist_zzzz")

    def test_both_or_neither_id_slug(self) -> None:
        with self.assertRaises(ValueError):
            context_loader.load_project_context()
        with self.assertRaises(ValueError):
            context_loader.load_project_context(project_id=1, slug="x")


if __name__ == "__main__":
    unittest.main()
