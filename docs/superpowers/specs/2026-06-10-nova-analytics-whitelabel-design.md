# Nova Analytics — Whitelabel, Landing Page, Auth & Deploy

**Date:** 2026-06-10
**Status:** Approved (proceeding to build)

## Goal

Take the existing `greensoft-leadgen` static dashboard, rebrand it end-to-end as
**Nova Analytics**, add a public landing page with a working Supabase
login/signup flow, and deploy the whole thing to a live HTTPS URL on Vercel.

## Positioning

Nova Analytics is a **lead-intelligence / sales-signal analytics** product. This
keeps the landing page coherent with what the dashboard actually displays
(companies, lead scores, hiring signals, AI-drafted outreach) — only names and
styling change, no rewrite of column semantics.

## Architecture

Dependency-free **static site** (no build step) deployed to Vercel. Existing
dashboard already uses Alpine.js + Tailwind via CDN, so we keep that approach for
maximum demo stability.

```
web/                     # Vercel root directory (static)
  index.html             # Landing: hero, features, CTA -> /signup
  login.html             # Supabase email/password sign-in
  signup.html            # Supabase email/password sign-up
  dashboard.html         # Rebranded Alpine dashboard (auth-gated)
  assets/
    brand.css            # Nova brand tokens + shared styles
    logo.svg             # Nova Analytics wordmark + star mark
    nova-mark.svg        # Standalone star/nova icon
    favicon.svg
  js/
    config.js            # Public Supabase URL + anon key (safe to commit)
    supabaseClient.js    # Creates the shared Supabase client (CDN ESM)
    auth.js             # login/signup handlers + requireAuth() guard + logout
    dashboard.js         # Former app.js, rebranded
  data/
    leads.json           # Sample Nova Analytics data
  vercel.json            # Clean-URL rewrites (/login -> /login.html etc.)
```

## Authentication (Supabase)

- Email/password via `@supabase/supabase-js` (CDN ESM). Anon key + URL are
  public-safe and committed in `js/config.js`.
- `signup.html`: `supabase.auth.signUp()` -> on success redirect to `/dashboard`.
- `login.html`: `supabase.auth.signInWithPassword()` -> redirect to `/dashboard`.
- `dashboard.html`: `requireAuth()` runs on load — `getSession()`; if no session,
  redirect to `/login`. Header shows signed-in email + **Log out** button.
- Supabase project config: **disable email confirmation** (or pre-seed a confirmed
  `admin@novaanalytics.io`) so signup -> immediate login works and reviewers get
  working test credentials.

**Known limitation (documented):** client-side auth gates the UI, not the static
`leads.json` itself. Production hardening = serve leads from a Supabase table with
Row-Level Security. Out of scope for this demo.

## Brand

- **Name:** Nova Analytics. **Sample user:** `admin@novaanalytics.io`.
- **Palette:** primary indigo→violet (`#6366F1`→`#7C3AED`), accent electric cyan
  (`#22D3EE`), dark hero (`#0B1020` / slate-950). Light dashboard surface retained.
- **Logo:** "nova" star/burst mark + wordmark, SVG. Matching SVG favicon.
- Replace every visible "Greensoft" reference, including strings inside
  `leads.json` (`outreach_message.body`, `score_rationale`) that render in the
  expanded dashboard row.

## Whitelabel scope (beyond visible UI, for a clean fork)

Rename "Greensoft" → "Nova Analytics" across README, Python scraper, prompts, and
tests. Fix the tests that assert on those strings (`test_message.py`,
`test_pipeline.py`, `test_message_linter.py`) so `pytest` stays green — doubles as
the "meaningful tests" extra credit. The Python pipeline is NOT deployed (Vercel
serves only `web/`); the demo uses the committed sample data.

## Landing page

Responsive, mobile-first, single page:
1. **Hero** — Nova wordmark, headline, sub-headline, primary CTA "Get started"
   (-> /signup), secondary "Log in".
2. **Features / benefits** — 3–4 cards mapped to real capabilities: AI lead
   scoring, hiring-signal detection, auto-drafted outreach, daily refresh.
3. **CTA band** — repeat call-to-action into signup.
4. **Footer** — © Nova Analytics, year. No "Greensoft" anywhere.

## Deployment

- **Vercel**, root directory = `web/`, no build command (static). HTTPS automatic.
- Git push -> auto-deploy (built-in CI/CD, extra credit).
- `vercel.json` provides clean-URL rewrites and security headers.
- Old `docs/runbooks/cloudflare-deploy.md` replaced with `vercel-deploy.md`.

## Deliverables

- [ ] Rebranded static site (landing + auth + dashboard) under `web/`
- [ ] Supabase auth wired, test creds working
- [ ] Rebranded repo + green `pytest`
- [ ] Updated `README.md` (stack, setup, env vars, test creds, limitations)
- [ ] Live Vercel HTTPS URL
- [ ] Video walkthrough script/notes
- [ ] Behavioral Questionnaire draft
- [ ] User-bound runbook: Supabase project, GitHub repo, Vercel connect

## Account-bound steps handed to the user

Creating the Supabase project, creating the personal GitHub repo, and connecting
Vercel — provided as click-by-click instructions (`gh` CLI not installed locally).
