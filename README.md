# Greensoft Leadgen

AI-driven B2B lead generation for Greensoft Technologies. Daily cron scrapes US ATS feeds (Greenhouse + Lever), classifies and scores prospects with Claude, generates personalized outreach copy, and serves the result at https://leads.greensofts.org.

Spec: `docs/superpowers/specs/2026-04-25-greensoft-leadgen-design.md`
Plan: `docs/superpowers/plans/2026-04-25-greensoft-leadgen-phase1.md`
Deploy: `docs/runbooks/cloudflare-deploy.md`

## Local development

```bash
python -m venv .venv
source .venv/bin/activate         # .venv\Scripts\activate on Windows
pip install -e ".[dev]"
cp .env.example .env              # add ANTHROPIC_API_KEY
pytest                            # all unit tests should pass
```

## Run the pipeline locally (consumes API tokens)

```bash
python -m scraper.main
```

Outputs:
- `data/leads.json` — full lead list
- `data/seen.json` — idempotency state
- stdout — JSON summary

## Add a company to the seed list

Edit `seed/companies.json`:

```json
{
  "name": "MyCompany",
  "ats_provider": "greenhouse",
  "ats_slug": "mycompany",
  "industry": "Fintech"
}
```

Verify the slug works:

```bash
curl -s https://boards-api.greenhouse.io/v1/boards/mycompany/jobs | head
```

## Adjust scoring weights

Weights live in `scraper/ai/prompts/score.txt` (model-facing instructions) and `scraper/ai/score.py` (CAPS dict, used to clamp model output). Change both together.

## Add a partner (Cloudflare Access user)

1. Cloudflare → Zero Trust → Access → Applications → `leads.greensofts.org`
2. Edit policy → add their Gmail address to "Include emails"
3. Save. They can immediately log in with magic link.

## Daily cron failure

GitHub auto-emails the repo admin. To re-run manually:
- GitHub → Actions → Daily Leadgen → Run workflow
- Or `gh workflow run daily-leadgen.yml`
