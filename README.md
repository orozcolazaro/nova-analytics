# Greensoft Leadgen

AI-driven B2B lead generation tool for Greensoft Technologies.

See `docs/superpowers/specs/2026-04-25-greensoft-leadgen-design.md` for the full design.

## Quickstart

    python -m venv .venv
    source .venv/bin/activate  # or .venv\Scripts\activate on Windows
    pip install -e ".[dev]"
    cp .env.example .env       # then fill ANTHROPIC_API_KEY
    pytest

## Run pipeline locally

    python -m scraper.main --dry-run
