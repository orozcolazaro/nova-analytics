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
