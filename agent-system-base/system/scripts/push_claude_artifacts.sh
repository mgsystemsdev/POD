#!/usr/bin/env bash
# One-launcher for push_claude_artifacts.py (same directory as this script).
exec python3 "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/push_claude_artifacts.py" "$@"
