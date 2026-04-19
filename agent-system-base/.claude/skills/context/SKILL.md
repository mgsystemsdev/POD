---
name: context
version: "1.0.0"
description: >
  Fetch up-to-date, version-specific documentation for any library or framework directly into
  your conversation. Use when working with unfamiliar APIs, checking current syntax, verifying
  deprecated methods, or before writing code that depends on a specific library version.
  Trigger when: "check the docs for", "how does X work?", "what's the current API for",
  "context7", or when you detect code using a library you're not confident about.
allowed-tools: Read, Grep, Glob, Bash, WebFetch, WebSearch
---

# Context: Live Documentation Lookup

Pull current, version-specific documentation for any library or framework. No stale training data. No guessing.
Real docs, right now.

## When to Use
- Before writing code that depends on a library's API
- When a user asks about current syntax or methods for a package
- When you're unsure if a method is deprecated or renamed
- When you need code examples from official docs
- When version-specific behavior matters

## Process
1. Identify the library/framework and version (ask if not specified)
2. Search for the official documentation
3. Fetch the relevant page(s)
4. Extract the specific API, method, or pattern needed
5. Present it with version context and a direct link

## Rules
- Always prefer official docs over blog posts or tutorials
- State the version you're referencing
- If docs conflict with training data, trust the docs
- Flag if a method/API appears to have changed recently

## Failure Modes

**No official docs found online** — For private, intranet, or obscure packages, fall back
to the local codebase: source files, type stubs, inline docstrings, README. Say where you
found the information so Miguel knows the confidence level.

**Web tools unavailable** — Search the codebase and local files only. State clearly:
"Web access isn't available — this is based on local files only." Don't pretend to fetch
docs that weren't actually retrieved.

**Version unknown** — Ask before guessing. API signatures change between versions;
wrong-version docs are worse than no docs. One question: "What version are you on?"

**Docs found but version doesn't match codebase** — Flag the mismatch explicitly:
"The docs I found are for v[X] but your code appears to use v[Y]. Behavior may differ."
Don't silently use the wrong version's docs.
