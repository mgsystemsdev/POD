# Tech Stack Guide — Blueprint Creator
# How to recommend technology for any project type

---

## How to use this file

When producing Document 2 (Tech Stack), use this guide to determine the right recommendation based on what the user is building. Follow the decision tree for the project type. Give the primary recommendation with rationale. Offer exactly two alternatives with plain English comparison.

Never recommend a stack you cannot explain in plain English. If you cannot explain why a choice is right for this user, it is not the right recommendation.

---

## Decision tree — match project type to stack

### Type 1: Web application (most common)
**User builds:** a website that users log in to and interact with

**Primary recommendation:**
- Backend: Python + FastAPI
- Frontend: React + TypeScript
- Database: PostgreSQL
- Hosting: Render or Railway (simple), AWS (at scale)
- Auth: JWT tokens or a managed service (Auth0, Supabase Auth)

**Plain English rationale:** Python is readable and widely used. FastAPI produces a backend that is fast to build and self-documents itself — it generates a page where you can see all the API connections. React is the most common choice for building web interfaces and has the largest community for help. PostgreSQL handles almost any data need. Render and Railway deploy without complex server management.

**Alternative A:** Node.js + Express + React + PostgreSQL
- Similar result, uses JavaScript on both sides (backend and frontend). Fewer languages to learn. Larger ecosystem of existing tools.

**Alternative B:** Django + React + PostgreSQL
- Django includes more features built-in (admin panel, authentication, forms). Faster for standard patterns. Less flexible for custom API designs.

---

### Type 2: API-only service (backend that other systems consume)
**User builds:** a service that has no user interface — other apps or systems connect to it

**Primary recommendation:**
- Backend: Python + FastAPI
- Database: PostgreSQL
- Hosting: Railway or Fly.io
- Auth: JWT or API keys

**Plain English rationale:** FastAPI is purpose-built for this. It is fast, generates documentation automatically, and handles high volume well. No frontend framework needed.

**Alternative A:** Node.js + Express
- JavaScript. Good performance. Massive ecosystem.

**Alternative B:** Go + standard library
- Very fast. Minimal memory use. Good for high-performance services. Harder to learn.

---

### Type 3: Data dashboard or internal tool
**User builds:** a tool their team uses to view, analyze, or manage data

**Primary recommendation:**
- Python + Streamlit
- Database: PostgreSQL or SQLite (for small scale)
- Hosting: Streamlit Cloud or Railway

**Plain English rationale:** Streamlit turns Python scripts into interactive web apps with very little code. No frontend experience required. Good for data visualization, admin tools, and internal dashboards. Can be running in hours.

**Alternative A:** Python + FastAPI + React dashboard
- More work to set up, more flexible, better for complex interactions.

**Alternative B:** Retool or Metabase (no-code/low-code)
- For non-developers who need dashboards. No coding required but limited customization.

---

### Type 4: Mobile application
**User builds:** an app that runs on phones (iOS and Android)

**Primary recommendation:**
- React Native + TypeScript
- Backend: Python + FastAPI (separate service)
- Database: PostgreSQL
- Hosting: Expo for distribution, Railway for backend

**Plain English rationale:** React Native lets you write one codebase that runs on both iPhone and Android. TypeScript catches errors before they reach users. FastAPI handles the backend that the app connects to.

**Alternative A:** Flutter (Google's framework)
- Also cross-platform. Uses Dart language (less commonly known). Strong for visual-heavy apps.

**Alternative B:** Native development (Swift for iOS, Kotlin for Android)
- Best performance and access to device features. Requires two separate codebases. Higher cost.

---

### Type 5: Static website or content site
**User builds:** a website with content that does not change based on who is viewing it (portfolio, landing page, documentation, blog)

**Primary recommendation:**
- Next.js + TypeScript
- Hosting: Vercel (simplest) or Netlify

**Plain English rationale:** Next.js builds fast websites that search engines can read well. Vercel deploys them with essentially no configuration. Best for content-focused sites.

**Alternative A:** Astro
- Even faster for pure content sites. Minimal JavaScript by default.

**Alternative B:** WordPress (for non-developers)
- No coding required. Large ecosystem of themes and plugins. Less control over performance and customization.

---

### Type 6: Automation or batch processing
**User builds:** a system that runs automatically — processes files, sends emails, syncs data, runs reports on a schedule

**Primary recommendation:**
- Python scripts + cron or a task queue (Celery + Redis)
- Database: PostgreSQL
- Hosting: Railway or a simple VPS

**Plain English rationale:** Python is the standard choice for automation. Cron runs tasks on a schedule. Celery handles tasks that need to run in the background without blocking other work.

**Alternative A:** Node.js + Bull queue
- JavaScript-based. Large ecosystem for integrations.

**Alternative B:** Airflow (for complex data pipelines)
- Built for orchestrating many interdependent tasks. More setup overhead. Worth it for complex workflows.

---

## Questions to determine project type

If the project type is unclear, ask the one question that determines it:

"What is the main thing a user does with this — do they interact with it in a browser, on a phone, or does it run automatically in the background?"

This one answer determines the stack recommendation.

---

## What to always include in Document 2

Regardless of stack:

1. Name every technology chosen
2. Give a plain English description of what each one does (use `plain_language_rules.md`)
3. Give a reason for each choice in plain English
4. Name exactly two alternatives with a plain English comparison
5. Specify versions (no "latest")
6. Flag any decisions the Architect needs to validate

---

## What to never do in Document 2

- Do not recommend a technology because it is fashionable
- Do not recommend a technology you cannot explain in plain English
- Do not leave the user to choose between technologies they don't understand
- Do not use version ranges ("3.x") — name the specific version
