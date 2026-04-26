import json
from pathlib import Path
import pytest
import respx
from httpx import Response
from scraper.ats.lever import LeverClient
from scraper.models import SeedCompany


FIXTURE = Path(__file__).parent / "fixtures" / "lever_example.json"


@pytest.fixture
def fixture_payload() -> list:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


@pytest.mark.asyncio
@respx.mock
async def test_lever_returns_jobs(fixture_payload):
    respx.get("https://api.lever.co/v0/postings/plaid").mock(
        return_value=Response(200, json=fixture_payload)
    )
    client = LeverClient()
    jobs = await client.fetch_jobs(SeedCompany(name="Plaid", ats_provider="lever", ats_slug="plaid"))
    await client.aclose()
    assert len(jobs) > 0
    j = jobs[0]
    assert j.id
    assert j.title


@pytest.mark.asyncio
@respx.mock
async def test_lever_handles_404():
    respx.get("https://api.lever.co/v0/postings/nope").mock(
        return_value=Response(404, json={})
    )
    client = LeverClient()
    jobs = await client.fetch_jobs(SeedCompany(name="X", ats_provider="lever", ats_slug="nope"))
    await client.aclose()
    assert jobs == []
