from datetime import date
import html
import logging
import re
import httpx
from scraper.ats.base import ATSClient
from scraper.ats.greenhouse import _extract_tech_stack, _is_remote
from scraper.models import Job, SeedCompany

log = logging.getLogger(__name__)

API_TEMPLATE = "https://api.lever.co/v0/postings/{slug}"


class LeverClient(ATSClient):
    provider = "lever"

    async def fetch_jobs(self, company: SeedCompany) -> list[Job]:
        url = API_TEMPLATE.format(slug=company.ats_slug)
        try:
            resp = await self.http.get(url, params={"mode": "json"})
        except httpx.RequestError as e:
            log.warning("lever fetch failed for %s: %s", company.ats_slug, e)
            return []
        if resp.status_code != 200:
            return []
        payload = resp.json()
        if not isinstance(payload, list):
            return []
        jobs: list[Job] = []
        for raw in payload:
            try:
                # Lever fields
                location = ((raw.get("categories") or {}).get("location")) or ""
                description_html = raw.get("descriptionPlain") or raw.get("description") or ""
                description_text = html.unescape(re.sub(r"<[^>]+>", " ", description_html))
                created_at_ms = raw.get("createdAt")
                posted = (
                    date.fromtimestamp(created_at_ms / 1000)
                    if isinstance(created_at_ms, (int, float))
                    else date.today()
                )
                jobs.append(Job(
                    id=str(raw["id"]),
                    title=raw["text"],
                    url=raw["hostedUrl"],
                    location=location,
                    remote_friendly=_is_remote(location),
                    posted_date=posted,
                    tech_stack=_extract_tech_stack(description_text),
                    raw_description=description_text[:8000],
                ))
            except (KeyError, ValueError):
                continue
        return jobs
