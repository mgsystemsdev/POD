#!/usr/bin/env python3
"""
Entry point next to task_worker.py — same working directory convention:

  cd ~/agents/agent-services && python3 workers/push_claude_artifacts.py
"""

from __future__ import annotations

import runpy
from pathlib import Path

_SCRIPT = Path(__file__).resolve().parent.parent / "system" / "scripts" / "push_claude_artifacts.py"

if __name__ == "__main__":
    runpy.run_path(str(_SCRIPT), run_name="__main__")
