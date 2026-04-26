import pytest
from datetime import date
from unittest.mock import AsyncMock, patch, MagicMock
from scraper.pipeline import run_pipeline, PipelineSummary
from scraper.models import SeedCompany, Job, Company, ScoreBreakdown, OutreachMessage
from scraper.ai.filter import FilterResult
from scraper.ai.score import ScoreResult


def make_job(id_="1", title="QA Engineer"):
    return Job(
        id=id_, title=title, url="https://x/y",
        location="Remote - US", remote_friendly=True,
        posted_date=date.today(), tech_stack=[],
        raw_description="..."
    )


@pytest.mark.asyncio
async def test_pipeline_happy_path(tmp_path):
    seed = [SeedCompany(name="Acme", ats_provider="greenhouse", ats_slug="acme")]
    company_jobs = {"Acme": [make_job("1", "Senior QA"), make_job("2", "DevOps")]}

    fetch_all = AsyncMock(return_value=company_jobs)
    filter_fn = MagicMock(return_value=FilterResult(
        is_lead_candidate=True,
        extracted={"role": "QA", "seniority": "senior", "location": "Remote", "remote_friendly": True, "urgency_signal": "low"},
    ))
    score_fn = MagicMock(return_value=ScoreResult(
        breakdown=ScoreBreakdown(qa_relevance=22, company_size=18, urgency=14, nearshore_fit=18, deal_size=12),
        rationale="test rationale",
    ))
    message_fn = MagicMock(return_value=OutreachMessage(
        subject="Helping Acme close 2 IT roles",
        body="...short body... 15-min call?\n\n[Your name]\nGreensoft Technologies",
    ))

    summary = await run_pipeline(
        seed_companies=seed,
        leads_path=tmp_path / "leads.json",
        seen_path=tmp_path / "seen.json",
        fetch_all=fetch_all,
        filter_fn=filter_fn,
        score_fn=score_fn,
        message_fn=message_fn,
    )
    assert isinstance(summary, PipelineSummary)
    assert summary.companies_scraped == 1
    assert summary.new_postings == 2
    assert summary.leads_written == 1
    # ensure filter called for each job, score called once at company level
    assert filter_fn.call_count == 2
    assert score_fn.call_count == 1


@pytest.mark.asyncio
async def test_pipeline_skips_seen_jobs(tmp_path):
    seen_path = tmp_path / "seen.json"
    seen_path.write_text('{"greenhouse:acme:1": "2026-04-20"}')
    seed = [SeedCompany(name="Acme", ats_provider="greenhouse", ats_slug="acme")]
    company_jobs = {"Acme": [make_job("1"), make_job("2")]}
    fetch_all = AsyncMock(return_value=company_jobs)
    filter_fn = MagicMock(return_value=FilterResult(is_lead_candidate=True, extracted={}))
    score_fn = MagicMock(return_value=ScoreResult(
        breakdown=ScoreBreakdown(qa_relevance=10, company_size=10, urgency=10, nearshore_fit=10, deal_size=5),
        rationale="r",
    ))
    message_fn = MagicMock(return_value=OutreachMessage(subject="s", body="b? [Your name]\nGreensoft Technologies"))
    summary = await run_pipeline(
        seed_companies=seed,
        leads_path=tmp_path / "leads.json",
        seen_path=seen_path,
        fetch_all=fetch_all,
        filter_fn=filter_fn,
        score_fn=score_fn,
        message_fn=message_fn,
    )
    # job id=1 was already seen; only job id=2 should be filtered
    assert filter_fn.call_count == 1
