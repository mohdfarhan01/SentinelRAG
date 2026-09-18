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
The agent decides how to reformulate and re-search (up to 3 tries) when evidence is thin, when it has enough to answer, and how to honestly disclose a genuine cross-document conflict instead of guessing between two figures. Verified live, not scripted.
Why wouldn't a fixed script, if-else rules, or a simple chatbot be enough?
Open-ended questions, judging "is this evidence enough," and phrasing an honest conflict disclosure require reasoning a fixed script can't do. The actual security decision (who can see what) is deliberately NOT left to the agent - it's a deterministic check the agent cannot bypass.

6. Who It's For & What Changes
Who or what is this for?
Employees at a company with internal documents split across classification levels, departments, and roles.
The world today, without your solution:
Either employees can't self-serve answers at all, or a naive RAG chatbot risks leaking Restricted/Confidential content by stuffing it into the LLM prompt because it was "relevant."
The world with your solution, fully built and scaled to production:
Every employee gets instant, cited answers scoped exactly to what they're authorized to see, with zero unauthorized exposure and a full audit trail for every request, replacing manual document hunting and legal/compliance risk.
What your hackathon build actually delivers today:
A working web app: real login, an agentic LLM (DeepSeek V4 Flash or Gemini) that searches and re-searches through a fused authorization firewall, real document upload, and a redacted audit trace UI - not just the three official test cases in isolation.
Before vs. After
What Changes | Today | With Our Current Build | At Production Scale
Time to find an authorized answer | Manual search across docs/folders | Seconds, via chat | Seconds, org-wide
Risk of leaking restricted content | Depends on employee/admin discipline | 0% - blocked before LLM sees it | 0%, audited on every query
Handling outdated/conflicting docs | Manual comparison, guesswork | Deterministic latest-version pick | Same, plus conflict alerts
Traceability of who saw what | None / manual | Full audit log per query | Full, queryable audit trail

7. Architecture & Agents
How is your system put together?
An employee logs into a React app; a FastAPI backend authenticates them (role/department/clearance come only from the server's own record, never the client) and hands the question to one agent. The agent's only tool fuses retrieval, authorization, and version resolution - it can re-search before answering, but never sees unauthorized content.
7.1 Agents
- **Research Agent (tool-calling loop):** Decides how to search, reformulates and retries up to 3x if evidence is thin, synthesizes the cited answer, and discloses genuine version conflicts honestly instead of guessing. Uses DeepSeek V4 Flash or Gemini (swappable, auto-detected). Talks only to its one search tool.
7.2 Services, APIs, Databases & Memory
- **Evidence Firewall + Authorization Engine (deterministic Python, no LLM):** Fused inside the one search tool; checks classification/department/role/ACL/effective-date per candidate on every call.
- **Version Resolver (deterministic):** Picks the current version by effective date; flags genuine ties for the agent to disclose rather than guess between.
- **SQLite:** Stores users, documents, authorization decisions, and the full audit trail. Used by the backend API - no external database needed.
- **Citation Validator (deterministic):** Strips any citation not backed by evidence actually supplied to that call.
- **React Web App:** Login, chat with live firewall stats + a redacted execution trace, admin document upload. Talks to the FastAPI backend.
How does your system remember things (memory & state)?
No cross-session chat memory: each query is independently authorized. Every query, decision, and agent search is persisted in SQLite for the audit trace, not for conversational continuity.
Diagram Link (Optional): See ARCHITECTURE.md in this repo for full Mermaid diagrams.
7.3 Example Walkthrough
Example input: Marketing employee (U205) asks "What is the Q4 revenue forecast?" - the only real match is Restricted, Executive-only.
1. [React app] Sends the question with a server-issued JWT to POST /query.
2. [Agent] Calls its one search tool with the question.
3. [Search tool] Retrieves candidates; the Authorization Gatekeeper checks each - all denied for Marketing.
4. [Search tool] Returns to the agent: 0 authorized documents, blocked_count=4 - no titles, no content.
5. [Agent] Sees zero evidence, returns the fixed refusal - never calls the LLM to synthesize an answer.
6. [Backend] Logs the query and every decision + reason to the audit trail.
7. [React app] Shows the refusal, all 4 chips rendered redacted, and a link to the trace.
Final output: Safe refusal, zero document content or metadata leaked, backed by a full (redacted-for-Marketing) audit trace.
Anything special about how your workflow runs? (Optional)
Retrieval and authorization are fused into one non-decomposable server-side tool call: the agent can never call retrieval without the firewall running, so it cannot forget or be tricked into skipping the security check.

8. Tech Stack
Layer | Technology
Frontend / Interface | React + Vite
Backend | Python + FastAPI
Agent Framework | Custom tool-calling loop (DeepSeek + Gemini, swappable)
Database / Storage | SQLite
Hosting | Local machine
Other | bcrypt + JWT (auth), pypdf / python-docx (real file ingestion)

9. What to Expect From Our Current Build
Working:
Full pipeline live end to end: login, agentic search + answer, citations, audit trace - all 3 official PS14 tests pass.
Real LLM (DeepSeek V4 Flash) generating grounded, cited answers with zero unauthorized exposure, verified live.
Hybrid semantic + keyword retrieval (ChromaDB, local embeddings): paraphrased questions with no shared exact words are still found.
Admin document upload (PDF/DOCX/TXT) with manual classification/ACL, searchable immediately, no reindex step.
Redacted audit trace UI, proven (tested + verified in-browser) not to leak blocked-document metadata to non-admins.
Partly working, mocked, or hard-coded:
Demo corpus is curated/seeded; bulk upload of "thousands of documents" at real enterprise scale is untested.
Semantic retrieval embeds whole title+content per document, no chunking yet - fine at these document lengths.
Not working or not built yet:
A dedicated second "conflict resolution" agent for genuinely ambiguous cross-document disagreement.
An automated, parametrized security test matrix beyond the existing authorization and leakage test suites.
What we'd most like to be judged on:
The agent's own tool-calling: on a vague question it searched once, got nothing, and reformulated the query itself - captured live in the execution trace, not scripted, and the firewall held even then.

10. Future Scope
Idea 1
Name: Dedicated Conflict Resolution Agent
What it is: A second LLM call, triggered only when two authorized documents genuinely tie, to phrase the disclosure separately from the main answer.
Why it matters: Keeps the primary agent's prompt focused and makes conflict-handling independently testable.
How we'd build it: Trigger on the existing version resolver's tie-detection; hand off only the conflicting evidence, nothing else.
Done when: A synthetic tie between two same-effective-date documents produces a two-sided disclosure from the second agent, not the first.
Idea 2
Name: Security Test Matrix
What it is: Parametrized tests over Users x Roles x Documents x Classifications x document status (active/revoked/future-dated).
Why it matters: Turns "0% unauthorized exposure" from a claim into a continuously-checked, reportable number.
How we'd build it: pytest.mark.parametrize over the existing authorization engine, plus prompt-injection fixtures, run in CI.
Done when: CI reports "N cases, 0 leaks" and fails the build if that ever changes.
Idea 3 (Optional)
Name: Chunking for Long Documents
What it is: Split long documents into passages before embedding, so citations point at a specific section instead of a whole document.
Why it matters: Current semantic retrieval embeds whole title+content; fine at demo scale, weaker on real multi-page policies.
How we'd build it: Chunk at ingestion, embed each chunk, resolve authorization at the parent-document level so access control doesn't change.
Done when: A citation from a long uploaded document points at the specific passage the answer actually used.

11. Additional Notes (Optional)
This form summarizes a fully working implementation, verified live end to end, not a plan. Full technical detail (diagrams, threat model, schema) is in ARCHITECTURE.md; setup/run instructions in sentinelrag/README.md; a verified live demo script in sentinelrag/DEMO.md. Team details above are placeholders pending finalization.
