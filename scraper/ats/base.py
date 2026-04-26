import asyncio
import logging
from abc import ABC, abstractmethod
import httpx
from scraper.models import Job, SeedCompany


class ATSClient(ABC):
    """Fetches active job postings for a single company on a single ATS provider."""
    provider: str

    def __init__(self, http: httpx.AsyncClient | None = None):
        self.http = http or httpx.AsyncClient(timeout=30.0)

    @abstractmethod
    async def fetch_jobs(self, company: SeedCompany) -> list[Job]:
        """Return all currently-active jobs for the given company."""
        ...

    async def aclose(self) -> None:
        await self.http.aclose()


log = logging.getLogger(__name__)


async def fetch_all_companies(
    companies: list[SeedCompany],
    clients: dict[str, ATSClient],
    concurrency: int = 10,
) -> dict[str, list]:
    """
    Fetch jobs for every company through its respective ATS client, with bounded concurrency.
    Returns {company_name: [Job, ...]}. Per-company failures are swallowed and logged.
    """
    sem = asyncio.Semaphore(concurrency)

    async def _one(company: SeedCompany):
        client = clients.get(company.ats_provider)
        if client is None:
            log.warning("No client for provider %s", company.ats_provider)
            return company.name, []
        async with sem:
            try:
                jobs = await client.fetch_jobs(company)
                return company.name, jobs
            except Exception as e:
                log.warning("fetch failed for %s (%s): %s", company.name, company.ats_provider, e)
                return company.name, []

    pairs = await asyncio.gather(*(_one(c) for c in companies))
    return dict(pairs)
