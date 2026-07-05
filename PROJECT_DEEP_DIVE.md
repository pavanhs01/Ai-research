# AI Research Assistant — Complete Project Deep Dive

Repo: https://github.com/pavanhs01/Ai-research

---

## 1. What This Project Is

An AI Research Assistant is a **RAG (Retrieval-Augmented Generation) SaaS application**: users upload documents (PDF, DOCX, TXT, Markdown, or a URL), the system reads and indexes them, and users can then chat with an AI that answers questions **using only their uploaded documents as the source of truth**, always showing which document and passage each answer came from.

Think of it as: *"Upload your research papers, contracts, or notes, then ask questions and get answers with receipts — not a chatbot guessing from its training data."*

## 2. Why This Kind of Project Is Needed

Plain ChatGPT/Claude-style chat has three problems for document-heavy work:

1. **Hallucination risk** — a general LLM will confidently answer from its training data even when it doesn't know your specific document, with no way to tell fact from fabrication.
2. **No traceability** — even a correct-sounding answer gives you nothing to verify against.
3. **Context limits** — you can't paste 50 PDFs into a chat window.

RAG solves this by never asking the model to "recall" facts from memory. Instead, at question time, the system retrieves the *actual relevant passages* from your documents and hands them to the model as grounding, along with an instruction to answer only from what's given and cite it. This is the same pattern used by tools like NotebookLM, Perplexity, and enterprise "chat with your docs" products.

**Real use cases this serves**: a lawyer chatting with case files, a student querying lecture PDFs, a researcher cross-referencing papers, a company building internal knowledge search.

---

## 3. How It Works — End to End Flow

```
1. UPLOAD
   User uploads a PDF/DOCX/TXT/MD file (or pastes a URL)
        │
        ▼
2. PARSE
   Backend extracts raw text (pypdf for PDF, python-docx for Word,
   OCR fallback via pytesseract for scanned/image-based PDFs)
        │
        ▼
3. CHUNK
   Text is split into ~500-token chunks with 75-token overlap
   (overlap prevents cutting a sentence's context in half at a chunk boundary)
        │
        ▼
4. EMBED
   Each chunk is sent to an embedding model (text-embedding-3-small,
   or an OpenRouter equivalent) → converted into a vector (list of numbers
   representing semantic meaning)
        │
        ▼
5. INDEX
   Vectors are stored in a vector database (ChromaDB locally, Pinecone in
   production), namespaced per-project so one user's documents never
   leak into another's search results
        │
        ▼
6. USER ASKS A QUESTION
   The question itself is embedded the same way
        │
        ▼
7. RETRIEVE
   The vector DB returns the top-K chunks whose embeddings are most
   similar (closest in vector space) to the question's embedding
        │
        ▼
8. AUGMENT
   Those chunks are formatted into a context block, each tagged with
   a citation marker (source document + page/section)
        │
        ▼
9. GENERATE
   The LLM (GPT-4.1 or an OpenRouter model) receives a system prompt
   that says, in effect: "Answer ONLY using the provided context below.
   If the answer isn't in the context, say you don't know. Cite sources
   using the provided markers."
        │
        ▼
10. RESPOND
    The answer is returned to the user with clickable citations that
    expand to show the exact source passage
```

This entire pipeline is what "RAG" means: **R**etrieve relevant chunks, **A**ugment the prompt with them, **G**enerate the answer.

---

## 4. Architecture

### 4.1 High-Level Diagram

```
┌─────────────────────────────┐        ┌──────────────────────────────┐
│         FRONTEND             │        │           BACKEND             │
│   Next.js 15 (App Router)    │  HTTP  │          FastAPI               │
│   deployed on Vercel         │◄──────►│      deployed on Render        │
│                               │  JWT   │                                │
│  - React Query (data layer)  │        │  ┌──────────────────────────┐ │
│  - Clerk (auth UI + session) │        │  │   API Layer (routers)     │ │
│  - Tailwind (styling)        │        │  ├──────────────────────────┤ │
│  - React Hook Form + Zod     │        │  │   Service Layer           │ │
│    (form validation)          │        │  │  (RAG, ingestion, billing)│ │
└───────────────────────────────┘        │  ├──────────────────────────┤ │
                                          │  │   Repository Layer        │ │
              │                          │  │  (DB access via SQLAlchemy│ │
              │ verifies session         │  └──────────────────────────┘ │
              ▼                          └──────────────┬─────────────────┘
        ┌──────────┐                                    │
        │  Clerk    │◄───── JWKS verification ──────────┘
        │ (Auth-as-a│
        │  -Service)│
        └──────────┘
                                     ┌──────────────┴───────────────┐
                                     ▼                               ▼
                          ┌──────────────────┐          ┌──────────────────────┐
                          │   PostgreSQL       │          │  Vector Store          │
                          │  (users, projects, │          │  ChromaDB (dev) /      │
                          │  documents,         │          │  Pinecone (prod)       │
                          │  conversations,     │          └──────────────────────┘
                          │  messages,          │
                          │  subscriptions)     │          ┌──────────────────────┐
                          └──────────────────────┘          │  OpenAI / OpenRouter   │
                                                             │  (chat + embeddings)   │
                          ┌──────────────────────┐          └──────────────────────┘
                          │   AWS S3 (or local)   │
                          │  raw uploaded files    │          ┌──────────────────────┐
                          └──────────────────────┘          │  Stripe (billing)      │
                                                             └──────────────────────┘
```

### 4.2 Backend — Layered Architecture

The backend follows a strict **3-layer pattern**, which is a deliberate design choice for testability and separation of concerns:

- **API layer** (`app/api/v1/endpoints/`) — FastAPI route handlers. Only responsible for: parsing the request, calling a service, returning a response. No business logic lives here.
- **Service layer** (`app/services/`) — all business logic. `rag_service.py` orchestrates retrieval + generation, `ingestion_service.py` handles the parse→chunk→embed→index pipeline, `billing_service.py` wraps Stripe, `openai_service.py` wraps the LLM provider.
- **Repository layer** (`app/repositories/`) — the *only* place that touches the database directly via SQLAlchemy. Services never write raw queries; they call repository methods like `conversation_repo.delete(conversation)`.

Why this matters: you can unit-test a service by mocking its repository, and you can swap the database or ORM without touching business logic.

### 4.3 Frontend — Structure

- **`app/(auth)/`** and **`app/(dashboard)/`** — Next.js route groups. The `(auth)` group holds sign-in/sign-up pages; `(dashboard)` holds everything behind login. Route groups don't affect the URL, just organize the file tree.
- **`hooks/`** — one React Query hook file per resource (`useProjects`, `useDocuments`, `useChat`). Each hook wraps `fetch` calls through a shared `api-client.ts`, which automatically attaches the Clerk session token to every request.
- **`components/`** — organized by feature (`chat/`, `documents/`, `projects/`, `billing/`), not by type. This keeps everything related to one feature co-located.

### 4.4 Data Model (Simplified)

```
User (from Clerk, synced via webhook)
 └── Project (a "workspace" — e.g., "Thesis Research")
      ├── Document (uploaded file, has parsing status: pending/processing/done/failed)
      │    └── Chunk (stored in vector DB, referenced back to Document)
      └── Conversation (a chat thread within the project)
           └── Message (role: user/assistant, content, citations JSON)

Subscription (1:1 with User, tracks Stripe plan tier: free/pro/team)
```

### 4.5 Authentication Flow

1. Frontend uses Clerk's React SDK — the user signs in through Clerk's hosted UI components.
2. Clerk issues a short-lived JWT, attached automatically to every API request by `api-client.ts`.
3. Backend middleware (`get_current_db_user` dependency) verifies the JWT signature against Clerk's public JWKS endpoint (no shared secret needed — this is standard OAuth2/OIDC-style asymmetric verification).
4. On first request from a new Clerk user, a matching `User` row is created in Postgres. A Clerk **webhook** also fires on `user.created`/`user.updated`/`user.deleted` to keep the local DB in sync even for events that don't go through the API (e.g., a user deleting their account directly in Clerk).

---

## 5. Key Features (Complete List)

| Feature | Notes |
|---|---|
| Multi-format document ingestion | PDF, DOCX, TXT, Markdown, URL |
| OCR fallback | For scanned/image-based PDFs via pytesseract |
| Token-aware chunking | 500 tokens/chunk, 75-token overlap |
| Semantic search | Standalone search across all documents in a project |
| RAG chat with citations | Every answer traceable to source passage |
| Multiple conversations per project | With rename/delete |
| AI-generated document summaries | On-demand, one per document |
| Projects/workspaces | Isolate document sets per use case |
| Stripe billing | Free/Pro/Team tiers, checkout + customer portal + webhooks |
| Admin dashboard | User management, usage stats |
| Rate limiting | Per-IP sliding window middleware |
| Swappable vector store | Chroma (dev, zero setup) or Pinecone (managed, prod) |
| Swappable LLM provider | OpenAI directly, or any OpenAI-compatible API (OpenRouter, Groq, etc.) via `OPENAI_BASE_URL` |

---

## 6. Tech Stack Summary

| Layer | Choice | Why |
|---|---|---|
| Frontend framework | Next.js 15 (App Router) | Server components reduce client JS, file-based routing, first-class Vercel support |
| Frontend auth | Clerk | Avoids building password reset, MFA, session management from scratch |
| Frontend data layer | React Query | Handles caching, refetching, loading/error states declaratively |
| Frontend styling | Tailwind CSS | Fast iteration without leaving JSX |
| Backend framework | FastAPI | Async-native, automatic OpenAPI docs, Pydantic validation built in |
| ORM | SQLAlchemy 2.0 (async) + Alembic | Async matches FastAPI's model; Alembic gives versioned schema migrations |
| Database | PostgreSQL | Relational integrity for users/projects/billing; battle-tested |
| Vector store | ChromaDB / Pinecone | Chroma = zero-setup local dev; Pinecone = managed, scalable production option |
| LLM | GPT-4.1 (or OpenRouter-routed alternatives) | Strong instruction-following needed for "answer only from context" grounding |
| File storage | AWS S3 | Standard, cheap, decouples file storage from app servers |
| Payments | Stripe | Industry standard for subscription billing |
| Deployment | Vercel (frontend) + Render (backend + Postgres) | Vercel is purpose-built for Next.js; Render supports Docker + managed Postgres in one blueprint |

---

## 7. Challenges Faced (and How They Were Solved)

This section covers real issues hit while auditing, fixing, and deploying this specific project — useful both as an honest history and as talking points if you need to explain your debugging process.

### 7.1 Dependency lockfile was internally inconsistent
**Problem**: `package-lock.json` pinned `@clerk/nextjs@6.39.5`, but that version's peer dependency requires `next ^15.2.3`, while `package.json` pinned `next@15.1.0`. A fresh `npm install` failed with an unresolvable `ERESOLVE` error — meaning the project, as originally handed off, could not be installed on a clean machine at all.
**Fix**: Bumped `next` to `15.5.20` and `react`/`react-dom` to `19.2.7` — staying on the same major versions (no architecture change), just moving to patch/minor releases that satisfy the peer requirement chain.
**Lesson**: A lockfile committed at one point in time can silently drift out of sync with `package.json`'s intent once any dependency publishes a new version with tighter peer requirements — always verify with a *clean* install (`rm -rf node_modules && npm ci`), not just "it works on my machine."

### 7.2 Hardcoded placeholder values masquerading as config
**Problem**: `billing_service.py` had `PRICE_IDS = {PRO: "price_pro_placeholder", TEAM: "price_team_placeholder"}` hardcoded in source. This would compile and even pass tests (since tests mock Stripe), but would fail cryptically in production the moment a real user tried to check out.
**Fix**: Moved these into environment-driven `Settings` fields (`STRIPE_PRICE_ID_PRO`/`TEAM`), with an explicit, human-readable error raised at call time if they're unset — fail loud and clear instead of fail silent and confusing.

### 7.3 A feature that was half-wired
**Problem**: A `Conversation.update_title` repository method existed in the codebase but was never called from any API endpoint — dead code implying an intended feature (rename) that was never finished. There was also no delete endpoint for conversations at all, even though delete existed for both Documents and Projects — an inconsistent, incomplete CRUD surface.
**Fix**: Added `PATCH` (rename) and `DELETE` endpoints, ownership checks matching the existing security pattern, frontend hooks, and UI (pencil/trash icons in the conversation sidebar), plus tests covering the new behavior and the ownership boundary (a non-owner gets a 403).

### 7.4 Cloud database URL scheme mismatch
**Problem**: Render's managed Postgres (and most PaaS providers — Railway, Heroku-style) hand out a connection string as `postgresql://user:pass@host/db`. But SQLAlchemy's **async** engine requires the driver to be explicit: `postgresql+asyncpg://...`. Without a fix, the app would crash immediately on boot in production despite working fine locally (where the `.env` file was hand-written with the correct scheme).
**Fix**: Added a Pydantic `field_validator` on the `DATABASE_URL` setting that automatically rewrites `postgres://` or `postgresql://` to `postgresql+asyncpg://` — so the app works correctly regardless of what scheme the hosting platform provides, with zero manual intervention needed at deploy time.

### 7.5 Vercel config using a deprecated secrets syntax
**Problem**: `vercel.json` referenced environment variables using the old `"KEY": "@secret_name"` syntax, which requires pre-creating secrets via the Vercel CLI (`vercel secrets add`). Nobody using the modern Vercel dashboard flow (just typing values into the Environment Variables UI) would have those secrets — the build would fail with "Environment Variable references Secret which does not exist."
**Fix**: Removed the `env` block entirely; env vars are now set directly through the dashboard, which is both the current recommended approach and simpler.

### 7.6 Sandbox network restrictions during deployment
**Problem**: While trying to actually execute the Render/Vercel deployment on the user's behalf, the working environment's outbound network access was restricted to an allowlist that didn't include `api.render.com` or `api.vercel.com` (it did include `github.com`/`api.github.com`, which is why the GitHub push could be automated but the platform deploys could not).
**Resolution**: Rather than claim to have deployed something that wasn't actually deployed, this was surfaced transparently, with a precise manual walkthrough (exact fields, exact values, exact order of operations to avoid the "frontend needs backend's URL, backend needs frontend's URL for CORS" chicken-and-egg problem) handed to the user instead.
**Lesson (broader, real-world one)**: any environment that executes code or agents on your behalf — CI runners, AI sandboxes, restricted VPCs — will have a network boundary somewhere. Knowing where that boundary is (and designing your deployment process to hand off cleanly at that boundary) is itself part of the architecture.

### 7.7 Skipped test masking a missing dev dependency
**Problem**: One PDF-parsing test was silently skipped in every test run (`pytest.skip("reportlab not installed")`). A skipped test doesn't fail CI, so this could persist indefinitely without anyone noticing that PDF parsing wasn't actually being tested end-to-end.
**Fix**: Identified this was just a missing *test-fixture* dependency (`reportlab`, used only to *generate* a sample PDF for the test to parse — not a runtime dependency of the app itself), installed it, and confirmed the previously-skipped test passes.

---

## 8. Technical Q&A

**Q: Why RAG instead of fine-tuning a model on the user's documents?**
A: Fine-tuning is expensive, slow to update (retraining needed every time a document changes), and doesn't reliably teach a model new *facts* — it mostly changes style/behavior. RAG updates instantly (just re-index) and lets you show exactly which text an answer came from, which fine-tuning cannot do.

**Q: How do you prevent one user's documents from leaking into another user's search results?**
A: The vector store is namespaced per-project. Every embedding is written to and queried from a project-scoped namespace/collection, so a similarity search physically cannot return vectors belonging to a different project, regardless of how similar the content might be.

**Q: Why chunk with overlap instead of clean, non-overlapping splits?**
A: If a chunk boundary falls in the middle of an important sentence or idea, a non-overlapping split can cut it in a way that loses meaning in both resulting chunks. A 75-token overlap means the "seam" between chunks still contains full context on both sides.

**Q: How do you stop the LLM from hallucinating an answer not actually in the documents?**
A: Two layers: (1) the system prompt explicitly instructs the model to answer only from the provided context and to say "I don't know" if the answer isn't present, and (2) every claim in the answer is expected to map to a citation marker tied to a specific retrieved chunk — if the model can't cite it, that's a signal (surfaced in the UI) that it's not well-grounded.

**Q: Why async SQLAlchemy instead of the traditional sync version?**
A: FastAPI is built around Python's `asyncio` — using a sync DB driver would block the event loop on every query, defeating the purpose of using an async framework at all under concurrent load. `asyncpg` (the driver) and async SQLAlchemy let the app handle many simultaneous requests without spawning a thread per request.

**Q: How is auth verified without the backend and Clerk sharing a secret?**
A: Clerk signs JWTs with a private key; the backend verifies the signature using Clerk's *public* key, published at a JWKS (JSON Web Key Set) endpoint. This is standard asymmetric-key JWT verification (the same model OAuth2/OIDC providers use) — no shared secret ever needs to exist between the two systems, which is safer than a shared-secret model.

**Q: What happens if a webhook from Clerk or Stripe is delivered twice (duplicate delivery)?**
A: Webhook handlers should be idempotent — e.g., a `user.created` event upserts (create-or-update) rather than blind-inserts, so processing the same event twice doesn't create a duplicate row or error out. This is a general webhook-handling best practice: any webhook provider can and will occasionally redeliver events.

**Q: Why separate the Repository layer from the Service layer at all — isn't that overkill for one app?**
A: It pays off in two concrete ways here: (1) tests can mock the repository and test business logic in isolation, without needing a real database, and (2) if you ever needed to change ORMs or add a caching layer in front of the database, only the repository layer would need to change — services and API routes stay untouched.

**Q: How would this scale if usage grew significantly?**
A: A few natural next steps: move ingestion (parsing/chunking/embedding) to a background job queue (Celery + Redis are already in `requirements.txt`, suggesting this was planned) so large-file uploads don't block the request thread; add a caching layer (Redis) for frequently-repeated queries; move from Chroma to Pinecone in production for the vector store, since Pinecone is a managed, horizontally scalable service rather than a local file-backed store.

**Q: Why is the vector store swappable (Chroma vs. Pinecone) instead of hardcoding one?**
A: This is the **Strategy pattern** — both are hidden behind a common `VectorStoreProvider` interface, so the rest of the app calls generic methods like `upsert()` and `query()` without knowing which backend is in use. This makes local development free and dependency-free (Chroma runs as a local file), while production can use a managed service, without touching business logic in either case.

**Q: Same question for the LLM provider — why is `OPENAI_BASE_URL` configurable?**
A: Any provider that implements the OpenAI-compatible API shape (OpenRouter, Groq, Together AI, etc.) can be swapped in by changing a URL and model name string, with zero code changes to `openai_service.py`. This avoids vendor lock-in and lets you pick a provider based on cost, model quality, or rate limits without a rewrite.

**Q: What's the actual security boundary for a document — can another user ever see it?**
A: Every document, project, and conversation query filters by `owner_id` (or project ownership) at the repository/service layer, checked against the authenticated user's ID from their verified JWT — not from anything the client claims about itself. Ownership checks happen server-side on every read/write, so even a modified request from a malicious client can't access another user's data by guessing an ID.

**Q: Why does rate limiting exist, and how does it work here?**
A: To prevent abuse (accidental infinite-loop clients or intentional scraping/DoS) and to control LLM API cost exposure, since every chat message triggers a paid API call downstream. It's implemented as ASGI middleware using a sliding time-window counter per client, configurable via `RATE_LIMIT_PER_MINUTE`.

---

## 9. Quick Reference: Where Things Live

```
backend/app/
├── main.py                  # FastAPI app entrypoint, middleware registration
├── core/
│   ├── config.py            # All environment variables — single source of truth
│   ├── exceptions.py        # Custom exception hierarchy → consistent error JSON shape
│   └── rate_limit.py        # Rate limiting middleware
├── models/                  # SQLAlchemy ORM models (the actual DB schema)
├── repositories/            # DB access layer — the only place with raw queries
├── services/                # Business logic (RAG, ingestion, billing, OpenAI wrapper)
├── schemas/                 # Pydantic request/response shapes (API contract)
└── api/v1/endpoints/        # Route handlers, one file per resource

frontend/
├── app/(auth)/               # Sign-in / sign-up pages
├── app/(dashboard)/          # Everything behind login
├── components/                # UI, organized by feature
├── hooks/                     # React Query data-fetching hooks
├── lib/api-client.ts          # Shared fetch wrapper, attaches Clerk token
└── schemas/                   # Zod validation schemas (mirrors backend Pydantic schemas)
```
