import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Awaitable, Callable
from datetime import date

from scraper.models import SeedCompany, Lead, Company, Job, OutreachMessage
from scraper.storage import LeadStore, SeenStore
from scraper.ai.filter import FilterResult
from scraper.ai.score import ScoreResult

log = logging.getLogger(__name__)

QA_KEYWORDS = ["qa", "quality assurance", "test", "sdet"]


@dataclass
class PipelineSummary:
    companies_scraped: int
    new_postings: int
    candidates_after_filter: int
    leads_written: int
    hot_count: int   # score > 70
    warm_count: int  # 50-70
    cold_count: int  # <50


def _is_qa_role(title: str) -> bool:
    t = title.lower()
    return any(kw in t for kw in QA_KEYWORDS)


async def run_pipeline(
    *,
    seed_companies: list[SeedCompany],
    leads_path: Path,
    seen_path: Path,
    fetch_all: Callable[..., Awaitable[dict[str, list[Job]]]],
    filter_fn: Callable[[Job], FilterResult],
    score_fn: Callable[[Company, list[Job]], ScoreResult],
    message_fn: Callable[..., OutreachMessage],
) -> PipelineSummary:
    leads_store = LeadStore(leads_path)
    seen_store = SeenStore(seen_path)

    # Phase 1: scrape
    company_jobs = await fetch_all(seed_companies)

    new_postings = 0
    candidate_postings = 0
    leads_out: list[Lead] = []
    hot = warm = cold = 0

    for seed in seed_companies:
        jobs = company_jobs.get(seed.name, [])
        # idempotency: skip already-seen jobs
        new_jobs = []
        for j in jobs:
            lead_id = f"{seed.ats_provider}:{seed.ats_slug}:{j.id}"
            if seen_store.has_seen(lead_id):
                continue
            seen_store.mark_seen(lead_id)
            new_jobs.append(j)
        new_postings += len(new_jobs)
        if not new_jobs:
            continue

        # Phase 2: per-job filter (Haiku)
        candidates: list[Job] = []
        for j in new_jobs:
            res = filter_fn(j)
            if res.is_lead_candidate:
                candidates.append(j)
        candidate_postings += len(candidates)
        if not candidates:
            continue

        # Phase 3: per-company aggregate score + message (Sonnet)
        company = Company(
            name=seed.name,
            ats_provider=seed.ats_provider,
            ats_slug=seed.ats_slug,
            homepage=seed.homepage,
            linkedin=seed.linkedin,
            industry=seed.industry,
            country="US",
        )
        score = score_fn(company, candidates)
        message = message_fn(company, candidates, score.breakdown, score.rationale)

        first_job_id = candidates[0].id
        lead = Lead(
            lead_id=f"{seed.ats_provider}:{seed.ats_slug}:{first_job_id}",
            company=company,
            active_jobs=candidates,
            qa_jobs_count=sum(1 for j in candidates if _is_qa_role(j.title)),
            all_it_jobs_count=len(candidates),
            lead_score=score.total,
            score_breakdown=score.breakdown,
            score_rationale=score.rationale,
            outreach_message=message,
            status="new",
            first_seen=date.today(),
        )
        leads_out.append(lead)
        if score.total > 70:
            hot += 1
        elif score.total >= 50:
            warm += 1
        else:
            cold += 1

    leads_store.upsert(leads_out)
    return PipelineSummary(
        companies_scraped=len(seed_companies),
        new_postings=new_postings,
        candidates_after_filter=candidate_postings,
        leads_written=len(leads_out),
        hot_count=hot,
        warm_count=warm,
        cold_count=cold,
    )
