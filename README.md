# AI Research Assistant

A production-ready SaaS for chatting with your own documents — PDFs, DOCX, TXT, Markdown, and URLs — grounded entirely in retrieved content with inline citations. Zero hallucination by design.

## Quick start (local dev — 5 steps)

### Prerequisites
- Python 3.12+
- Node.js 20+
- PostgreSQL 15+ running locally (or use `docker-compose up -d postgres`)
- A [Clerk](https://clerk.com) account (free)

---

### Step 1 — Clone and copy env files

```bash
git clone <your-repo>
cd ai-research-assistant

cp backend/.env.example backend/.env
cp frontend/.env.local.example frontend/.env.local
```

---

### Step 2 — Fill in Clerk keys

1. Go to [dashboard.clerk.com](https://dashboard.clerk.com) → Create application
2. Copy **Publishable key** and **Secret key**
3. Paste into `frontend/.env.local`:
   ```
   NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...
   CLERK_SECRET_KEY=sk_test_...
   ```
4. Paste **Secret key** into `backend/.env`:
   ```
   CLERK_SECRET_KEY=sk_test_...
   CLERK_JWKS_URL=https://<your-clerk-domain>.clerk.accounts.dev/.well-known/jwks.json
   CLERK_ISSUER=https://<your-clerk-domain>.clerk.accounts.dev
   ```
   (Your Clerk domain is visible in the dashboard URL)
5. In Clerk dashboard → Webhooks → Add endpoint:
   - URL: `http://localhost:8000/api/v1/webhooks/clerk` (use [ngrok](https://ngrok.com) to expose locally)
   - Events: `user.created`, `user.updated`, `user.deleted`
   - Copy the signing secret → `backend/.env` → `CLERK_WEBHOOK_SECRET=whsec_...`

---

### Step 3 — Start Postgres

```bash
# Option A: Docker (easiest)
docker-compose up -d postgres

# Option B: Local Postgres
createdb research_assistant
```

---

### Step 4 — Start backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head              # Creates all 7 tables
uvicorn app.main:app --reload
```

Backend runs at **http://localhost:8000**  
Swagger docs: **http://localhost:8000/docs**

---

### Step 5 — Start frontend

```bash
cd frontend
npm install
npm run dev
```

App runs at **http://localhost:3000**

---

### Step 6 — Add your OpenAI key (to enable chat)

In `backend/.env`:
```
OPENAI_API_KEY=sk-...
```

Restart the backend. You can now upload documents and chat with them.

---

### Step 7 — Make yourself admin (optional)

```sql
-- Run in psql or any Postgres client
UPDATE users SET role = 'admin' WHERE email = 'you@example.com';
```

Then visit http://localhost:3000/admin to see platform stats and user list.

---

## Running tests

```bash
cd backend
# Make sure Postgres is running with a test_research_assistant database:
createdb test_research_assistant

source venv/bin/activate
pytest tests/ -v --tb=short
```

Expected: **59 passed, 1 skipped** (PDF test skipped without reportlab)

---

## Production deployment

### Frontend → Vercel

1. Import repo to [vercel.com](https://vercel.com), set root directory to `frontend`
2. Add environment variables in Vercel dashboard:
   - `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`
   - `CLERK_SECRET_KEY`
   - `NEXT_PUBLIC_API_URL` (your Render backend URL)
   - `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` (if using billing)

### Backend → Render

1. Connect repo at [render.com](https://render.com), use the `render.yaml` blueprint
2. Add environment variables in Render dashboard:
   - `DATABASE_URL` (Render managed Postgres, or Neon/Supabase)
   - `CLERK_SECRET_KEY`, `CLERK_JWKS_URL`, `CLERK_ISSUER`, `CLERK_WEBHOOK_SECRET`
   - **`OPENAI_API_KEY`** ← entered here at deploy time, never in the repo
   - `PINECONE_API_KEY`, `PINECONE_ENVIRONMENT`, `PINECONE_INDEX_NAME`
   - `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_S3_BUCKET`
   - `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`
   - `VECTOR_STORE_PROVIDER=pinecone` (switch from chroma for production)
3. Run migrations: `alembic upgrade head` (add as a Render release command)
4. Update Clerk webhook URL to your production backend URL

---

## Architecture

```
Upload → Parse (PDF/DOCX/TXT/MD/URL + OCR fallback)
       → Chunk (500 tokens / 75 overlap)
       → Embed (text-embedding-3-small)
       → Store (Chroma dev / Pinecone prod, namespaced per project)
       → Retrieve (top-k semantic search)
       → Build context with [Source: filename, page, section] headers
       → GPT-4.1 chat completion with strict no-hallucination system prompt
       → Return answer + citations resolved to chunk metadata
```

## Feature list

| Feature | Status |
|---|---|
| Auth (Clerk JWT + webhook sync) | ✅ |
| Document upload (PDF, DOCX, TXT, MD, URL) | ✅ |
| Parsing + OCR fallback for scanned PDFs | ✅ |
| Token-aware chunking with overlap | ✅ |
| OpenAI embeddings (text-embedding-3-small) | ✅ |
| Vector indexing (Chroma / Pinecone) | ✅ |
| RAG chat with citations | ✅ |
| Projects & Workspaces | ✅ |
| Semantic search | ✅ |
| Conversation history | ✅ |
| AI document summaries | ✅ |
| Citation highlighting (expandable snippets) | ✅ |
| Stripe billing (checkout, portal, webhooks) | ✅ |
| Admin dashboard (stats + user management) | ✅ |
| Deployment configs (Vercel + Render + CI) | ✅ |

## Stack

**Frontend**: Next.js 15 (App Router) · TypeScript · Tailwind CSS · Clerk · React Query · React Hook Form · Zod  
**Backend**: FastAPI · SQLAlchemy (async) · Alembic · Pydantic v2  
**Database**: PostgreSQL  
**Vector DB**: ChromaDB (dev) / Pinecone (prod)  
**AI**: OpenAI GPT-4.1 + text-embedding-3-small  
**Storage**: AWS S3  
**Auth**: Clerk  
**Billing**: Stripe  
**Deploy**: Vercel (frontend) · Render (backend) · Docker · GitHub Actions CI

## Changelog

### Fixes applied during audit (this session)
- **Dependency conflict resolved**: `next` bumped 15.1.0 → 15.5.20 and `react`/`react-dom` bumped 19.0.0 → 19.2.7 to satisfy `@clerk/nextjs`'s peer requirements. The original lockfile was internally inconsistent and would not install cleanly on a fresh clone.
- **Stripe price ID placeholders removed**: `STRIPE_PRICE_ID_PRO`/`STRIPE_PRICE_ID_TEAM` are now real environment variables (see `.env.example`) instead of hardcoded placeholder strings. Checkout now fails with a clear configuration error if they're unset, instead of silently calling Stripe with a fake price ID.
- **Conversation delete & rename added**: previously only projects and documents could be deleted; conversations had no delete or rename endpoint despite a `title` field already existing on the model. Added `DELETE /api/v1/chat/conversations/{id}` and `PATCH /api/v1/chat/conversations/{id}`, plus matching frontend hooks and UI (trash + pencil icons in the conversation sidebar).
- **OpenRouter support**: `OPENAI_BASE_URL` is now configurable, so any OpenAI-compatible provider (OpenRouter, Groq, etc.) can be used instead of OpenAI directly.

### Verification
- Backend: 64/64 tests passing against a real PostgreSQL 16 instance (fresh `pip install`)
- Frontend: zero TypeScript errors, zero lint errors, clean `next build` across all 12 routes (fresh `npm install`)
