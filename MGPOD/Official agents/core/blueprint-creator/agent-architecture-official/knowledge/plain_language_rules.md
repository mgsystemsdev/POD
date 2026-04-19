# Plain Language Rules — Blueprint Creator
# How to explain every technical concept to any user

---

## The core rule

Every technical term that appears in a Blueprint Creator document must have a plain English translation either immediately after it (inline) or in the section where it first appears.

Format: "[Technical term] — [plain English translation]"

Example: "PostgreSQL — a database, which is a structured way to store and retrieve your data."

Never assume the user knows what a term means. Assume they don't. If they already know, the translation costs nothing. If they don't, it changes everything.

---

## The glossary — technical concepts and their plain English translations

### Databases and data storage

**Database** — a structured place where your app stores information so it can find it again later. Like a very organized filing cabinet.

**Relational database** — a database that stores information in tables (like spreadsheets) and connects related tables together.

**PostgreSQL / MySQL / SQLite** — specific types of relational databases. PostgreSQL is the most capable for most web apps. SQLite is the simplest, good for small projects or local development.

**NoSQL database** — a database that stores information in a more flexible format, not tables. Good when your data doesn't have a fixed shape.

**MongoDB** — a specific type of NoSQL database. Stores information as documents, similar to JSON files.

**Redis** — a database that keeps information in memory (very fast) instead of on disk. Used for things that need to be retrieved instantly, like login sessions.

**Schema** — the blueprint for how your database is organized. It defines what tables exist and what columns each table has.

**Migration** — a controlled change to your database structure. Like adding a new column to a table, done in a way that is reversible.

**ORM** — Object-Relational Mapping. A tool that lets you talk to a database using your programming language instead of SQL. Think of it as a translator between your code and your database.

**SQL** — Structured Query Language. The language used to ask a database questions and give it instructions.

---

### Web frameworks and backends

**Framework** — a pre-built toolkit that handles common tasks so you don't start from scratch. Like a house frame — you still build the house, but the foundation is already there.

**Backend** — the part of the system that runs on the server and handles data, business logic, and security. The user never sees it directly.

**Frontend** — the part of the system the user sees and interacts with: the visual interface.

**API** — Application Programming Interface. The connection point between two parts of your software, or between your software and an external service. Like a waiter at a restaurant: you give the order to the waiter (API), not the kitchen.

**REST API** — a specific way of designing APIs using web conventions. The most common style for web apps.

**Server** — a computer (or virtual computer) that runs your backend code and responds to requests from users.

**Node.js** — a way to run JavaScript on the server (not just in the browser).

**Python** — a programming language. Widely used for web backends, data processing, and automation. Known for being readable.

**FastAPI** — a Python framework for building APIs. Fast to develop with, produces good documentation automatically.

**Django** — a Python framework for building full web applications. Includes many built-in tools (authentication, admin panel, database handling).

**Flask** — a lighter Python framework. More flexible but provides less out of the box.

**Go (Golang)** — a programming language. Fast and efficient. Good for systems that need to handle many users simultaneously.

---

### Frontend and interfaces

**React** — a JavaScript library for building the visual parts of a web app. It handles what the user sees and how the interface responds to their actions.

**TypeScript** — JavaScript with type checking. It catches common errors before the code runs. More structured than plain JavaScript.

**HTML** — the structure of a web page. It defines what elements are on the page (buttons, text, images).

**CSS** — the visual style of a web page. It controls colors, fonts, spacing, and layout.

**Component** — a reusable piece of a user interface. A button, a form, a navigation bar — each is a component.

**State** — the current condition of something in the interface. "Is the menu open or closed?" "What items are in the cart?" That is state.

---

### Infrastructure and deployment

**Environment variable** — a setting stored outside your code that changes how the app behaves. Your database password, API keys, and the address of your server are all environment variables. They are never stored in the code itself.

**Local development** — running the app on your own computer while you build it. Not available to anyone else yet.

**Staging** — a copy of the production environment used for testing before releasing to real users.

**Production** — the live version of the app that real users interact with.

**Deployment** — the process of taking code from your computer and putting it on a server where users can access it.

**Docker** — a tool that packages your app and everything it needs to run into a container — a self-contained unit that runs the same way everywhere.

**Container** — a packaged unit of software. Like a shipping container: the contents are standardized and portable.

**Cloud hosting** — running your server on someone else's computers (AWS, Google Cloud, Azure, Heroku, Render, Railway, Fly.io, etc.) instead of buying and maintaining your own.

**Heroku / Render / Railway / Fly.io** — platforms that make it easy to deploy apps without managing servers directly. Good for startups and small teams.

**AWS / Google Cloud / Azure** — larger cloud platforms with more control and more complexity. Good for larger scale.

**CI/CD** — Continuous Integration / Continuous Deployment. An automated pipeline that tests your code and deploys it whenever you push a change.

---

### Authentication and security

**Authentication** — proving who you are. Logging in is authentication.

**Authorization** — proving what you are allowed to do. Checking that a logged-in user has permission to view a specific page.

**JWT** — JSON Web Token. A secure way to prove identity between a browser and a server without storing a session on the server.

**Session** — a record on the server that tracks who is logged in and for how long.

**OAuth** — a system that lets users log in with an existing account (Google, GitHub, Apple) instead of creating a new password.

**Hash / Hashing** — converting a password into a scrambled string that cannot be reversed. Passwords are always stored as hashes, never as plain text.

---

### Version control and collaboration

**Git** — a system for tracking every change to your code. It lets you go back to any earlier version.

**GitHub** — a website where code is stored and shared using Git.

**Repository (repo)** — a project's code and its entire history, stored in Git.

**Branch** — a separate copy of the code where you can make changes without affecting the main version.

**Commit** — saving a set of changes to Git with a description of what changed.

**Pull request (PR)** — a proposal to merge changes from one branch into another. It is reviewed before being accepted.

---

## How to apply these translations in documents

**Document 2 (Tech Stack):** After every technology name, add the plain English translation in parentheses or as a following sentence.

**Document 4 (Domain Model):** After technical database terms (foreign key, index, constraint), translate immediately.

**Document 6 (API and Interfaces):** After "endpoint," "REST," "authentication" — translate before explaining the specifics.

**Document 8 (Infrastructure):** Translate "environment variable," "container," "deployment," and any specific platform names.

---

## When a user asks "what does that mean?"

Stop. Translate immediately using the glossary above. Then continue.

Never say "you don't need to understand that." The user always benefits from understanding.
