"""Tests for decision_service (append-only)."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
import unittest.mock
from contextlib import contextmanager
from pathlib import Path

_SERVICES_DIR = Path(__file__).resolve().parent
if str(_SERVICES_DIR) not in sys.path:
    sys.path.insert(0, str(_SERVICES_DIR))

import db as db_mod  # noqa: E402
import decision_service  # noqa: E402

_real_connect = db_mod.connect


class TestDecisionService(unittest.TestCase):
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

        self._patcher = unittest.mock.patch.object(decision_service.db, "connect", _patched_connect)
        self._patcher.start()

    def tearDown(self) -> None:
        self._patcher.stop()

    def test_add_list_multiple_rows(self) -> None:
        a = decision_service.add_decision("First", "Body one")
        b = decision_service.add_decision("Second", "Body two")
        self.assertNotEqual(a["id"], b["id"])
        rows = decision_service.list_decisions()
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["title"], "First")
        self.assertEqual(rows[1]["title"], "Second")
        self.assertEqual(rows[0]["content"], "Body one")

    def test_empty_title_raises(self) -> None:
        with self.assertRaises(ValueError):
            decision_service.add_decision("  ", "x")

    def test_empty_content_raises(self) -> None:
        with self.assertRaises(ValueError):
            decision_service.add_decision("t", "   ")


if __name__ == "__main__":
    unittest.main()
