#!/usr/bin/env python3
"""agents open — print Railway dashboard base URL; on macOS optionally open in browser."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

import agents_cli_config as acfg


def main() -> int:
    parser = argparse.ArgumentParser(description="Print or open Railway dashboard URL.")
    parser.add_argument(
        "--browser",
        action="store_true",
        help="Open in default browser (macOS: open(1))",
    )
    args = parser.parse_args()

    cwd = Path.cwd()
    cfg_path = acfg.config_path(cwd)
    if not cfg_path.is_file():
        print(f"error: {cfg_path} not found", file=sys.stderr)
        return 1

    cfg = acfg.load_config_file(cwd=cwd)
    api_url = acfg.resolve_api_url(cfg, cwd=cwd)
    print(api_url)

    if args.browser:
        try:
            subprocess.run(["open", api_url], check=False)
        except FileNotFoundError:
            print("note: `open` not found; print URL only", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
