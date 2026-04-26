import pytest
from unittest.mock import AsyncMock
from scraper.ats.base import fetch_all_companies
from scraper.models import SeedCompany, Job, Company
from datetime import date


def make_job(id="1", title="QA"):
    return Job(
        id=id, title=title, url="https://x/y",
        location="Remote", remote_friendly=True,
        posted_date=date.today(), tech_stack=[],
    )


@pytest.mark.asyncio
async def test_fetch_all_dispatches_to_correct_client():
    gh_client = AsyncMock()
    gh_client.fetch_jobs.return_value = [make_job("g1")]
    gh_client.aclose = AsyncMock()
    lever_client = AsyncMock()
    lever_client.fetch_jobs.return_value = [make_job("l1")]
    lever_client.aclose = AsyncMock()

    companies = [
        SeedCompany(name="A", ats_provider="greenhouse", ats_slug="a"),
        SeedCompany(name="B", ats_provider="lever", ats_slug="b"),
    ]
    results = await fetch_all_companies(
        companies,
        clients={"greenhouse": gh_client, "lever": lever_client},
    )
    assert len(results) == 2
    assert results["A"][0].id == "g1"
    assert results["B"][0].id == "l1"


@pytest.mark.asyncio
async def test_fetch_all_isolates_failures():
    gh_client = AsyncMock()
    gh_client.fetch_jobs.side_effect = Exception("boom")
    gh_client.aclose = AsyncMock()
    lever_client = AsyncMock()
    lever_client.fetch_jobs.return_value = [make_job("ok")]
    lever_client.aclose = AsyncMock()

    companies = [
        SeedCompany(name="A", ats_provider="greenhouse", ats_slug="a"),
        SeedCompany(name="B", ats_provider="lever", ats_slug="b"),
    ]
    results = await fetch_all_companies(
        companies,
        clients={"greenhouse": gh_client, "lever": lever_client},
    )
    assert results["A"] == []  # failure didn't crash anything
    assert len(results["B"]) == 1
