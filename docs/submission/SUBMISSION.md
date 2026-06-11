# Nova Analytics — Submission

## Links (fill in as you complete the account-bound steps)

| Item                 | Link                                                        |
| -------------------- | ----------------------------------------------------------- |
| GitHub repo          | <https://github.com/orozcolazaro/nova-analytics>            |
| Live deployment URL  | <https://nova-analytics-sigma.vercel.app> (HTTPS)           |
| Video walkthrough    | `<YouTube unlisted / Loom link — add after recording>`      |

## Test credentials

```
email:    admin@novaanalytics.io
password: NovaDemo2026!
```

- In **demo mode** (before Supabase is configured) these work out of the box.
- In **Supabase mode**, create this user once (see `docs/runbooks/supabase-setup.md`,
  step 5) so reviewers can log in without signing up.

## What was built

- **Whitelabel:** every "Greensoft" reference removed (UI, sample data, Python,
  prompts, tests, docs). New Nova Analytics brand — nova-spectrum gradient,
  Fraunces/Sora/JetBrains Mono type, SVG mark + favicon.
- **Landing page:** responsive (hero, features, how-it-works, CTA, footer),
  mobile-friendly, dark "signal in the dark" aesthetic.
- **Auth:** Supabase email/password login + signup; successful auth redirects to
  the dashboard; the dashboard is guarded (logged-out users are redirected to
  `/login`); logout works. A localStorage demo fallback keeps the flow working
  before Supabase is configured.
- **Dashboard:** the original lead dashboard, rebranded and behind auth.
- **Deploy:** static site on Vercel, HTTPS, push-to-deploy CI/CD.
- **Tests/CI:** `pytest` suite green (36 passed, 5 external-API tests skipped);
  GitHub Actions runs ruff + pytest on every push.
- **Development process:** built end-to-end with Claude Code — see
  [`DEVELOPMENT-PROCESS.md`](DEVELOPMENT-PROCESS.md) for the methodology, key
  prompts, the verification approach, and a production bug caught and fixed.

## Remaining account-bound steps (need your accounts)

1. **GitHub** — create a public repo `nova-analytics` on your account and push
   (see handoff notes / `git remote add origin … && git push`).
2. **Supabase** — `docs/runbooks/supabase-setup.md` (~5 min) for real auth.
3. **Vercel** — `docs/runbooks/vercel-deploy.md` (~2 min), Root Directory = `web`.
4. **Video** — record 5–10 min using `docs/submission/VIDEO-SCRIPT.md`.
5. **Behavioral questionnaire** — fill in the provided template.

## Known limitations & what I'd improve with more time

- **Client-side auth gating** protects the UI, not the static `leads.json`.
  Production fix: serve leads from a Supabase table with row-level security.
- **Sample data** is curated; wiring the live daily pipeline output into
  `web/data/` is a small follow-up.
- **With more time:** Playwright E2E tests for the auth flow, a custom domain,
  and product analytics (PostHog/Plausible).

## Tech decisions (the short version)

- **Static site, no build step** → maximum demo stability and instant deploys.
- **Supabase** → real managed auth with minimal code and a free tier.
- **Vercel** → free HTTPS + push-to-deploy, perfect for a static site.
- Kept the original Alpine.js dashboard rather than rewriting it in a framework —
  reusing working code beat a multi-day port for zero user-facing benefit.
