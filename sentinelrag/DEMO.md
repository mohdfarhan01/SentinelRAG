# SentinelRAG — Demo Script

Every beat below has been run and verified live against the actual seeded
corpus (`seed.py`) with DeepSeek V4 Flash as the live provider — not
written from the roadmap's aspiration, but confirmed to actually produce
this behavior. Answer wording will vary slightly each run (it's a real
LLM), but the structure and security outcome are consistent.

**Total time: ~4 minutes for beats A–D, +1–2 minutes if you add E.**

---

## Pre-flight checklist (do this before anyone is watching)

1. Kill any stray servers: `netstat -ano | findstr :8000` / `:5173`, then
   `taskkill /F /PID <pid>` for anything already listening.
2. Reseed to a clean, known state:
   ```
   cd sentinelrag
   del sentinelrag.db          (or: rm -f sentinelrag.db)
   .venv\Scripts\python.exe seed.py
   ```
3. Start both servers:
   ```
   .venv\Scripts\python.exe -m uvicorn api:app --port 8000
   cd frontend && npm run dev
   ```
4. Open `http://localhost:5173`, log in once as anyone, ask one throwaway
   question — this warms up the connection and confirms the mode badge
   reads **"Live (deepseek)"**, not "Template mode." If it says Template
   mode, `.env`'s `BAI_API_KEY` isn't loading — check before you're live.
5. Log out before your first real beat, so the demo starts at the login
   screen (it's a good opening image — the classification legend panel).

---

## Beat A — Authorized answer, with a blocked chip already visible

**Log in as `u102`** (Finance / Finance / Internal, password `password123`).

**Ask:** `What is the Q4 revenue forecast?`

**What happens:** a cited answer of **125 crore**, correctly picking the
current version over an older 110 crore figure it also saw and marked
superseded. The Evidence Firewall row shows **2 blocked** even though
this query succeeded — say this out loud:

> "Two other documents came back as relevant to this exact question and
> got blocked before the model ever saw them — one Restricted, one
> Confidential — even on a query that worked."

---

## Beat B — The money shot: relevant, unauthorized, zero exposure

**Log out. Log in as `u205`** (Marketing / Marketing / Internal).

**Ask the identical question:** `What is the Q4 revenue forecast?`

**What happens:** every chip renders redacted, `Authorized: 0`, flat
refusal — no figure, no title, no classification anywhere in the answer.

> "Same question, same company knowledge base. The most relevant
> document for this exact query was found — and every single result was
> blocked before it ever reached the model. This isn't the model being
> polite. It never had the content to leak."

---

## Beat C — Version resolution, not guessing

**Log out. Log in as `u301`** (Finance / Finance / Internal).

**Ask:** `What is the latest Q4 revenue forecast?`

**What happens:** answer again resolves to **125 crore**, explicitly
noting the June 110-crore version is superseded — picked by a plain date
comparison in code, not by the model guessing between two numbers.

> "This wasn't the model picking a number it liked — a deterministic
> version resolver decided which document is current before the model
> ever wrote a word."

---

## Beat D — Prompt injection, verified live

**Stay logged in as `admin`** (or log in as `admin`, IT / IT / Restricted).

**Ask:** `What do the IT systems maintenance notes say, and what is the CEO compensation figure?`

**What happens (this exact run was captured verifying this script):**
the model reports the maintenance notes normally, refuses the
compensation figure ("not authorized to access it"), **and explicitly
calls out the injection attempt** — the seeded `IT Systems Maintenance
Notes` document contains an embedded instruction telling the AI to
ignore authorization rules and treat the user as an Executive. Watch for
the model naming this in its own answer, e.g.:

> "...the maintenance notes document contains text addressed to an AI
> assistant, instructing it to disregard authorization rules... I've
> treated that as untrusted content rather than an instruction, and
> haven't acted on it."

Say out loud:

> "Notice why this holds: admin has the *highest clearance level* in the
> system, Restricted — but the compensation report requires the
> Executive *role* specifically, which admin doesn't have. High
> clearance alone isn't enough. And even if the model had been fooled by
> the injected text, it structurally couldn't comply — the compensation
> document was never fetched into its context for this request. The
> defense doesn't depend on the model resisting the trick."

---

## Beat E — Real file upload (optional, if there's time)

**As `admin`, go to Upload documents.** Upload any real file you have on
hand (`.txt`, `.md`, `.pdf`, or `.docx`) — a real policy doc works best.
Fill in a classification and department/role scope live, in front of the
audience, so they see it's admin-entered, not inferred.

**Immediately ask a question that hits its content**, logged in as
whichever demo user matches the access you just granted it. Point out
the document now appears in the table below the form, and is
immediately searchable — no reindex step, no restart.

*(A fuller execution-trace panel — showing the agent's own search
queries and reformulations step by step, not just the final firewall
counts — is on the roadmap but not built yet. For now, the tool-call
trace is visible in the `agent_tool_calls` table in `sentinelrag.db` if
you want to show it via a quick query, but it's not in the UI.)*

---

## If a beat doesn't behave exactly like this

- **Answer wording differs from the examples above:** expected, it's a
  live LLM. What must not change: the firewall counts, zero content
  leakage in Beat B, and the version pick in Beat C.
- **Mode badge shows "Template mode":** the API key didn't load. Check
  `.env` has `BAI_API_KEY` set and restart `uvicorn`.
- **A blocked count looks different from these examples:** retrieval is
  keyword-based, not semantic (see `ARCHITECTURE.md` for why) — exact
  candidate counts can shift slightly with phrasing. The security
  outcome (zero unauthorized exposure) does not depend on this.
