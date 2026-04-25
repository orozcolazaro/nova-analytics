from datetime import date, datetime
import re
from scraper.ats.base import ATSClient
from scraper.models import Job, SeedCompany

API_TEMPLATE = "https://boards-api.greenhouse.io/v1/boards/{slug}/jobs"

# Tech keywords we care about for tech_stack extraction; expanded over time.
TECH_KEYWORDS = [
    "Selenium", "Cypress", "Playwright", "Postman", "k6", "JMeter",
    "Python", "TypeScript", "JavaScript", "Go", "Java", "Ruby",
    "AWS", "GCP", "Azure", "Kubernetes", "Docker", "Terraform",
    "React", "Vue", "Node", "Django", "Flask", "FastAPI",
    "PostgreSQL", "MySQL", "MongoDB", "Redis", "Kafka",
]


def _parse_date(iso: str | None) -> date:
    if not iso:
        return date.today()
    return datetime.fromisoformat(iso.replace("Z", "+00:00")).date()


def _extract_tech_stack(content: str) -> list[str]:
    if not content:
        return []
    found = set()
    for kw in TECH_KEYWORDS:
        if re.search(rf"\b{re.escape(kw)}\b", content, re.IGNORECASE):
            found.add(kw)
    return sorted(found)


def _is_remote(location: str) -> bool:
    if not location:
        return False
    return bool(re.search(r"\bremote\b|\banywhere\b|\bworldwide\b", location, re.IGNORECASE))


class GreenhouseClient(ATSClient):
    provider = "greenhouse"

    async def fetch_jobs(self, company: SeedCompany) -> list[Job]:
        url = API_TEMPLATE.format(slug=company.ats_slug)
        try:
            resp = await self.http.get(url, params={"content": "true"})
        except Exception:
            return []
        if resp.status_code != 200:
            return []
        payload = resp.json()
        jobs: list[Job] = []
        for raw in payload.get("jobs", []):
            try:
                content = raw.get("content") or ""
                # Greenhouse "content" is HTML-encoded; strip rough tags
                content_text = re.sub(r"<[^>]+>", " ", content)
                location = (raw.get("location") or {}).get("name") or ""
                jobs.append(Job(
                    id=str(raw["id"]),
                    title=raw["title"],
                    url=raw["absolute_url"],
                    location=location,
                    remote_friendly=_is_remote(location),
                    posted_date=_parse_date(raw.get("updated_at")),
                    tech_stack=_extract_tech_stack(content_text),
                    raw_description=content_text[:8000],  # cap for IA token budget
                ))
            except (KeyError, ValueError):
                continue
        return jobs
