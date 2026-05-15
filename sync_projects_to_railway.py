#!/usr/bin/env python3
"""
One-shot: sync local SQLite projects → Railway database via API.
Run once: python sync_projects_to_railway.py
"""
import os
import sys
import json
from pathlib import Path
import urllib.request
import urllib.error

RAILWAY_URL = "https://pod-production-63e3.up.railway.app"

# Load AGENTS_API_KEY from agent-services/.env
def load_api_key() -> str:
    env_file = Path(__file__).parent / "agent-services" / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line.startswith("AGENTS_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    key = os.environ.get("AGENTS_API_KEY", "")
    if key:
        return key
    sys.exit("ERROR: AGENTS_API_KEY not found in agent-services/.env or environment.")

PROJECTS = [
    {"name": "Global Claude",          "slug": "claude-global"},
    {"name": "DMRB Production",        "slug": "dmrb"},
    {"name": "Quick Agent Job",        "slug": "quick-agent-job"},
    {"name": "Agent System Base",      "slug": "agent-system-base"},
    {"name": "DMRB Legacy (Streamlit)","slug": "dmrb-legacy"},
]

def post(url: str, payload: dict, headers: dict) -> dict:
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())

def get(url: str, headers: dict) -> list:
    req = urllib.request.Request(url, headers=headers, method="GET")
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())

def main():
    key = load_api_key()
    headers = {"X-API-Key": key, "Content-Type": "application/json"}

    print(f"Target: {RAILWAY_URL}")
    print(f"API key: {'set (' + key[:4] + '…)' if key else 'MISSING'}\n")

    # Check existing projects on Railway
    try:
        existing = get(f"{RAILWAY_URL}/api/projects", headers)
    except urllib.error.HTTPError as e:
        sys.exit(f"GET /api/projects failed: {e.code} {e.reason}")

    existing_slugs = {p["slug"] for p in existing}
    print(f"Railway already has {len(existing)} project(s): {existing_slugs or 'none'}\n")

    created, skipped, failed = [], [], []

    for p in PROJECTS:
        if p["slug"] in existing_slugs:
            print(f"  SKIP  {p['name']} ({p['slug']}) — already exists")
            skipped.append(p["slug"])
            continue
        try:
            result = post(
                f"{RAILWAY_URL}/api/projects",
                {"name": p["name"], "slug": p["slug"]},
                headers,
            )
            print(f"  OK    {p['name']} ({p['slug']}) → id={result.get('id')}")
            created.append(p["slug"])
        except urllib.error.HTTPError as e:
            body = e.read().decode()
            print(f"  FAIL  {p['name']} ({p['slug']}) → {e.code}: {body}")
            failed.append(p["slug"])

    print(f"\nDone. created={len(created)} skipped={len(skipped)} failed={len(failed)}")
    if failed:
        sys.exit(1)

if __name__ == "__main__":
    main()
