# Nova Analytics

**Lead intelligence, refreshed daily.** Nova Analytics reads live hiring signals
across the market, scores every company with AI, and hands revenue teams
sales-ready leads with outreach already drafted.

This repository contains:

- A polished, responsive **marketing landing page** with a working
  **login / signup** flow (Supabase auth).
- A whitelabeled, auth-gated **lead dashboard** (the product).
- The **AI pipeline** (Python) that scrapes ATS feeds, scores companies with
  Claude, and drafts outreach — the engine behind the data.

> **Live demo:** <https://nova-analytics-sigma.vercel.app>
> **Test login:** `admin@novaanalytics.io` / `NovaDemo2026!`

---

## Tech stack

| Layer            | Choice                                                                 |
| ---------------- | --------------------------------------------------------------------- |
| Frontend         | Static HTML + [Alpine.js](https://alpinejs.dev) + Tailwind (CDN) — **no build step** |
| Auth             | [Supabase](https://supabase.com) email/password (`@supabase/supabase-js`) |
| Hosting          | [Vercel](https://vercel.com) static deploy, HTTPS, push-to-deploy CI/CD |
| Data pipeline    | Python 3.11, [Anthropic Claude](https://www.anthropic.com) API        |
| Tests            | `pytest` (pipeline) + manual E2E of the auth flow                     |

**Why this architecture:** the dashboard is a dependency-free static site, so it
deploys anywhere instantly and is rock-solid to demo. Supabase provides real,
managed authentication with almost no code, and Vercel gives free HTTPS plus
automatic deploys on every push.

---

## Project structure

```
web/                     # The deployable static site (Vercel root directory)
  index.html             # Landing page: hero, features, how-it-works, CTA
  login.html             # Supabase sign-in
  signup.html            # Supabase sign-up
  dashboard.html         # Auth-gated lead dashboard
  assets/                # brand.css, nova-mark.svg, favicon.svg
  js/
    config.js            # Public Supabase URL + anon key (safe to commit)
    auth.js              # Auth layer (Supabase + demo fallback)
    dashboard.js         # Dashboard logic (Alpine component)
  data/leads.json        # Sample lead data served by the dashboard
  vercel.json            # Clean-URL routing + security headers

scraper/                 # Python AI pipeline (the data engine)
  ats/                   # Greenhouse + Lever feed adapters
  ai/                    # Claude client, filter, score, message, linter
  pipeline.py            # Orchestration
tests/                   # pytest suite for the pipeline
devserver.py             # Local dev server that mirrors Vercel clean URLs
docs/                    # Specs + deployment runbooks
```

---

## Run the site locally

The site is fully static. Use the included dev server (it mirrors Vercel's
clean-URL routing, so `/login` works the same locally as in production):

```bash
python devserver.py            # serves web/ at http://127.0.0.1:4321
```

Open <http://127.0.0.1:4321>. Until you configure Supabase (below), the app runs
in **demo mode** — auth is emulated in your browser's localStorage so the full
landing → login → dashboard flow is demonstrable with zero backend.

**Demo credentials (work out of the box in demo mode):**

```
email:    admin@novaanalytics.io
password: NovaDemo2026!
```

---

## Environment variables / configuration

The only configuration the frontend needs is the **public** Supabase URL and anon
key, in [`web/js/config.js`](web/js/config.js):

```js
export const SUPABASE_URL = "https://YOUR-PROJECT.supabase.co";
export const SUPABASE_ANON_KEY = "YOUR-ANON-KEY";
```

These two values are **public by design** — Supabase's anon key is meant to ship
in client code; data is protected by row-level security, not by hiding the key.
When both are filled in, real Supabase auth activates automatically and the demo
fallback turns off.

The Python pipeline uses one secret, in a local `.env` (never committed):

```
ANTHROPIC_API_KEY=sk-ant-...      # required to run the scraper
LEADGEN_DRY_RUN=false             # optional
LEADGEN_LOG_LEVEL=INFO            # optional
```

See [`docs/runbooks/supabase-setup.md`](docs/runbooks/supabase-setup.md) and
[`docs/runbooks/vercel-deploy.md`](docs/runbooks/vercel-deploy.md) for the
click-by-click setup.

---

## Deployment (Vercel)

1. Push this repo to GitHub.
2. In Vercel → **New Project** → import the repo.
3. Set **Root Directory** to `web`. Framework preset: **Other**. No build command.
4. Deploy. Vercel gives you an HTTPS URL and redeploys on every push.

Full walkthrough (with Supabase): [`docs/runbooks/vercel-deploy.md`](docs/runbooks/vercel-deploy.md).

---

## Run the data pipeline (optional, consumes API tokens)

```bash
python -m venv .venv
.venv\Scripts\activate            # source .venv/bin/activate on macOS/Linux
pip install -e ".[dev]"
cp .env.example .env              # add ANTHROPIC_API_KEY
pytest                            # run the test suite
python -m scraper.main           # run the pipeline -> data/leads.json
```

To serve freshly generated data in the dashboard, copy the pipeline output into
`web/data/leads.json` (or point the pipeline's output path there).

---

## Tests

```bash
pip install -e ".[dev]"
pytest
```

The suite covers the ATS adapters, AI filtering/scoring/message generation, the
message quality linter, storage idempotency, and the pipeline orchestration.

---

## Known limitations & next steps

- **Client-side auth gating.** The dashboard checks the Supabase session in the
  browser and redirects if absent. This gates the **UI**, not the static
  `leads.json` file itself. Production hardening: store leads in a Supabase table
  with **row-level security** and fetch them with the authenticated client so the
  data is never publicly readable.
- **Sample data.** The deployed dashboard serves a curated `leads.json` sample.
  Wiring the live daily pipeline output into `web/data/` is a small follow-up.
- **Email confirmation.** For frictionless reviewer access, disable email
  confirmation in Supabase (or pre-seed a confirmed user) so signup → login is
  instant. See the Supabase runbook.
- **With more time:** add Playwright E2E tests for the auth flow, a custom
  domain, and product analytics (PostHog/Plausible).
