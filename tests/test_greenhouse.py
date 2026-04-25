import json
from pathlib import Path
import pytest
import respx
from httpx import Response
from scraper.ats.greenhouse import GreenhouseClient
from scraper.models import SeedCompany


FIXTURE = Path(__file__).parent / "fixtures" / "greenhouse_airtable.json"


@pytest.fixture
def fixture_payload() -> dict:
    return json.loads(FIXTURE.read_text())


@pytest.mark.asyncio
@respx.mock
async def test_greenhouse_returns_jobs(fixture_payload):
    respx.get("https://boards-api.greenhouse.io/v1/boards/airtable/jobs").mock(
        return_value=Response(200, json=fixture_payload)
    )
    client = GreenhouseClient()
    jobs = await client.fetch_jobs(SeedCompany(name="Airtable", ats_provider="greenhouse", ats_slug="airtable"))
    await client.aclose()
    assert len(jobs) > 0
    j = jobs[0]
    assert j.id
    assert j.title
    assert str(j.url).startswith("http")


@pytest.mark.asyncio
@respx.mock
async def test_greenhouse_handles_404():
    respx.get("https://boards-api.greenhouse.io/v1/boards/nonexistent/jobs").mock(
        return_value=Response(404, json={"error": "not found"})
    )
    client = GreenhouseClient()
    jobs = await client.fetch_jobs(SeedCompany(name="X", ats_provider="greenhouse", ats_slug="nonexistent"))
    await client.aclose()
    assert jobs == []
