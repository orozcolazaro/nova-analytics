# Deploy to Vercel

The Nova Analytics site is a static site in the `web/` directory. Vercel serves
it with free HTTPS and redeploys on every git push (that's your CI/CD).

## Prerequisites

- The repo is pushed to GitHub (see the main README / handoff notes).
- Supabase configured ([`supabase-setup.md`](supabase-setup.md)) for real auth —
  optional; demo mode works without it.

## Steps

1. Go to <https://vercel.com> → sign in with GitHub.
2. **Add New… → Project** → import your `nova-analytics` repo.
3. Configure:
   - **Framework Preset:** `Other`
   - **Root Directory:** click **Edit** → select **`web`**  ← important
   - **Build Command:** leave empty (no build)
   - **Output Directory:** leave default
4. Click **Deploy**. In ~30 seconds you get a URL like
   `https://nova-analytics.vercel.app` with HTTPS already enabled.

The `web/vercel.json` in the repo enables clean URLs (`/login`, `/dashboard`) and
adds security headers automatically.

## Continuous deployment

Vercel watches your GitHub repo. Every push to the default branch triggers a new
production deploy; pull requests get preview URLs. No extra configuration needed.

The separate GitHub Actions workflow (`.github/workflows/ci.yml`) runs lint +
tests on each push, so deploys are gated on a green test suite.

## Custom domain (optional)

Project → **Settings → Domains** → add your domain and follow the DNS
instructions. HTTPS is provisioned automatically.

## Verify

- Visit your URL → landing page loads over HTTPS.
- `/signup` → create an account → redirected into the dashboard.
- `/login` with the reviewer credentials → dashboard.
- Visiting `/dashboard` while logged out → redirected to `/login`.
