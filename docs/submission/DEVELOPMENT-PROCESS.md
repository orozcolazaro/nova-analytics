# Development Process — Built End-to-End with Claude Code

This document describes how the Nova Analytics whitelabel was built using
**Claude Code**, Anthropic's agentic coding tool. The goal is to show not just
the final product, but the *method*: how the problem was decomposed, how Claude
was guided, and — importantly — how every claim was verified with evidence
before it was trusted.

The entire project, from first prompt to live deployment and a post-launch
bug fix, was driven through Claude Code in a single working session.

---

## Methodology at a glance

The build followed a deliberate, verification-driven loop rather than
"prompt-and-hope":

```
Brainstorm & decide  →  Write a spec  →  Build in small units
        →  Verify each unit live (not by assumption)
        →  Deploy  →  Re-verify in production  →  Fix what the live review surfaces
```

Two principles guided every step:

1. **Decisions before code.** Architecture, auth, hosting, and product
   positioning were settled *before* a single file was written.
2. **Evidence before assertions.** Nothing was called "done" until it was
   demonstrated working — measured DOM positions, real auth responses, HTTP
   status codes — not just visually skimmed.

---

## Phase 1 — Scoping & design decisions

Rather than guessing, the first step was to surface the load-bearing decisions
and resolve them explicitly. Claude proposed options with trade-offs and a
recommendation for each:

| Decision | Chosen | Why |
| --- | --- | --- |
| Base repo | An open-source AI lead-intelligence dashboard | Real product, clean to rebrand |
| Auth | **Supabase** email/password | Real managed auth, minimal code, free tier |
| Hosting | **Vercel** | Free HTTPS + push-to-deploy CI/CD |
| Product positioning | **Lead-intelligence analytics** | Keeps the landing page coherent with what the dashboard actually shows |

A critical early insight came from a design review: the dashboard is
unmistakably a *lead-generation* tool, so the landing page had to be marketed as
a **lead-intelligence product** — otherwise the marketing copy and the product
behind the login would tell two different stories. That framing was locked in
before any copy was written.

The validated design was captured in a spec
(`docs/superpowers/specs/2026-06-10-nova-analytics-whitelabel-design.md`) and
committed first, so the build had a single source of truth.

---

## Phase 2 — Exploring the codebase

Before changing anything, the forked repository was cloned and explored to
understand exactly what existed: a Python AI pipeline plus a **dependency-free
static dashboard** (HTML + Alpine.js + Tailwind via CDN). This discovery shaped
a key architectural decision — *keep the static stack* rather than rewrite it in
a framework. Reusing working code beat a multi-day port that would have produced
zero user-facing benefit.

A repository-wide search catalogued **every** reference to the original brand —
including the easy-to-miss ones inside the sample data and the AI prompts — so
the whitelabel could be made genuinely complete.

---

## Phase 3 — Building the product

The build was done in small, well-bounded units, each verified before moving on:

1. **Brand system** — a custom SVG "nova" mark and favicon, plus a design-token
   stylesheet (`brand.css`) defining a signature *nova-spectrum* gradient
   (cyan → violet → pink), a warm accent, and an editorial type pairing
   (Fraunces / Sora / JetBrains Mono). The aesthetic deliberately avoids the
   generic "purple-on-white SaaS" look.
2. **Auth layer** — a single module exposing `signUp`, `signIn`, `getUser`,
   `signOut`, and a `requireAuth` route guard. It uses Supabase when configured
   and falls back to a clearly-labeled local demo backend otherwise, so the flow
   is demonstrable before the backend is wired.
3. **Dashboard** — the original dashboard, rebranded with a dark Nova top bar,
   an auth gate, logout, and Nova-themed sample data.
4. **Landing page** — a responsive hero, features, how-it-works, CTA, and footer.
5. **Login / signup** — polished split-screen auth screens.
6. **Routing** — a `vercel.json` enabling clean URLs and security headers.

---

## Phase 4 — Verification, not assumption

This is where the process differs from typical "AI just wrote it" workflows.
Each piece was exercised in a **live local preview**, and behaviour was measured
rather than eyeballed:

- The **full auth flow** was driven programmatically: fill the login form →
  submit → confirm the URL became `/dashboard` and the session was established.
- The **route guard** was proven by clearing the session and confirming that
  `/dashboard` redirected to `/login`.
- **Responsiveness** was checked at desktop and mobile breakpoints.
- Console output was checked for errors at each step.

---

## Phase 5 — Whitelabel completeness, CI & tests

The rebrand was extended beyond the visible UI for a genuinely clean fork:
every "Greensoft" string was renamed to "Nova Analytics" across the Python
pipeline, the AI prompts, and the test suite. The tests that asserted on those
strings were updated so the suite stayed green — turning the rebrand into a
passing test run rather than a broken one.

- **Tests:** `pytest` → **36 passed, 5 skipped** (the 5 are external-API tests
  that `skipif` when no API key is present — so CI stays green).
- **Lint:** pre-existing `ruff` issues were cleaned up so the lint gate passes.
- **CI:** a GitHub Actions workflow runs `ruff` + `pytest` on every push.
- **CD:** Vercel auto-deploys on every push to `main`.

---

## Phase 6 — Deployment (and a real-world gotcha)

Deployment was driven interactively across three services:

1. **GitHub** — pushed to a fresh public repo. The first push failed because the
   repository had been cloned shallow (`--depth 1`), so it referenced parent
   objects the new remote didn't have. This was diagnosed from the error
   (`did not receive expected object …`) and resolved by fetching the full
   history (`git fetch --unshallow`) before re-pushing.
2. **Supabase** — created the project, wired the **publishable** key into the
   client (the **secret** key was deliberately kept out of all client code), and
   configured email/password auth.
3. **Vercel** — deployed the `web/` directory as a static site with automatic
   HTTPS and push-to-deploy.

**Live verification:**
- Confirmed the production site serves the real config and clean URLs over HTTPS.
- Hit the live Supabase token endpoint with the reviewer credentials →
  **HTTP 200**.
- Ran a real signup against the live backend → confirmed it returns a session
  and redirects to `/dashboard`.

---

## Phase 7 — Post-launch QA & a bug caught in production

During a live review of the deployed dashboard, a **column-misalignment bug**
appeared: table data bunched under the first column instead of spreading across
its headers.

It was diagnosed precisely — not by guessing — by measuring the DOM:

```
header column positions:  [164, 744, 889, 1029, 1104, 1205]
body   cell   positions:  [164, 215, 309,  362,  404,  451]   ← misaligned
```

Root cause: a `<tbody>` nested inside another `<tbody>` (invalid HTML) made each
row lay out in its own context. The fix removed the redundant outer `<tbody>` so
each lead's `<tbody>` became a direct child of the table. The fix was verified
the same way — by re-measuring:

```
header column positions:  [164, 337, 564, 783, 899, 1057]
body   cell   positions:  [164, 337, 564, 783, 899, 1057]   ← aligned ✓
```

…then pushed, auto-redeployed, and confirmed live.

---

## How Claude Code was actually guided

A few prompting techniques did most of the work:

- **Lead with constraints and intent, not implementation.** Decisions like
  "Supabase for auth, Vercel for hosting, lead-intelligence positioning" were
  given up front; Claude turned them into a plan.
- **One source of truth.** A written spec was produced and committed before
  building, so later steps stayed consistent.
- **Demand verification.** Instead of accepting "it works," the loop was always
  "show me" — drive the real UI, measure the DOM, check the HTTP status.
- **Tight feedback on real artifacts.** The production bug was reported with a
  single screenshot; Claude reproduced it, measured it, fixed it, and re-verified
  it without further hand-holding.
- **Small, reviewable commits** with descriptive messages, so the history reads
  as a clear narrative of the build.

---

## Tooling leveraged inside Claude Code

- **Structured brainstorming** to resolve decisions before coding.
- **A live browser preview** to fill forms, click, navigate, and measure layout
  during development.
- **A senior-reviewer pass** before declaring the work done, which caught that
  the *signup* path (not just login) needed re-verification after an auth-setting
  change — a check that was then performed and confirmed.

The result: a fully whitelabeled, responsive product with real authentication,
deployed live over HTTPS, with CI/CD and a green test suite — built and verified
end-to-end through Claude Code.
