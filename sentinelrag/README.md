# SentinelRAG

A secure enterprise research agent (PS14: "The Employee Who Asked for Too
Much"). Employees ask natural-language questions over internal company
documents; an agentic AI answers them — but a deterministic **Evidence
Firewall** enforces authorization *before* any document content reaches
the model, so a relevant-but-restricted document can never leak, however
the model behaves.

For the full architecture, threat model, and design rationale, see
[`ARCHITECTURE.md`](../ARCHITECTURE.md). For a rehearsed, verified demo
script, see [`DEMO.md`](DEMO.md).

## What's actually built

- **Deterministic security core** — authorization, version/conflict
  resolution, and citation validation are plain Python, never an LLM
  decision. See `sentinel/authorization.py`, `sentinel/conflict_resolver.py`.
- **Real agentic loop** — with an LLM configured, the model decides how
  to search (and can reformulate and re-search, up to 3 times) via one
  fused retrieval+authorization tool (`sentinel/agent_tools.py`,
  `sentinel/agent_loop.py`). Without a key, a deterministic fixed
  pipeline runs instead — same response shape either way.
- **Two LLM providers** — DeepSeek V4 Flash (via chat.b.ai/api.b.ai) and
  Google Gemini, both optional, auto-detected from whichever API key is
  set (`sentinel/llm_client.py`). Neither is required — the whole system
  runs in a deterministic template mode with zero API calls if no key is
  configured.
- **Real document ingestion** — `.txt`, `.md`, `.pdf`, `.docx` via the
  admin upload endpoint, with classification/ACL always entered by hand,
  never inferred from content.
- **Hybrid semantic + keyword retrieval** — a ChromaDB-backed semantic
  search (local embedding model, no API key), adapted from a teammate's
  separate SentinelRAG prototype, fused with the original keyword matcher
  via Reciprocal Rank Fusion, so a paraphrased question sharing none of a
  document's exact words is still found, without regressing exact-term/ID
  lookups (`sentinel/vector_store.py`, `sentinel/semantic_retrieval.py`,
  `sentinel/hybrid_retrieval.py`). Both the agentic and deterministic
  paths pick this up automatically; falls
  back to keyword-only if chromadb isn't installed. The vector index is
  never trusted as a system of record -- every hit is resolved back to
  the live document before authorization ever sees it.
- **Full audit trail** — every query, authorization decision, and agent
  search is logged; visible in the UI as a per-answer execution trace,
  redacted for non-admins so the trace itself can't leak metadata.
- **React frontend** — login, chat with a live "Evidence Firewall"
  visualization (blocked documents render as a redacted chip, not just a
  number), and an admin upload screen.
- **CLI** — a lighter-weight interface (`cli.py`) reading documents from
  a JSON file instead of the database, useful for quickly checking the
  three official PS14 test scenarios without starting the web stack.

## Not built (see `ARCHITECTURE.md` and `ROADMAP.md` for the plan)

- A dedicated second "conflict resolution" LLM agent for genuinely
  ambiguous cross-document conflicts (today, the single answer-generation
  call handles this directly, and does so honestly rather than guessing —
  see `DEMO.md` for a live example).
- A parametrized security test matrix beyond the existing authorization
  and leakage tests.

## Project layout

```
sentinelrag/
├── sentinel/              # the actual application, provider- and UI-agnostic
│   ├── models.py            # User, Document
│   ├── authorization.py     # AuthorizationGatekeeper -- the security kernel
│   ├── conflict_resolver.py # version resolution
│   ├── retrieval.py         # keyword retrieval
│   ├── vector_store.py      # ChromaDB index (semantic retrieval)
│   ├── semantic_retrieval.py# same interface as retrieval.py, embeddings-backed
│   ├── hybrid_retrieval.py  # fuses both via Reciprocal Rank Fusion
│   ├── retrieval_factory.py # picks hybrid if chromadb is available, else keyword-only
│   ├── agent_tools.py       # DocumentSearchTool -- the one LLM-facing tool
│   ├── agent_loop.py        # agentic orchestration
│   ├── answer_synthesis.py  # deterministic-path answer generation
│   ├── query_planner.py
│   ├── llm_client.py        # the only provider-specific file
│   ├── citation_validator.py
│   ├── orchestrator.py      # wires it all together, both paths
│   ├── audit.py             # SQLite audit log (write + read)
│   ├── audit_trace.py       # redaction logic for the trace endpoint
│   ├── auth.py               # bcrypt + JWT
│   ├── user_repository.py    # SQLite-backed users
│   ├── document_repository.py# SQLite-backed documents (admin uploads)
│   ├── document_store.py     # JSON-backed documents (CLI)
│   └── ingestion.py          # file text extraction
├── api.py                  # FastAPI app -- thin HTTP layer only
├── cli.py                  # CLI entrypoint
├── seed.py                 # seeds demo users + curated demo corpus
├── frontend/                # React + Vite
├── data/                     # JSON test fixtures + sample documents
└── tests/
```

## Setup

Requires Python 3.11+ and Node 18+.

```
cd sentinelrag
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
cd frontend
npm install
cd ..
```

> This project uses its own virtual environment deliberately. Always run
> `.venv\Scripts\python.exe`, never a global `python`/`pip` — a global
> environment on this machine has an unrelated broken package
> combination that will produce confusing errors otherwise.

### API keys (optional)

Copy `.env.example` to `.env` and fill in either key — or leave both
blank to run in deterministic STUB mode (no network calls, no cost,
still fully functional):

```
LLM_PROVIDER=deepseek
BAI_API_KEY=your-key-here
GEMINI_API_KEY=your-key-here
```

## Running it

Seed the database once (idempotent — safe to re-run):

```
.venv\Scripts\python.exe seed.py
```

Then, in two separate terminals:

```
.venv\Scripts\python.exe -m uvicorn api:app --port 8000
```
```
cd frontend
npm run dev
```

Open `http://localhost:5173`. Demo accounts (password `password123` for
all): `u102` / `u301` (Finance), `u205` (Marketing), `admin` (IT, admin
access). See `DEMO.md` for a scripted walkthrough of what each account
demonstrates.

### Running the CLI instead

```
.venv\Scripts\python.exe cli.py --user data/users/u102.json --question "What is the Q4 revenue forecast?"
```

### Running the tests

```
.venv\Scripts\python.exe -m pytest -q
```

All tests run without any API key — the deterministic paths and a fake
LLM client cover the security-critical behavior without a network call.

## Troubleshooting

**`[WinError 10048] only one usage of each socket address...`** — port
8000 or 5173 is already in use, usually a server left running from a
previous session.
```
netstat -ano | findstr :8000
taskkill /F /PID <the number in the last column>
```

**Mode badge in the UI says "Template mode" instead of "Live (...)"** —
no API key loaded. Check `.env` exists (not just `.env.example`) and has
`BAI_API_KEY` or `GEMINI_API_KEY` set, then restart `uvicorn`.

**`sqlite3.OperationalError: database is locked` / can't delete
`sentinelrag.db`** — a running `uvicorn` process still has it open; stop
the server first.
