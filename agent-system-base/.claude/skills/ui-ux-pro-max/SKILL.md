---
name: ui-ux-pro-max
version: "1.0.0"
description: >
  Design intelligence for any product. Generates
  full design system: style, palette, typography,
  tokens, UX rules. Use when starting a new UI,
  building a design system, or when frontend-design
  needs a complete token set. Trigger: "design
  system", "what style should I use", "generate
  tokens", "design this product", "UI for [product]"
user-invocable: true
allowed-tools: Read, Write, Edit, Grep, Glob
---

# UI/UX Pro Max

Full design intelligence. Describe your product
and audience — this skill selects and generates
everything.

## Phase 1 — Product Analysis
Before any design decision:
- What is this product? What does it do?
- Who uses it? (operators, admins, tenants,
  developers, general public?)
- What is the primary emotion it should evoke?
  (trust, efficiency, delight, power, calm)
- What industry? (property mgmt, gaming,
  productivity, health, finance, consumer)

## Phase 2 — Style Selection
Match product + audience to style category:
- Enterprise / ops tools → clean, efficient,
  data-dense, neutral palette
- Consumer apps → expressive, brand-forward,
  emotional color
- Developer tools → monospace, dark, precise
- Creative tools → expressive, experimental
- Property management (DMRB) → professional,
  trust-forward, data-first

## Phase 3 — Design Token Generation
Output a complete token set:

COLORS:
- Primary: [hex] — main brand action color
- Accent: [hex] — secondary emphasis
- Success: [hex]
- Warning: [hex]
- Danger: [hex]
- Background: [hex]
- Surface: [hex]
- Border: [hex]
- Text primary: [hex]
- Text muted: [hex]

TYPOGRAPHY:
- Display font: [name] — headings, hero
- Body font: [name] — paragraphs, labels
- Mono font: [name] — code, data, IDs
- Scale: 12/14/16/20/24/32/48px

SPACING: 4px base scale
  xs:4 sm:8 md:16 lg:24 xl:32 2xl:48

RADIUS: none/sm(4px)/md(8px)/lg(16px)/full

## Phase 4 — UX Rules (applied to this product)
Select the 10 most relevant from:
- Progressive disclosure for complex forms
- Inline validation, never on submit
- Empty states must suggest next action
- Destructive actions require confirmation
- Loading states on every async operation
- Error messages must explain AND suggest fix
- Navigation shows current location always
- Search before filter for large datasets
- Bulk actions for list views > 10 items
- Keyboard shortcuts for power users

## Phase 5 — Component Checklist
For every component produced, verify:
□ Contrast ratio >= 4.5:1
□ Touch targets >= 44px
□ Focus state visible
□ Loading state defined
□ Empty state defined
□ Error state defined
□ Mobile layout defined

## Failure Modes

**Product description is vague** — Ask: "Who is the primary user and what is the
one thing they need to accomplish?" Don't generate tokens for an undefined product.

**Token conflicts with existing codebase** — Read existing CSS/Tailwind config first.
Surface conflicts before generating; don't overwrite a live design system blindly.

**User wants tokens but no product context** — Refuse to generate generic tokens.
Every token decision must be anchored to a real product decision.

## Output
1. Design brief (2 sentences)
2. Complete token set
3. Typography pairing with rationale
4. Top 10 UX rules for this product
5. Component checklist
6. Apply everything to the requested UI
