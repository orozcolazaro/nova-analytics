# Cloudflare Pages + Access deploy runbook

One-time setup. Estimated time: 15 min.

## Prerequisites
- Domain `greensofts.org` registered in Cloudflare (already done)
- GitHub repo `greensofttech-usa-mx/greensoft-leadgen` exists and is private
- You have admin access to both

## Step 1 — Create a Cloudflare Pages project

1. Cloudflare dashboard → Workers & Pages → Create application → Pages → Connect to Git
2. Authorize Cloudflare GitHub App if not already done; grant access to the `greensofttech-usa-mx` org
3. Select the `greensoft-leadgen` repo
4. Project name: `greensoft-leadgen`
5. Production branch: `main`
6. Build settings:
   - Framework preset: **None**
   - Build command: *(leave blank)*
   - Build output directory: `dashboard`
7. Click **Save and Deploy**. First deploy will succeed even before any cron runs (it'll just lack data).

## Step 2 — Custom domain

1. In the new Pages project → Custom domains → **Set up a custom domain**
2. Enter `leads.greensofts.org`
3. Cloudflare auto-creates the CNAME record in your zone (because the registrar is Cloudflare)
4. Wait ~30 sec for HTTPS cert to provision

## Step 3 — Cloudflare Access (auth)

1. Cloudflare → Zero Trust → Access → Applications → Add application → Self-hosted
2. App name: `Greensoft Leads`
3. Application domain: `leads.greensofts.org`
4. Identity providers: enable **One-time PIN** (default; sends magic links)
5. Click **Next**
6. Policy:
   - Action: **Allow**
   - Configure rules → Include → **Emails** → list each partner Gmail address one per row
7. Save policy
8. Save application
9. Test: open an incognito browser and visit `https://leads.greensofts.org`. You should see Cloudflare's login screen.

## Step 4 — Verify the cron workflow

1. GitHub → Repo → Settings → Secrets and variables → Actions → New repository secret
2. Name: `ANTHROPIC_API_KEY`, Value: your Anthropic key
3. Trigger a manual run: GitHub → Actions → Daily Leadgen → Run workflow
4. Wait ~5 min. Check the Actions log; the run should commit changes to `data/leads.json` and `dashboard/data/leads.json`
5. Cloudflare Pages auto-redeploys (~1 min after commit). Refresh `leads.greensofts.org` and your leads should appear.

## Adding a new partner

Cloudflare → Zero Trust → Access → Applications → `Greensoft Leads` → Policies → Allow → Add their email. Save. They can log in immediately.
