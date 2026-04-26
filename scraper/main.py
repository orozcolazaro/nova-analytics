import argparse
import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

from scraper.models import SeedCompany
from scraper.ats.base import fetch_all_companies
from scraper.ats.greenhouse import GreenhouseClient
from scraper.ats.lever import LeverClient
from scraper.ai.filter import filter_job
from scraper.ai.score import score_company
from scraper.ai.message import generate_message
from scraper.pipeline import run_pipeline


def _load_seed(path: Path) -> list[SeedCompany]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return [SeedCompany.model_validate(item) for item in raw]


async def _amain(args):
    load_dotenv()
    logging.basicConfig(
        level=os.environ.get("LEADGEN_LOG_LEVEL", "INFO"),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    log = logging.getLogger("leadgen")

    seed = _load_seed(Path(args.seed))
    log.info("Loaded %d seed companies", len(seed))

    gh = GreenhouseClient()
    lever = LeverClient()
    clients = {"greenhouse": gh, "lever": lever}

    async def _fetch_all(seed_companies):
        return await fetch_all_companies(seed_companies, clients=clients, concurrency=10)

    try:
        summary = await run_pipeline(
            seed_companies=seed,
            leads_path=Path(args.leads),
            seen_path=Path(args.seen),
            fetch_all=_fetch_all,
            filter_fn=filter_job,
            score_fn=score_company,
            message_fn=generate_message,
        )
    finally:
        await gh.aclose()
        await lever.aclose()

    print(json.dumps({
        "timestamp": datetime.utcnow().isoformat(),
        "companies_scraped": summary.companies_scraped,
        "new_postings": summary.new_postings,
        "candidates_after_filter": summary.candidates_after_filter,
        "leads_written": summary.leads_written,
        "hot": summary.hot_count,
        "warm": summary.warm_count,
        "cold": summary.cold_count,
    }, indent=2))


def main():
    parser = argparse.ArgumentParser(prog="leadgen")
    parser.add_argument("--seed", default="seed/companies.json")
    parser.add_argument("--leads", default="data/leads.json")
    parser.add_argument("--seen", default="data/seen.json")
    parser.add_argument("--dry-run", action="store_true",
                        help="Log what would happen, do not call paid APIs")
    args = parser.parse_args()
    if args.dry_run:
        os.environ["LEADGEN_DRY_RUN"] = "true"
    asyncio.run(_amain(args))


if __name__ == "__main__":
    main()
