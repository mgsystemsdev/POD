---
name: frontend-design
version: "1.0.0"
description: >
  Create distinctive, production-grade frontend
  interfaces with high design quality. Commit to
  a bold aesthetic before writing a single line.
  Use when building any UI — React, Streamlit,
  HTML. Trigger when user says "build a page",
  "create a component", "design a UI", "build
  a dashboard", or when any frontend work begins.
user-invocable: true
allowed-tools: Read, Write, Edit, Grep, Glob, Bash
---

# Frontend Design Skill

Before coding, commit to a bold aesthetic.
Zero generic components. All distinctive.

## Step 1 — Pick a style direction
Choose ONE before writing any code:
- Brutally minimal
- Maximalist chaos
- Retro-futuristic
- Organic / natural
- Luxury / refined
- Playful / toy-like
- Editorial / magazine
- Art deco / geometric

## Step 2 — Typography rules
- Choose fonts that are beautiful + unique
- NEVER use Arial, Inter, or generic fonts
- Match font weight to aesthetic vision
- Use Google Fonts for distinctive choices
- Pair a display font with a mono or serif

## Step 3 — Color philosophy
- 1 primary + 1 accent + neutrals only
- Dark mode: depth through gradients
- Light mode: contrast through spacing
- Avoid rainbow — constrain your palette
- Every color must earn its place

## Step 4 — Animation intent
- Every animation must have a purpose
- Micro-interactions on hover/focus
- Page transitions: subtle, fast (200-300ms)
- Loading states: skeleton, never spinner
- Motion should guide attention, not distract

## Step 5 — Component rules
- No generic cards — make them distinctive
- Spacing is a design decision, not a default
- Every interactive element has 3 states:
  default, hover, active
- Mobile-first, always
- Contrast ratio >= 4.5:1 (WCAG AA)
- Touch targets >= 44px minimum

## Project-specific notes

STREAMLIT (DMRB):
- Use st.markdown with custom CSS injection
- Custom color tokens via CSS variables
- Consistent spacing scale (4px base)

REACT (dmrb-web / zelda):
- Tailwind for utility, custom CSS for identity
- shadcn/ui as base, always customize
- Never ship default shadcn styling

## Failure Modes

**User wants "something clean"** — Don't default to generic. Ask one question:
"What's the primary emotion this UI should evoke?" Then commit to a direction.

**Aesthetic conflicts with framework constraints** — Surface it immediately:
"Streamlit limits X — here's how I'll work around it." Never silently downgrade.

**Too many design decisions at once** — Pick the style direction first, lock it in,
then derive everything else from it. Don't freestyle each component independently.

## Output
Produce the UI with the chosen aesthetic applied.
State the style direction chosen at the top.
Every component reflects the aesthetic decision.
Zero defaults. All intentional.
