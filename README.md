Evidence Firewall — Secure Enterprise Research Agent

1. Team Details
Team Name / ID: TBD (fill in before submission)
Team Lead: TBD
Team Members:
TBD | Agent Whisperer
TBD | Backend Developer
TBD | Frontend Developer
TBD | Data Engineer
Repo Link (Optional): N/A
Demo Link (Optional): N/A

2. Problem Statement
The Employee Who Asked for Too Much

Context
Your company has thousands of internal documents. Employees can ask questions such as:
"What was the revenue forecast for Q4?"
An AI assistant should be able to search documents, understand them, compare information and answer questions. But not every employee is allowed to access every document. Documents have classifications:
Public
Internal
Confidential
Restricted
Different employees have different permissions. The assistant must answer a question without exposing information that the employee is not authorized to access. Documents may also:
contradict each other
be outdated
have different versions
contain incomplete information
Critical requirement
An unauthorized document must never be provided to the LLM simply because it is relevant to the question.

The Challenge
Build a secure enterprise research agent that answers employee questions over internal documents while enforcing authorization. Documents have classifications and access rules. Relevant information that the requesting employee is not authorized to access must never be provided to the language model or revealed in the final answer.
Core Requirements
Accept a natural-language employee question and user context.
Ingest documents with classification, department, owner, and access-control metadata.
Search for relevant candidates but enforce authorization before document content reaches the LLM.
Handle outdated and conflicting authorized documents.
Return an answer with citations to the evidence the user is allowed to access.
Record an audit trail of the request, authorization decisions, and evidence used.
Safely respond when the answer exists only in documents the user cannot access.

3. TL;DR
Problem: Relevant docs can be off-limits; RAG prompts LLMs with content the employee has no right to see.
Solution: A firewall fuses retrieval+authorization into one call, so blocked content never reaches the LLM.
Who benefits: Enterprise employees get grounded answers; the company gets guaranteed no unauthorized leakage.

4. Scope of the Project
What are you building?
A secure research agent: employees ask questions over internal documents; an LLM agent retrieves, an "Evidence Firewall" deterministically strips anything the employee isn't authorized to see before it ever reaches the LLM, then the agent answers with citations and an audit trail.
How does it solve the problem statement?
Authorization runs inside the same server-side call as retrieval, not as an LLM instruction, so unauthorized content structurally cannot enter the LLM's context or the final answer.
Key features you're building for this hackathon:
Evidence Firewall: fused retrieval + deterministic ACL/RBAC authorization check per candidate document.
Deterministic version resolver for outdated/conflicting authorized documents (picks latest effective version).
Orchestrator agent (LLM, tool-calling) that answers only from authorized evidence, with citations.
Citation validator that strips any citation not backed by supplied authorized evidence.
Live UI panel showing Retrieved / Authorized / Blocked counts and audit trail per query.
What are you deliberately NOT doing? (Optional)
No fine-tuning, no content-based auto-classification, no SSO/OAuth, no more than 2 LLM agents, no custom vector DB.

5. Why an Agentic Approach?
What does your agent decide or do on its own?
The Orchestrator plans the retrieval query, judges whether returned evidence is sufficient or needs reformulation, and decides whether a genuine version conflict must be handed to a second Conflict Resolution agent instead of guessing.
Why wouldn't a fixed script, if-else rules, or a simple chatbot be enough?
Open-ended NL questions, judging "is this evidence enough," and phrasing an honest conflict disclosure require reasoning a fixed script can't do; but the actual security decision (who can see what) is deliberately NOT left to the agent - it's a deterministic, non-LLM check the agent cannot bypass or override.

6. Who It's For & What Changes
Who or what is this for?
Employees at a company with internal documents split across classification levels, departments, and roles.
The world today, without your solution:
Either employees can't self-serve answers at all, or a naive RAG chatbot risks leaking Restricted/Confidential content by stuffing it into the LLM prompt because it was "relevant."
The world with your solution, fully built and scaled to production:
Every employee gets instant, cited answers scoped exactly to what they're authorized to see, with zero unauthorized exposure and a full audit trail for every request, replacing manual document hunting and legal/compliance risk.
What your hackathon build actually delivers today:
End-to-end flow for the three official test cases: authorized answer, blocked-but-relevant document with safe refusal, and version-conflict resolution to the latest authorized figure - all with live firewall stats and citations.
Before vs. After
What Changes | Today | With Our Current Build | At Production Scale
Time to find an authorized answer | Manual search across docs/folders | Seconds, via chat | Seconds, org-wide
Risk of leaking restricted content | Depends on employee/admin discipline | 0% - blocked before LLM sees it | 0%, audited on every query
Handling outdated/conflicting docs | Manual comparison, guesswork | Deterministic latest-version pick | Same, plus conflict alerts
Traceability of who saw what | None / manual | Full audit log per query | Full, queryable audit trail

7. Architecture & Agents
How is your system put together?
Employee asks a question in a web chat. An Orchestrator Agent calls one tool that retrieves candidate document chunks and immediately runs a deterministic Evidence Firewall (authorization + version resolution) before anything returns to it, then it answers with citations from what survives.
7.1 Agents
- **Orchestrator Agent:** Plans the retrieval query, calls the firewalled search tool, judges evidence sufficiency, and synthesizes the cited answer. Uses Claude (Sonnet) for reliable tool-calling and grounded synthesis. Talks to the search tool and the Citation Validator.
- **Conflict Resolution Agent:** Runs only when two authorized, currently-effective documents genuinely conflict (not explained by version dates). Uses Claude to phrase an honest disclosure of both sides rather than guessing. Talks to the Orchestrator only, sees only pre-authorized evidence.
7.2 Services, APIs, Databases & Memory
- **Evidence Firewall + Authorization Engine (deterministic Python, no LLM):** Fused inside the search tool; checks classification/department/role/ACL/effective-date per candidate. Used by the search tool on every query.
- **Version Resolver (deterministic):** Picks the applicable document version by effective date; flags true conflicts. Used inside the search tool.
- **Vector Store (Chroma) + BM25:** Holds document chunks for hybrid semantic + keyword retrieval. Used by the search tool.
- **PostgreSQL:** Stores users, documents, versions, authorization decisions, and audit events. Used by the backend API.
- **Citation Validator (deterministic):** Strips any citation not backed by the evidence actually supplied to that call. Used after the Orchestrator drafts an answer.
- **Web Chat (React):** Where employees ask questions and see answers, citations, and firewall stats. Talks to the backend API.
How does your system remember things (memory & state)?
No cross-session memory: each query is self-contained (question + user context) so authorization is always re-evaluated fresh. Query history and every decision are persisted in PostgreSQL for audit lookup, not for chat continuity.
Diagram Link (Optional): See ARCHITECTURE.md in this repo for full Mermaid diagrams.
7.3 Example Walkthrough
Example input: User U205 (Marketing, clearance Internal) asks "What is the Q4 revenue forecast?" where the only matching document is Restricted/Executive-only.
1. [Web Chat] Sends the question and U205's user context to the Orchestrator Agent.
2. [Orchestrator Agent] Calls the search tool with the question and user context.
3. [Search tool: Retrieval] Finds DOC-201 "Q4 Revenue Forecast" (Restricted) as the top semantic match (uses: Vector Store).
4. [Search tool: Evidence Firewall] Checks access: U205's clearance (Internal) and role/department don't satisfy DOC-201's Restricted/Executive-only rules -> DENY, content dropped.
5. [Search tool] Returns to the Orchestrator: authorized_evidence = [], blocked_count = 1 (no content, no title).
6. [Orchestrator Agent] Sees zero authorized evidence, skips LLM synthesis, returns the fixed refusal template.
7. [Backend] Writes an audit event (query, decision, reason) to PostgreSQL (uses: PostgreSQL).
8. [Web Chat] Shows "I don't have enough authorized information to answer that" plus Retrieved 1 / Authorized 0 / Blocked 1.
Final output: A safe refusal with zero document content or metadata leaked, backed by an audit trail entry.
Anything special about how your workflow runs? (Optional)
Retrieval and authorization are fused into one non-decomposable server-side call: the Orchestrator can never call retrieval without the firewall running, so it cannot forget or be tricked into skipping the security check.

8. Tech Stack
Layer | Technology
Frontend / Interface | React + Vite + Tailwind
Backend | Python + FastAPI
Agent Framework | Native Anthropic tool-use loop (custom code, no heavy framework)
Database / Storage | PostgreSQL + Chroma (vector store)
Hosting | Local machine (Docker Compose)
Other | sentence-transformers (embeddings), rank-bm25 (keyword search), JWT (auth)

9. What to Expect From Our Current Build
Working:
Architecture, security model, and API/data design are fully specified in ARCHITECTURE.md.
Partly working, mocked, or hard-coded:
No code has been written yet - this submission is the planning/architecture phase only, per our current task.
Not working or not built yet:
Ingestion pipeline, Evidence Firewall implementation, agents, frontend, and audit logging - all designed, none implemented yet.
What we'd most like to be judged on:
The Evidence Firewall design: authorization fused into the retrieval tool itself so unauthorized content structurally cannot reach the LLM, rather than relying on prompting.

10. Future Scope
Idea 1
Name: RBAC/ABAC Policy Admin Console
What it is: A UI for security admins to manage roles, department mappings, and per-user access overrides instead of seeded JSON files.
Why it matters: Real enterprises need to update access policy without redeploying code or editing raw data.
How we'd build it: A CRUD admin panel over the existing Permission/ACL tables in PostgreSQL, gated to an Admin role.
Done when: An admin can add/revoke a user's document access and it takes effect on the next query.
Idea 2
Name: Field-Level Redaction
What it is: Redact specific sensitive fields (e.g. a salary figure) inside an otherwise-accessible document, instead of gating access at the whole-document level.
Why it matters: Some documents are mostly shareable but contain a few restricted fields; today classification is all-or-nothing.
How we'd build it: Tag sensitive spans at ingestion; the firewall replaces just those spans with "[redacted]" before content leaves the tool.
Done when: An authorized user sees the document with a specific field visibly redacted and cited as such.
Idea 3 (Optional)
Name: Continuous Red-Team Test Pipeline
What it is: An automated suite that re-runs leakage, injection, and citation-leak scenarios on every change to catch security regressions.
Why it matters: Authorization logic changes over time; regressions should be caught before deployment, not in production.
How we'd build it: CI job running the security test matrix (Users x Roles x Documents x Classifications) plus injection fixtures on every commit.
Done when: CI fails the build if any scenario shows nonzero unauthorized exposure.

11. Additional Notes (Optional)
This file is the hackathon submission form; the full technical blueprint (Mermaid diagrams, threat model, DB schema, API specs, roadmap) lives in ARCHITECTURE.md in this repo. Team details above are placeholders pending finalization.
