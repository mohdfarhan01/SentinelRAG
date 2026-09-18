# UI Revamp — Build Prompt

You are implementing a full frontend revamp of **SentinelRAG**, a secure
enterprise research agent built for hackathon problem statement PS14
("The Employee Who Asked for Too Much"). The backend is finished and
working. **Your job is the interface**, plus exactly one small, carefully
scoped backend addition (a signup endpoint).

Read this whole document before writing any code.

---

## 0. Where things are

Repo root: `C:\Users\Farhan PC\Documents\Project\Pragyaan`
App: `sentinelrag/`
Frontend: `sentinelrag/frontend/` (React 18 + Vite, plain JS, no TypeScript,
no CSS framework — hand-written CSS in one file)

Current frontend files:

```
sentinelrag/frontend/src/
├── main.jsx
├── App.jsx                      # session state, login gate, view switch
├── api.js                       # every fetch call lives here
├── index.css                    # ~940 lines, all styling, CSS variables at :root
└── components/
    ├── LoginScreen.jsx          # two-column: form left, access-tier list right
    ├── Sidebar.jsx              # brand, identity card, nav, sign out
    ├── ChatView.jsx             # ask box on TOP, answers listed below
    ├── EvidenceFirewall.jsx     # the chips row — the signature visual
    ├── TracePanel.jsx           # collapsible per-answer execution trace
    ├── AdminUpload.jsx          # admin-only upload form + document table
    └── BrandMark.jsx            # inline SVG shield logo + wordmark
```

Run it:

```
cd sentinelrag
.venv\Scripts\python.exe seed.py                          # once, idempotent
.venv\Scripts\python.exe -m uvicorn api:app --port 8000   # terminal 1
cd frontend && npm run dev                                # terminal 2
```

> Always use `.venv\Scripts\python.exe`, never a global `python` — a global
> environment on this machine has a broken package combination.

Demo accounts, password `password123` for all:
`u102` (Finance), `u205` (Marketing), `u301` (Finance), `admin` (IT, admin).

---

## 1. Hard rules — do not break these

This project's entire value proposition is that **authorization is
deterministic and cannot be influenced by the model or the client**. A UI
change that undermines that is worse than no UI change at all.

1. **Do not touch anything in `sentinelrag/sentinel/`** except where §4
   explicitly says so. The authorization gatekeeper, conflict resolver,
   citation validator, retrieval agents, and agent loop are finished,
   tested, and verified live. They are out of scope.
2. **Never send role, department, or clearance from the client.** The
   server reads them from the signed JWT only. If you find yourself
   adding a clearance field to a request body, stop — you have
   reintroduced the exact vulnerability this project exists to prevent.
3. **Never render blocked-document metadata.** The backend deliberately
   returns only a *count* of blocked documents to non-admins. Do not add
   tooltips, alt text, hidden DOM nodes, `title` attributes, or console
   logs that would expose blocked titles or IDs. Whatever the API doesn't
   send, the UI must not invent.
4. **Keep all 45 tests passing.** Run `.venv\Scripts\python.exe -m pytest -q`
   from `sentinelrag/` before you call the work done.
5. **No new heavy dependencies.** No Tailwind, no Material UI, no
   Chakra, no component library. Hand-written CSS, same as now. You may
   add `react-router-dom` if and only if you implement real routing per
   §5 — otherwise keep the existing state-based view switching.

---

## 2. What the user asked for, in their words

> "I want the UI to be better. The Home page. That sidebar explaining the
> four access levels doesn't look good. Also add a sign in option and
> inside login, make the UI similar to what AI models currently look like —
> the text field should be below. Add different color theme options. First
> add sign up option. It should be impressive to present but should not
> give too AI vibe."

Two clarifications, because the wording is ambiguous in two places:

- **"That sidebar explaining the four access levels"** is not the app
  sidebar. It is the right-hand column of `LoginScreen.jsx` (the
  `.login-ledger-side` block listing Public / Internal / Confidential /
  Restricted). That's the thing that needs redesigning.
- **"similar to what AI models look like"** refers to the *chat layout* —
  transcript above, composer pinned at the bottom, like ChatGPT or Claude.
  It does **not** mean the visual style should look AI-generated. See §7.

---

## 3. What to build — overview

| # | Deliverable |
|---|---|
| A | Theme system: 4 selectable color themes, persisted |
| B | Public landing / home page with Sign in + Sign up entry points |
| C | Sign up (new backend endpoint + frontend screen) and Sign in |
| D | Chat rebuilt as an assistant-style transcript with bottom composer |
| E | App shell + sidebar polish |
| F | Admin upload screen brought into visual consistency |
| G | Verification |

Build in this order. A and B/C can be committed separately from D.

---

## 4. Deliverable C's backend piece — signup (READ CAREFULLY)

There is currently **no signup endpoint**. You must add one. This is the
only backend change in scope.

Add `POST /auth/signup` to `sentinelrag/api.py`, next to the existing
`/auth/login` (around line 79).

### The security constraint that governs this entire endpoint

A self-service signup form where the user chooses their own clearance
would be an instant, total privilege escalation — anyone could register as
`Restricted` / `Executive` and read everything. That would invalidate the
whole project in front of a judge.

**Therefore the endpoint must hard-code the new user's privileges
server-side:**

```python
SIGNUP_ROLE = "Employee"
SIGNUP_DEPARTMENT = "General"
SIGNUP_CLEARANCE = "Public"
```

- Accept **only** `username` and `password` in the request body. Nothing else.
- Ignore any `role`, `department`, `clearance`, or `is_admin` field if a
  client sends one. Do not merely validate it — do not read it at all.
- Always create the user with `is_admin=False`.
- Reject duplicate usernames with a 409 and a plain message.
- Require a password of at least 8 characters; return 400 otherwise.
- Hash with the existing `hash_password` from `sentinel/auth.py`. Never
  store a plaintext password.
- Return the same shape as `/auth/login` (`access_token` + `user`), so the
  frontend can log the new user straight in.

`UserRepository.create_user(...)` already exists in
`sentinel/user_repository.py` with the signature you need, and
auto-generates a `user_id`. Use it.

### Make this visible, don't hide it

The signup UI must *tell the user* they're getting Public clearance, and
say that elevated access is granted by an administrator, not self-selected.
Something like:

> New accounts start at **Public** clearance. Role, department, and
> elevated clearance are assigned by an administrator — they can't be
> chosen here.

This turns a limitation into a demonstration of the product's thesis.
Judges will notice it. Do not bury it in small grey text; give it a
bordered note beside the form.

Also add a matching `signup(username, password)` function to `api.js`,
following the existing `login()` exactly (same error parsing via
`parseErrorDetail`).

---

## 5. Deliverable B — landing / home page

A logged-out visitor currently lands straight on a login form. Replace
that with a real landing page.

**Routing:** the app is currently a single view switched by `useState` in
`App.jsx`. Add `react-router-dom` and give these real URLs:

```
/            landing page (redirect to /app if a session exists)
/signin      sign in
/signup      sign up
/app         chat (protected)
/app/upload  admin upload (protected + admin-only)
```

Protected routes redirect to `/signin` when there's no session. The
existing `localStorage` session persistence in `App.jsx` stays as-is.

**Landing page content.** No stock photos, no illustrations of robots, no
generic hero gradient. Lead with the actual idea:

- A clear headline about the real problem: *relevant is not the same as
  authorized*. Do not write marketing fluff. The existing README's TL;DR
  is a good source of accurate phrasing.
- A short subhead explaining that authorization runs *before* content
  reaches the model, not after.
- Two buttons: **Sign in** (primary) and **Create account** (secondary).
- **A live, non-interactive miniature of the Evidence Firewall chip row** —
  a few authorized tier-colored chips plus two redacted "Blocked" chips.
  Reuse the real `.evidence-chip` styling. This is the single most
  compelling thing in the product; show it above the fold rather than
  describing it in words.
- A compact three-step explanation of the flow: *ask → firewall filters →
  cited answer*. Text and rules only — no animated SVG pipeline diagram.
- The four classification tiers, redesigned (see §6).

Keep the whole page to roughly two screens. Resist adding testimonials,
pricing, FAQ accordions, or a fake logo cloud.

---

## 6. The four access tiers — redesign

The current version (`.ledger-tier-list` in `LoginScreen.jsx`) is a flat
bulleted list with a small colored square per row. The user finds it weak,
and they're right: it reads as filler.

Rebuild it as **four tiers showing escalating restriction**, so the
hierarchy is legible at a glance rather than implied by reading order.
Pick one:

- Four cards in a row, each with a progressively heavier left border /
  deeper tier color, and a small lock-state indicator that escalates
  (open → half → closed).
- A vertical "ladder" where each step is visibly narrower than the one
  above it, communicating a shrinking audience.

Each tier needs: the name, who can see it, and a one-line concrete
example (e.g. Restricted → *"Board compensation review — Executive role
only"*). The existing `--tier-*` CSS variables already define the four
colors; keep using them so the tiers stay consistent with the chips and
badges elsewhere in the app.

This block appears on the landing page. Remove it from the sign-in screen
entirely — sign-in should be a focused, single-column form, not a
two-column split.

---

## 7. Visual direction — "impressive, but not AI vibe"

The user wants this to look designed, not generated. Concretely:

### Avoid

- Purple/violet→blue gradients, especially on buttons and hero text
- Glassmorphism, frosted blur panels, heavy `box-shadow` glows
- Emoji as iconography (🚀 🔒 ✨ 🤖)
- Generic sans everywhere at one weight
- Rounded-everything (`border-radius: 16px` on every surface)
- Copy like "Powered by AI", "Supercharge your workflow", "Seamlessly…"
- Animated gradient borders, floating particle backgrounds
- Centered single-column marketing layout with 200px of padding

### Aim for

The current design already has a defensible point of view — an
**institutional / document-archive** feel: IBM Plex Sans + Plex Mono,
small radii (3px/6px), muted paper background, restrained accent, monospace
for IDs and versions. It looks like enterprise document software, which is
exactly right for this product. **Build on it; don't throw it away.**

- Keep monospace for document IDs, versions, dates, usernames
- Sharp corners and hairline borders over shadows and big radii
- Type hierarchy through weight and size, not color
- Color used meaningfully — the tier colors *mean* something; don't
  introduce decorative colors that mean nothing
- Real density. Enterprise tools are information-dense; whitespace-heavy
  landing-page rhythm looks wrong here.
- Transitions under 150ms, on hover/focus only. No entrance animations on
  page load.

---

## 8. Deliverable A — theme system

Add **four** themes. `index.css` already declares every color as a CSS
variable on `:root`, so this is mostly mechanical.

1. **Archive** (default) — the current light paper look. Keep values as-is.
2. **Carbon** — dark. Near-black background, light text. Re-tune the four
   tier colors for dark backgrounds; do not simply invert, or
   Confidential's amber will vibrate. Set `color-scheme: dark`.
3. **Slate** — cool neutral grey-blue, mid-contrast, low saturation.
4. **Sepia** — warm off-white paper, brown-black ink. Reads like a
   physical document archive.

Implementation:

- Define each as `[data-theme="carbon"] { --ink: …; … }` overriding the
  `:root` block. Set `data-theme` on `document.documentElement`.
- Persist to `localStorage` under a key like `sentinelrag_theme`, and read
  it back on first paint. Wrap every `localStorage` access in `try/catch` —
  it throws in some privacy modes.
- Default to Archive when nothing is stored.
- Switcher lives in the app sidebar (bottom, above Sign out) **and** on the
  landing page header, so it's reachable before login. Four small labeled
  swatches, not a dropdown — a judge should be able to flip themes in one
  click during a demo.
- **Verify every theme against the redacted "Blocked" chip.** The redaction
  bars use `--redact` and must stay clearly readable as *deliberately
  hidden* in all four themes. In Carbon especially, a dark bar on a dark
  card will disappear. That chip is the product's signature visual — check
  it in each theme before moving on.

Also confirm tier colors keep sufficient contrast in every theme. Aim for
WCAG AA (4.5:1) on body text.

---

## 9. Deliverable D — the chat rebuild

This is the largest piece. Current `ChatView.jsx` puts the input at the
top and prepends new answers, so the transcript reads newest-first. Rebuild
it as a conventional assistant transcript.

### Layout

```
┌────────────────────────────────────────────┐
│ header: title + mode badge (Live / Template)│
├────────────────────────────────────────────┤
│                                            │
│  scrolling transcript, oldest → newest      │
│   · user question, right-aligned or         │
│     visually distinct                       │
│   · assistant response block:               │
│       – Evidence Firewall chip row          │
│       – answer text                         │
│       – conflict note (when present)        │
│       – sources list                        │
│       – collapsible execution trace         │
│                                            │
├────────────────────────────────────────────┤
│  composer, pinned to bottom                 │
└────────────────────────────────────────────┘
```

### Behavior

- Composer is a **textarea**, not an input. Enter submits; Shift+Enter
  inserts a newline. Auto-grow with height capped (~200px) then scroll.
- Auto-scroll to the newest message after a response arrives.
- While waiting, show the user's question immediately with a pending
  assistant block beneath it — a subtle "Searching authorized documents…"
  state. A quiet pulsing skeleton is fine; no bouncing dots, no typewriter
  effect. Responses are not streamed (the API returns one JSON payload), so
  do **not** fake token-by-token streaming.
- Disable the send button while a request is in flight; keep the composer
  focusable so the user can draft the next question.
- Empty state: a short line plus **three clickable starter questions** that
  fill the composer. Use real ones from `sentinelrag/DEMO.md` so they
  actually demonstrate something — including at least one that triggers a
  refusal and one that surfaces a version conflict. A demo where the first
  click shows the firewall blocking something is far stronger than one
  where it just answers.
- Errors render inline in the transcript where that answer would have
  been, not as a banner that pushes layout around.

### Keep exactly as-is

`EvidenceFirewall.jsx` and `TracePanel.jsx` are the parts that make this
project legible to a judge. Restyle them to fit the new layout if you
must, but **do not change what data they render**, and do not make the
chip row less prominent than it is today. The chip row should remain the
first thing visible in an assistant response.

---

## 10. Deliverables E & F — shell and admin

**Sidebar** (`Sidebar.jsx`): keep the structure (brand, identity card, nav,
sign out) and add the theme switcher above Sign out. Make the identity card
carry more weight — the user's clearance badge is the thing that explains
every answer they get, so it should be the most prominent element after
the brand. Collapse the sidebar to a top bar under ~900px width.

**Admin upload** (`AdminUpload.jsx`): functionally complete; needs visual
consistency only. The form is long — group it into labeled sections
(Identity / Classification & access / Content). Keep the document table
dense and monospaced. Do not change field names, the `FormData` keys, or
the submit logic — the endpoint contract is fixed.

---

## 11. API reference — exact shapes

Do not guess these; they're read from the live code.

`POST /auth/login` → `{ access_token, user: { user_id, username, role, department, clearance, is_admin } }`

`POST /auth/signup` → *you are building this* — return the same shape as login.

`POST /query` (Bearer token) → body `{ question }`, returns:

```js
{
  query_id: "…",
  answer: "…",
  citations: [ { document_id, title, version, classification } ],
  evidence_firewall: { retrieved: 4, authorized: 2, blocked: 2 },
  conflicts: [ "…" ],          // may be empty
  llm_mode: "deepseek" | "gemini" | "stub"
}
```

`GET /audit/{query_id}` → `{ steps: [{ stage, detail }], agent_tool_calls: [{ call_index, query, retrieved, authorized, blocked }], is_full_trace: boolean }`

`GET /documents` (admin) → `[{ document_id, title, classification, version, effective_date, status }]`

`POST /documents` (admin, multipart) — fields: `title`, `classification`,
`effective_date`, `allowed_departments`, `allowed_roles`, optional
`version`, optional `text_content`, optional `file`.

Note `llm_mode: "stub"` renders as "Template mode" — that's the no-API-key
deterministic path, and it must keep working. Don't make the UI assume an
LLM is present.

---

## 12. Verification — do all of this before declaring done

Do not rely on the code compiling. Check the actual behavior:

1. `npm run build` succeeds with no errors.
2. `.venv\Scripts\python.exe -m pytest -q` — all 45 pass.
3. Add backend tests for signup in `sentinelrag/tests/`: duplicate username
   rejected, short password rejected, and — most important — **a signup
   request that includes `"clearance": "Restricted"` and `"is_admin": true`
   in the body still produces a Public, non-admin user.** That test is the
   proof the endpoint is safe.
4. Sign up as a brand-new user in the browser, then ask
   *"What is the Q4 revenue forecast?"*. A Public-clearance account must
   get a refusal or Public-only evidence — never the Restricted forecast.
   If it doesn't, stop and fix the endpoint.
5. Log in as `u205` (Marketing) and ask the same question. Confirm blocked
   chips render redacted, with no title or ID readable in the DOM. Inspect
   the element — don't just look at the screen.
6. Log in as `admin`, confirm the upload nav appears; confirm it does *not*
   appear for `u102`, and that navigating directly to `/app/upload` as a
   non-admin doesn't render the form.
7. Flip through all four themes on the chat screen with a blocked chip
   visible. Check the redaction bars in each.
8. Resize to ~375px width. No horizontal scroll, composer still usable.
9. Reload the page mid-session — theme and login both persist.

---

## 13. Scope discipline

Don't add: chat history persistence across sessions (the backend is
deliberately stateless per query — each query is independently
authorized), message editing, regeneration, file attachments in chat,
dark-mode auto-detection beyond the four explicit themes, or any
onboarding tour.

If you think something in this document is wrong or would break the
security model, say so before implementing it rather than working around
it silently.

Commit in logical chunks (theme system / landing + auth / chat rebuild /
polish), not one giant commit.
