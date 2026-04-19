"""Tests for claude_execution (mocked Anthropic client)."""

from __future__ import annotations

import os
import sys
import unittest
import unittest.mock
from pathlib import Path

_SERVICES_DIR = Path(__file__).resolve().parent
if str(_SERVICES_DIR) not in sys.path:
    sys.path.insert(0, str(_SERVICES_DIR))

import claude_execution  # noqa: E402


class TestRunMessages(unittest.TestCase):
    def test_missing_key_raises(self) -> None:
        with unittest.mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(RuntimeError) as ctx:
                claude_execution.run_messages("s", "u")
        self.assertIn("ANTHROPIC_API_KEY", str(ctx.exception))

    @unittest.mock.patch("anthropic.Anthropic")
    def test_returns_text(self, mock_anthropic: unittest.mock.MagicMock) -> None:
        block = unittest.mock.MagicMock()
        block.type = "text"
        block.text = "hello"
        mock_anthropic.return_value.messages.create.return_value = unittest.mock.MagicMock(content=[block])
        with unittest.mock.patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
            out = claude_execution.run_messages("sys", "user", timeout_s=5.0)
        self.assertEqual(out, "hello")


class TestRetry(unittest.TestCase):
    @unittest.mock.patch("claude_execution.time.sleep", unittest.mock.MagicMock())
    @unittest.mock.patch("claude_execution.run_messages")
    def test_retries_then_succeeds(self, mock_run: unittest.mock.MagicMock) -> None:
        class Boom(Exception):
            pass

        mock_run.side_effect = [Boom(), Boom(), "ok"]

        def fake_retry(exc: BaseException) -> bool:
            return isinstance(exc, Boom)

        with unittest.mock.patch.dict(os.environ, {"ANTHROPIC_API_KEY": "k"}):
            with unittest.mock.patch.object(claude_execution, "_retryable", fake_retry):
                out = claude_execution.run_messages_with_retry("s", "u", max_retries=3)
        self.assertEqual(out, "ok")
        self.assertEqual(mock_run.call_count, 3)


if __name__ == "__main__":
    unittest.main()
