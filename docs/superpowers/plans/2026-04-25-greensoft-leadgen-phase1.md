# Greensoft Leadgen Phase 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship a production MVP (`leads.greensofts.org`) that, every weekday at 07:00 CT, scrapes US ATS feeds (Greenhouse + Lever) for ~200 seed companies, scores each company as a B2B lead via Claude, generates personalized outreach messages, and serves the result through a Cloudflare-Pages dashboard protected by Cloudflare Access.

**Architecture:** GitHub Actions cron → Python async scraper → Claude Haiku 4.5 filter → Claude Sonnet 4.6 scoring + outreach copy → JSON committed to private repo → Cloudflare Pages auto-deploys → static dashboard reads JSON. Authentication via Cloudflare Access (allowlist of Gmail addresses).

**Tech Stack:** Python 3.11, `httpx` (async HTTP), `anthropic` SDK with prompt caching, Pydantic v2, pytest, Alpine.js, Tailwind CSS (CDN), GitHub Actions, Cloudflare Pages, Cloudflare Access.

**Reference spec:** `docs/superpowers/specs/2026-04-25-greensoft-leadgen-design.md`

---

## File Map

```
greensoft-leadgen/
├── .github/workflows/daily-leadgen.yml     # cron + scrape + IA + commit
├── pyproject.toml                          # deps + project metadata
├── .gitignore
├── .env.example
├── README.md
├── scraper/
│   ├── __init__.py
│   ├── models.py                           # Pydantic: Job, Company, Lead, etc.
│   ├── storage.py                          # leads.json / seen.json IO
│   ├── ats/
│   │   ├── __init__.py
│   │   ├── base.py                         # ATSClient abstract + dispatcher
│   │   ├── greenhouse.py                   # Greenhouse boards-api client
│   │   └── lever.py                        # Lever postings client
│   ├── ai/
│   │   ├── __init__.py
│   │   ├── client.py                       # Anthropic SDK wrapper w/ caching
│   │   ├── filter.py                       # Haiku 4.5 — is_lead_candidate
│   │   ├── score.py                        # Sonnet 4.6 — 5-signal scoring
│   │   ├── message.py                      # Sonnet 4.6 — outreach msg
│   │   ├── linter.py                       # validates generated messages
│   │   └── prompts/
│   │       ├── filter.txt
│   │       ├── score.txt
│   │       └── message.txt
│   ├── pipeline.py                         # orchestrator
│   └── main.py                             # CLI entrypoint
├── dashboard/
│   ├── index.html                          # Tailwind + Alpine SPA
│   ├── app.js                              # load + render + filter + sort
│   ├── styles.css                          # custom overrides
│   └── data/                               # symlink or copied at build
├── data/
│   ├── leads.json                          # output
│   └── seen.json                           # idempotency state
├── seed/
│   └── companies.json                      # ~200 US companies, Greenhouse/Lever slugs
└── tests/
    ├── conftest.py                         # pytest fixtures + mocks
    ├── fixtures/
    │   ├── greenhouse_airtable.json
    │   ├── lever_example.json
    │   └── golden_leads.json
    ├── test_models.py
    ├── test_storage.py
    ├── test_greenhouse.py
    ├── test_lever.py
    ├── test_filter.py
    ├── test_score.py
    ├── test_message_linter.py
    └── test_pipeline.py
```

---

## Task 1: Project skeleton — pyproject, gitignore, README

**Files:**
- Create: `pyproject.toml`, `.gitignore`, `.env.example`, `README.md`

- [ ] **Step 1: Create `pyproject.toml`**

```toml
[project]
name = "greensoft-leadgen"
version = "0.1.0"
description = "AI-driven B2B lead generation for Greensoft Technologies"
requires-python = ">=3.11"
dependencies = [
    "httpx>=0.27",
    "anthropic>=0.40",
    "pydantic>=2.6",
    "python-dotenv>=1.0",
    "tenacity>=8.2",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.23",
    "pytest-mock>=3.12",
    "respx>=0.21",
    "ruff>=0.4",
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
addopts = "-v --tb=short"

[tool.ruff]
line-length = 100
target-version = "py311"
```

- [ ] **Step 2: Create `.gitignore`**

```
__pycache__/
*.py[cod]
*.egg-info/
.venv/
.env
.pytest_cache/
.ruff_cache/
.coverage
htmlcov/
data/parse_errors.log
node_modules/
.DS_Store
```

- [ ] **Step 3: Create `.env.example`**

```
# Anthropic
ANTHROPIC_API_KEY=sk-ant-...

# Optional: override default cron behaviour for local dev
LEADGEN_DRY_RUN=false
LEADGEN_LOG_LEVEL=INFO
```

- [ ] **Step 4: Create `README.md` (minimal — full docs in Task 26)**

```markdown
# Greensoft Leadgen

AI-driven B2B lead generation tool for Greensoft Technologies.

See `docs/superpowers/specs/2026-04-25-greensoft-leadgen-design.md` for the full design.

## Quickstart

    python -m venv .venv
    source .venv/bin/activate  # or .venv\Scripts\activate on Windows
    pip install -e ".[dev]"
    cp .env.example .env       # then fill ANTHROPIC_API_KEY
    pytest

## Run pipeline locally

    python -m scraper.main --dry-run
```

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml .gitignore .env.example README.md
git commit -m "chore: bootstrap project metadata and gitignore"
```

---

## Task 2: Module skeleton — empty `__init__.py` files

**Files:**
- Create: `scraper/__init__.py`, `scraper/ats/__init__.py`, `scraper/ai/__init__.py`, `scraper/ai/prompts/.gitkeep`, `tests/__init__.py`, `tests/fixtures/.gitkeep`, `data/.gitkeep`, `seed/.gitkeep`

- [ ] **Step 1: Create empty package files**

```bash
mkdir -p scraper/ats scraper/ai/prompts tests/fixtures data seed dashboard/data
touch scraper/__init__.py scraper/ats/__init__.py scraper/ai/__init__.py
touch tests/__init__.py
touch scraper/ai/prompts/.gitkeep tests/fixtures/.gitkeep data/.gitkeep seed/.gitkeep
```

- [ ] **Step 2: Verify install works**

```bash
pip install -e ".[dev]"
pytest --collect-only
```

Expected: `pytest` reports `0 tests collected` with no import errors.

- [ ] **Step 3: Commit**

```bash
git add scraper/ tests/ data/ seed/ dashboard/
git commit -m "chore: scaffold package structure"
```

---

## Task 3: Pydantic data models

**Files:**
- Create: `scraper/models.py`, `tests/test_models.py`

- [ ] **Step 1: Write the failing tests in `tests/test_models.py`**

```python
import pytest
from datetime import date, datetime
from pydantic import ValidationError
from scraper.models import (
    Job, Company, Lead, ScoreBreakdown, OutreachMessage, SeedCompany
)


def test_seed_company_minimal():
    c = SeedCompany(name="Airtable", ats_provider="greenhouse", ats_slug="airtable")
    assert c.ats_provider == "greenhouse"


def test_seed_company_rejects_unknown_provider():
    with pytest.raises(ValidationError):
        SeedCompany(name="X", ats_provider="taleo", ats_slug="x")


def test_job_days_open_is_computed():
    j = Job(
        id="123", title="QA Engineer", url="https://x/y",
        location="Remote - US", remote_friendly=True,
        posted_date=date(2026, 4, 1), tech_stack=[]
    )
    # days_open computed against current date; just ensure non-negative
    assert j.days_open >= 0


def test_score_breakdown_total_capped_at_100():
    s = ScoreBreakdown(qa_relevance=25, company_size=20, urgency=20, nearshore_fit=20, deal_size=15)
    assert s.total == 100


def test_lead_id_format():
    company = Company(
        name="Airtable", ats_provider="greenhouse", ats_slug="airtable",
        homepage="https://airtable.com", country="US"
    )
    job = Job(
        id="5612345", title="QA", url="https://x", location="Remote",
        remote_friendly=True, posted_date=date.today(), tech_stack=[]
    )
    lead = Lead(
        lead_id="greenhouse:airtable:5612345",
        company=company, active_jobs=[job],
        qa_jobs_count=1, all_it_jobs_count=1,
        lead_score=80,
        score_breakdown=ScoreBreakdown(qa_relevance=20, company_size=15, urgency=15, nearshore_fit=15, deal_size=15),
        score_rationale="test",
        outreach_message=OutreachMessage(subject="test", body="test"),
        status="new",
        first_seen=date.today(),
    )
    assert lead.lead_id.startswith("greenhouse:")


def test_lead_score_bounds():
    company = Company(name="X", ats_provider="lever", ats_slug="x", country="US")
    with pytest.raises(ValidationError):
        Lead(
            lead_id="lever:x:1", company=company, active_jobs=[],
            qa_jobs_count=0, all_it_jobs_count=0,
            lead_score=150,  # invalid
            score_breakdown=ScoreBreakdown(qa_relevance=0, company_size=0, urgency=0, nearshore_fit=0, deal_size=0),
            score_rationale="", outreach_message=OutreachMessage(subject="x", body="y"),
            status="new", first_seen=date.today(),
        )
```

- [ ] **Step 2: Run tests, confirm they fail**

```bash
pytest tests/test_models.py -v
```

Expected: ImportError or ModuleNotFoundError for `scraper.models`.

- [ ] **Step 3: Implement `scraper/models.py`**

```python
from datetime import date, datetime
from typing import Literal
from pydantic import BaseModel, Field, computed_field, HttpUrl


ATSProvider = Literal["greenhouse", "lever", "occ", "computrabajo"]
LeadStatus = Literal["new", "contacted", "replied", "client", "dead", "needs_retry", "needs_review", "archived"]


class SeedCompany(BaseModel):
    name: str
    ats_provider: ATSProvider
    ats_slug: str
    homepage: HttpUrl | None = None
    linkedin: HttpUrl | None = None
    industry: str | None = None
    notes: str | None = None


class Job(BaseModel):
    id: str
    title: str
    url: HttpUrl
    location: str
    remote_friendly: bool
    posted_date: date
    tech_stack: list[str] = Field(default_factory=list)
    raw_description: str | None = None  # full JD for IA, not persisted to leads.json

    @computed_field
    @property
    def days_open(self) -> int:
        return max(0, (date.today() - self.posted_date).days)


class Company(BaseModel):
    name: str
    ats_provider: ATSProvider
    ats_slug: str
    homepage: HttpUrl | None = None
    linkedin: HttpUrl | None = None
    country: str = "US"
    size_estimate: str | None = None
    industry: str | None = None
    first_seen: date = Field(default_factory=date.today)


class ScoreBreakdown(BaseModel):
    qa_relevance: int = Field(ge=0, le=25)
    company_size: int = Field(ge=0, le=20)
    urgency: int = Field(ge=0, le=20)
    nearshore_fit: int = Field(ge=0, le=20)
    deal_size: int = Field(ge=0, le=15)

    @computed_field
    @property
    def total(self) -> int:
        return (
            self.qa_relevance + self.company_size + self.urgency
            + self.nearshore_fit + self.deal_size
        )


class OutreachMessage(BaseModel):
    subject: str
    body: str
    channel: Literal["email"] = "email"


class Lead(BaseModel):
    lead_id: str
    company: Company
    active_jobs: list[Job]
    qa_jobs_count: int
    all_it_jobs_count: int
    lead_score: int = Field(ge=0, le=100)
    score_breakdown: ScoreBreakdown
    score_rationale: str
    outreach_message: OutreachMessage
    status: LeadStatus = "new"
    first_seen: date = Field(default_factory=date.today)
    last_updated: datetime = Field(default_factory=datetime.utcnow)
```

- [ ] **Step 4: Run tests, confirm they pass**

```bash
pytest tests/test_models.py -v
```

Expected: 6 passed.

- [ ] **Step 5: Commit**

```bash
git add scraper/models.py tests/test_models.py
git commit -m "feat(models): add Pydantic schemas for Lead, Job, Company"
```

---

## Task 4: Storage — leads.json and seen.json IO

**Files:**
- Create: `scraper/storage.py`, `tests/test_storage.py`

- [ ] **Step 1: Write failing tests in `tests/test_storage.py`**

```python
import json
from datetime import date
from pathlib import Path
import pytest
from scraper.models import Lead, Company, Job, ScoreBreakdown, OutreachMessage
from scraper.storage import LeadStore, SeenStore


def make_lead(lead_id="greenhouse:x:1") -> Lead:
    return Lead(
        lead_id=lead_id,
        company=Company(name="X", ats_provider="greenhouse", ats_slug="x", country="US"),
        active_jobs=[],
        qa_jobs_count=0, all_it_jobs_count=0,
        lead_score=70,
        score_breakdown=ScoreBreakdown(qa_relevance=15, company_size=15, urgency=15, nearshore_fit=15, deal_size=10),
        score_rationale="test",
        outreach_message=OutreachMessage(subject="s", body="b"),
        status="new",
        first_seen=date.today(),
    )


def test_lead_store_roundtrip(tmp_path: Path):
    store = LeadStore(tmp_path / "leads.json")
    store.save([make_lead("greenhouse:a:1"), make_lead("greenhouse:b:2")])
    loaded = store.load()
    assert len(loaded) == 2
    assert loaded[0].lead_id == "greenhouse:a:1"


def test_lead_store_load_when_missing(tmp_path: Path):
    store = LeadStore(tmp_path / "absent.json")
    assert store.load() == []


def test_lead_store_upsert_replaces_existing(tmp_path: Path):
    store = LeadStore(tmp_path / "leads.json")
    store.save([make_lead("greenhouse:a:1")])
    new = make_lead("greenhouse:a:1")
    new.score_rationale = "updated"
    store.upsert([new, make_lead("greenhouse:b:2")])
    loaded = store.load()
    assert len(loaded) == 2
    by_id = {l.lead_id: l for l in loaded}
    assert by_id["greenhouse:a:1"].score_rationale == "updated"


def test_seen_store_roundtrip(tmp_path: Path):
    store = SeenStore(tmp_path / "seen.json")
    store.mark_seen("greenhouse:a:1")
    store.mark_seen("lever:b:2")
    assert store.has_seen("greenhouse:a:1")
    assert not store.has_seen("greenhouse:never:9")
    store2 = SeenStore(tmp_path / "seen.json")  # reload from disk
    assert store2.has_seen("lever:b:2")
```

- [ ] **Step 2: Run tests, confirm fail**

```bash
pytest tests/test_storage.py -v
```

Expected: ImportError.

- [ ] **Step 3: Implement `scraper/storage.py`**

```python
import json
from datetime import date, datetime
from pathlib import Path
from typing import Iterable
from scraper.models import Lead


def _json_default(obj):
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    raise TypeError(f"Cannot serialize {type(obj)}")


class LeadStore:
    def __init__(self, path: Path):
        self.path = Path(path)

    def load(self) -> list[Lead]:
        if not self.path.exists():
            return []
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        return [Lead.model_validate(item) for item in raw]

    def save(self, leads: Iterable[Lead]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        data = [l.model_dump(mode="json") for l in leads]
        self.path.write_text(
            json.dumps(data, indent=2, default=_json_default, ensure_ascii=False),
            encoding="utf-8",
        )

    def upsert(self, incoming: Iterable[Lead]) -> None:
        existing = {l.lead_id: l for l in self.load()}
        for lead in incoming:
            existing[lead.lead_id] = lead
        self.save(existing.values())


class SeenStore:
    def __init__(self, path: Path):
        self.path = Path(path)
        self._cache: dict[str, str] = {}
        if self.path.exists():
            self._cache = json.loads(self.path.read_text(encoding="utf-8"))

    def has_seen(self, lead_id: str) -> bool:
        return lead_id in self._cache

    def mark_seen(self, lead_id: str) -> None:
        self._cache[lead_id] = datetime.utcnow().isoformat()
        self._flush()

    def _flush(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self._cache, indent=2), encoding="utf-8")
```

- [ ] **Step 4: Run tests, confirm pass**

```bash
pytest tests/test_storage.py -v
```

Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add scraper/storage.py tests/test_storage.py
git commit -m "feat(storage): add LeadStore and SeenStore for JSON persistence"
```

---

## Task 5: ATS base class + dispatcher

**Files:**
- Create: `scraper/ats/base.py`, `tests/test_ats_base.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_ats_base.py
import pytest
from scraper.ats.base import ATSClient


def test_ats_client_is_abstract():
    with pytest.raises(TypeError):
        ATSClient()  # cannot instantiate abstract


def test_ats_client_subclass_must_implement_fetch():
    class Bad(ATSClient):
        provider = "x"
    with pytest.raises(TypeError):
        Bad()
```

- [ ] **Step 2: Run, confirm fail**

```bash
pytest tests/test_ats_base.py -v
```

- [ ] **Step 3: Implement `scraper/ats/base.py`**

```python
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
```

- [ ] **Step 4: Run, confirm pass**

```bash
pytest tests/test_ats_base.py -v
```

- [ ] **Step 5: Commit**

```bash
git add scraper/ats/base.py tests/test_ats_base.py
git commit -m "feat(ats): add ATSClient abstract base"
```

---

## Task 6: Greenhouse client + fixture

**Files:**
- Create: `tests/fixtures/greenhouse_airtable.json`, `scraper/ats/greenhouse.py`, `tests/test_greenhouse.py`

Greenhouse public boards API: `https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true`

- [ ] **Step 1: Save real fixture data**

Run this once to fetch a real example, then save it to the fixture path:

```bash
curl -s "https://boards-api.greenhouse.io/v1/boards/airtable/jobs?content=true" \
  | python -m json.tool > tests/fixtures/greenhouse_airtable.json
```

(If Airtable's slug ever stops working, swap to another known Greenhouse customer like `stripe` or `airbnb`.)

- [ ] **Step 2: Write failing tests in `tests/test_greenhouse.py`**

```python
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
```

- [ ] **Step 3: Run, confirm fail**

```bash
pytest tests/test_greenhouse.py -v
```

- [ ] **Step 4: Implement `scraper/ats/greenhouse.py`**

```python
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
```

- [ ] **Step 5: Run, confirm pass**

```bash
pytest tests/test_greenhouse.py -v
```

- [ ] **Step 6: Commit**

```bash
git add scraper/ats/greenhouse.py tests/test_greenhouse.py tests/fixtures/greenhouse_airtable.json
git commit -m "feat(ats): add Greenhouse client with HTML stripping and tech extraction"
```

---

## Task 7: Lever client + fixture

**Files:**
- Create: `tests/fixtures/lever_example.json`, `scraper/ats/lever.py`, `tests/test_lever.py`

Lever public API: `https://api.lever.co/v0/postings/{slug}?mode=json`

- [ ] **Step 1: Save real fixture**

```bash
# Pick a known active Lever-using company. Examples: 'netflix', 'figma', 'shopify' (verify slug works first).
curl -s "https://api.lever.co/v0/postings/netflix?mode=json" \
  | python -m json.tool > tests/fixtures/lever_example.json
```

- [ ] **Step 2: Write failing tests in `tests/test_lever.py`**

```python
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
    return json.loads(FIXTURE.read_text())


@pytest.mark.asyncio
@respx.mock
async def test_lever_returns_jobs(fixture_payload):
    respx.get("https://api.lever.co/v0/postings/netflix").mock(
        return_value=Response(200, json=fixture_payload)
    )
    client = LeverClient()
    jobs = await client.fetch_jobs(SeedCompany(name="Netflix", ats_provider="lever", ats_slug="netflix"))
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
```

- [ ] **Step 3: Run, confirm fail**

```bash
pytest tests/test_lever.py -v
```

- [ ] **Step 4: Implement `scraper/ats/lever.py`**

```python
from datetime import date
import re
from scraper.ats.base import ATSClient
from scraper.ats.greenhouse import _extract_tech_stack, _is_remote
from scraper.models import Job, SeedCompany

API_TEMPLATE = "https://api.lever.co/v0/postings/{slug}"


class LeverClient(ATSClient):
    provider = "lever"

    async def fetch_jobs(self, company: SeedCompany) -> list[Job]:
        url = API_TEMPLATE.format(slug=company.ats_slug)
        try:
            resp = await self.http.get(url, params={"mode": "json"})
        except Exception:
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
                description_text = re.sub(r"<[^>]+>", " ", description_html)
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
```

- [ ] **Step 5: Run, confirm pass**

```bash
pytest tests/test_lever.py -v
```

- [ ] **Step 6: Commit**

```bash
git add scraper/ats/lever.py tests/test_lever.py tests/fixtures/lever_example.json
git commit -m "feat(ats): add Lever client"
```

---

## Task 8: ATS dispatcher — fetch all clients in parallel

**Files:**
- Modify: `scraper/ats/base.py` (add `fetch_all`)
- Create: `tests/test_ats_dispatcher.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_ats_dispatcher.py
import pytest
from unittest.mock import AsyncMock
from scraper.ats.base import fetch_all_companies
from scraper.models import SeedCompany, Job
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
```

- [ ] **Step 2: Run, confirm fail**

```bash
pytest tests/test_ats_dispatcher.py -v
```

- [ ] **Step 3: Implement `fetch_all_companies` in `scraper/ats/base.py`**

Append to existing file:

```python
import asyncio
import logging
from scraper.models import SeedCompany

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
```

- [ ] **Step 4: Run, confirm pass**

```bash
pytest tests/test_ats_dispatcher.py -v
```

- [ ] **Step 5: Commit**

```bash
git add scraper/ats/base.py tests/test_ats_dispatcher.py
git commit -m "feat(ats): add concurrent fetch_all_companies dispatcher"
```

---

## Task 9: Anthropic client wrapper with prompt caching

**Files:**
- Create: `scraper/ai/client.py`, `tests/test_ai_client.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_ai_client.py
import pytest
from unittest.mock import MagicMock, patch
from scraper.ai.client import call_claude, CachedPrompt


def test_cached_prompt_builds_blocks():
    cp = CachedPrompt(static="System rules go here", dynamic="company-specific data")
    blocks = cp.to_system_blocks()
    assert blocks[0]["text"] == "System rules go here"
    assert blocks[0]["cache_control"] == {"type": "ephemeral"}
    assert blocks[1]["text"] == "company-specific data"
    assert "cache_control" not in blocks[1]


def test_call_claude_returns_text(monkeypatch):
    fake_client = MagicMock()
    fake_response = MagicMock()
    fake_response.content = [MagicMock(text='{"ok": true}')]
    fake_client.messages.create.return_value = fake_response

    monkeypatch.setattr("scraper.ai.client._get_client", lambda: fake_client)

    out = call_claude(
        model="claude-haiku-4-5-20251001",
        system=CachedPrompt(static="rules", dynamic=""),
        user="payload",
    )
    assert out == '{"ok": true}'
    fake_client.messages.create.assert_called_once()
```

- [ ] **Step 2: Run, confirm fail**

```bash
pytest tests/test_ai_client.py -v
```

- [ ] **Step 3: Implement `scraper/ai/client.py`**

```python
import os
from dataclasses import dataclass
from anthropic import Anthropic
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from anthropic import APIStatusError, APIConnectionError, RateLimitError


_singleton: Anthropic | None = None


def _get_client() -> Anthropic:
    global _singleton
    if _singleton is None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY not set")
        _singleton = Anthropic(api_key=api_key)
    return _singleton


@dataclass(frozen=True)
class CachedPrompt:
    """A two-block system prompt: static (cached) + dynamic (per-call)."""
    static: str
    dynamic: str = ""

    def to_system_blocks(self) -> list[dict]:
        blocks = [{"type": "text", "text": self.static, "cache_control": {"type": "ephemeral"}}]
        if self.dynamic:
            blocks.append({"type": "text", "text": self.dynamic})
        return blocks


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=2, max=10),
    retry=retry_if_exception_type((RateLimitError, APIConnectionError, APIStatusError)),
    reraise=True,
)
def call_claude(
    model: str,
    system: CachedPrompt,
    user: str,
    max_tokens: int = 1024,
    temperature: float = 0.0,
) -> str:
    """Single-turn call. Returns the assistant's text content."""
    client = _get_client()
    resp = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        system=system.to_system_blocks(),
        messages=[{"role": "user", "content": user}],
    )
    return resp.content[0].text
```

- [ ] **Step 4: Run, confirm pass**

```bash
pytest tests/test_ai_client.py -v
```

- [ ] **Step 5: Commit**

```bash
git add scraper/ai/client.py tests/test_ai_client.py
git commit -m "feat(ai): add Anthropic client wrapper with prompt caching and retries"
```

---

## Task 10: Filter (Haiku 4.5)

**Files:**
- Create: `scraper/ai/prompts/filter.txt`, `scraper/ai/filter.py`, `tests/test_filter.py`

- [ ] **Step 1: Create the static filter prompt at `scraper/ai/prompts/filter.txt`**

```
You are a B2B lead-qualification classifier for Greensoft Technologies, a Chicago-based nearshore staffing company that places senior IT engineers from Mexico/Latam into US tech companies.

Your job: given a single job posting, decide whether it represents a real lead candidate for Greensoft AND extract structured fields.

A "lead candidate" is any IT/engineering role posted by a US-based company that Greensoft could plausibly fill via nearshore staffing. Include: QA/testing, DevOps, SRE, Backend, Frontend, Mobile, Data Engineering, ML/AI, Cloud, Security, Architecture, technical PM, technical BA. Exclude: non-technical roles, executive (VP+ unless tech), internships, sales engineering on the US-customer-facing side, roles explicitly requiring US citizenship/clearance, healthcare clinical roles, or roles in non-US locations.

Return STRICT JSON, no markdown, no commentary. Schema:
{
  "is_lead_candidate": boolean,
  "extracted": {
    "role": string,            // canonical role family: "QA Automation" | "DevOps" | "Backend" | ...
    "seniority": "junior" | "mid" | "senior" | "staff" | "principal" | "unknown",
    "location": string,        // verbatim from posting
    "remote_friendly": boolean,
    "urgency_signal": "low" | "medium" | "high"  // based on language like "urgently hiring", "immediate start"
  },
  "reason_if_excluded": string  // empty if is_lead_candidate is true
}

Examples:
INPUT: { "title": "Senior QA Automation Engineer", "location": "Remote - US", "description": "We're looking for an SDET with Cypress experience..." }
OUTPUT: {"is_lead_candidate": true, "extracted": {"role": "QA Automation", "seniority": "senior", "location": "Remote - US", "remote_friendly": true, "urgency_signal": "low"}, "reason_if_excluded": ""}

INPUT: { "title": "VP of Marketing", "location": "New York, NY", "description": "..." }
OUTPUT: {"is_lead_candidate": false, "extracted": {"role": "Marketing", "seniority": "principal", "location": "New York, NY", "remote_friendly": false, "urgency_signal": "low"}, "reason_if_excluded": "non-technical role"}
```

- [ ] **Step 2: Write failing tests in `tests/test_filter.py`**

```python
import json
import pytest
from unittest.mock import patch
from scraper.ai.filter import filter_job, FilterResult
from scraper.models import Job
from datetime import date


def make_job(title="Senior QA", location="Remote - US", desc="Cypress, Playwright"):
    return Job(
        id="1", title=title, url="https://x/y",
        location=location, remote_friendly="remote" in location.lower(),
        posted_date=date.today(), tech_stack=[],
        raw_description=desc,
    )


def test_filter_parses_positive():
    fake_response = json.dumps({
        "is_lead_candidate": True,
        "extracted": {
            "role": "QA Automation", "seniority": "senior",
            "location": "Remote - US", "remote_friendly": True,
            "urgency_signal": "medium",
        },
        "reason_if_excluded": "",
    })
    with patch("scraper.ai.filter.call_claude", return_value=fake_response):
        result = filter_job(make_job())
    assert result.is_lead_candidate is True
    assert result.extracted["role"] == "QA Automation"


def test_filter_parses_negative():
    fake_response = json.dumps({
        "is_lead_candidate": False,
        "extracted": {
            "role": "Marketing", "seniority": "principal",
            "location": "NY", "remote_friendly": False, "urgency_signal": "low",
        },
        "reason_if_excluded": "non-technical role",
    })
    with patch("scraper.ai.filter.call_claude", return_value=fake_response):
        result = filter_job(make_job(title="VP Marketing"))
    assert result.is_lead_candidate is False
    assert "non-technical" in result.reason_if_excluded


def test_filter_swallows_malformed_json():
    with patch("scraper.ai.filter.call_claude", return_value="not json"):
        result = filter_job(make_job())
    assert result.is_lead_candidate is False
    assert result.reason_if_excluded.startswith("malformed")
```

- [ ] **Step 3: Run, confirm fail**

```bash
pytest tests/test_filter.py -v
```

- [ ] **Step 4: Implement `scraper/ai/filter.py`**

```python
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from scraper.ai.client import call_claude, CachedPrompt
from scraper.models import Job

log = logging.getLogger(__name__)

PROMPT = (Path(__file__).parent / "prompts" / "filter.txt").read_text(encoding="utf-8")
MODEL = "claude-haiku-4-5-20251001"


@dataclass
class FilterResult:
    is_lead_candidate: bool
    extracted: dict = field(default_factory=dict)
    reason_if_excluded: str = ""


def filter_job(job: Job) -> FilterResult:
    payload = {
        "title": job.title,
        "location": job.location,
        "description": (job.raw_description or "")[:4000],
    }
    user = json.dumps(payload, ensure_ascii=False)
    raw = call_claude(
        model=MODEL,
        system=CachedPrompt(static=PROMPT),
        user=user,
        max_tokens=512,
        temperature=0.0,
    )
    try:
        parsed = json.loads(raw)
        return FilterResult(
            is_lead_candidate=bool(parsed["is_lead_candidate"]),
            extracted=parsed.get("extracted", {}),
            reason_if_excluded=parsed.get("reason_if_excluded", ""),
        )
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        log.warning("filter parse failed for job %s: %s", job.id, e)
        return FilterResult(is_lead_candidate=False, reason_if_excluded=f"malformed: {e}")
```

- [ ] **Step 5: Run, confirm pass**

```bash
pytest tests/test_filter.py -v
```

- [ ] **Step 6: Commit**

```bash
git add scraper/ai/prompts/filter.txt scraper/ai/filter.py tests/test_filter.py
git commit -m "feat(ai): add Haiku-based lead filter"
```

---

## Task 11: Score (Sonnet 4.6) — 5-signal scoring

**Files:**
- Create: `scraper/ai/prompts/score.txt`, `scraper/ai/score.py`, `tests/test_score.py`

- [ ] **Step 1: Create `scraper/ai/prompts/score.txt`**

```
You are scoring B2B leads for Greensoft Technologies (Chicago LLC, nearshore IT staffing — Mexico/Latam talent for US clients). Greensoft's clients include Walmart, Coca-Cola FEMSA, Santander, and Nike. Their value props: 40-60% cost reduction, zero timezone gap, 14-day hiring timeline.

You will receive aggregated company data (the company plus its currently-active IT job postings). Compute a 0-100 lead score broken into FIVE weighted signals:

1. qa_relevance (0-25): Does the company have QA/test roles? Are they senior? Does the stack match Greensoft's strength (Selenium, Cypress, Playwright, Postman, k6)?
2. company_size (0-20): Sweet spot is 200-2000 employees (mid-market).
   - <50 employees: 0-5 (too small, doesn't care about nearshore)
   - 50-200: 8-12
   - 200-2000: 15-20 (sweet spot)
   - 2000-5000: 10-15
   - >5000: 5-10 (procurement is too slow; long sales cycle)
3. urgency (0-20): Based on how long jobs have been open.
   - All <7 days: 5 (just posted, not desperate)
   - 7-21 days: 10
   - 21-45 days: 15
   - >45 days for any: 18-20 (struggling to fill)
4. nearshore_fit (0-20): Keywords in JDs ("remote", "distributed", "global", "Latin America", "EMEA"), explicit mention of nearshore/offshore, time zone flexibility. Empresas with employees in Latam = +bonus.
5. deal_size (0-15): Total IT roles open.
   - 1-2: 3-5 (transactional)
   - 3-5: 7-10
   - 6-10: 11-13 (good)
   - >10: 14-15 (potential multi-role contract)

After computing the breakdown, sum to get total score 0-100. ALSO produce a 1-2 sentence rationale (Spanish or English, your choice based on company's primary market).

Return STRICT JSON only:
{
  "qa_relevance": int,
  "company_size": int,
  "urgency": int,
  "nearshore_fit": int,
  "deal_size": int,
  "rationale": string
}
```

- [ ] **Step 2: Write failing tests in `tests/test_score.py`**

```python
import json
import pytest
from unittest.mock import patch
from datetime import date
from scraper.ai.score import score_company, ScoreResult
from scraper.models import Company, Job


def make_jobs(n_qa=1, n_other=2, days_open=20):
    jobs = []
    for i in range(n_qa):
        jobs.append(Job(
            id=f"q{i}", title="Senior QA Automation Engineer",
            url="https://x/y", location="Remote - US",
            remote_friendly=True, posted_date=date.today(), tech_stack=["Cypress"],
            raw_description="Looking for SDET with Cypress",
        ))
    for i in range(n_other):
        jobs.append(Job(
            id=f"o{i}", title="DevOps Engineer",
            url="https://x/y", location="Remote - US",
            remote_friendly=True, posted_date=date.today(), tech_stack=["AWS"],
            raw_description="DevOps with AWS",
        ))
    return jobs


def test_score_returns_breakdown():
    fake = json.dumps({
        "qa_relevance": 22, "company_size": 18, "urgency": 14,
        "nearshore_fit": 18, "deal_size": 12,
        "rationale": "SaaS mid-market with QA + DevOps openings",
    })
    company = Company(name="X", ats_provider="greenhouse", ats_slug="x", country="US")
    with patch("scraper.ai.score.call_claude", return_value=fake):
        result = score_company(company, make_jobs())
    assert result.total == 84
    assert result.breakdown.qa_relevance == 22
    assert "SaaS" in result.rationale


def test_score_clamps_to_max():
    fake = json.dumps({
        "qa_relevance": 30, "company_size": 25, "urgency": 25,
        "nearshore_fit": 25, "deal_size": 20,
        "rationale": "model overshot caps",
    })
    company = Company(name="X", ats_provider="lever", ats_slug="x", country="US")
    with patch("scraper.ai.score.call_claude", return_value=fake):
        result = score_company(company, make_jobs())
    # Must clamp each component to its max
    assert result.breakdown.qa_relevance == 25
    assert result.breakdown.company_size == 20
    assert result.total == 100
```

- [ ] **Step 3: Run, confirm fail**

```bash
pytest tests/test_score.py -v
```

- [ ] **Step 4: Implement `scraper/ai/score.py`**

```python
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from scraper.ai.client import call_claude, CachedPrompt
from scraper.models import Company, Job, ScoreBreakdown

log = logging.getLogger(__name__)

PROMPT = (Path(__file__).parent / "prompts" / "score.txt").read_text(encoding="utf-8")
MODEL = "claude-sonnet-4-6"

CAPS = {
    "qa_relevance": 25,
    "company_size": 20,
    "urgency": 20,
    "nearshore_fit": 20,
    "deal_size": 15,
}


@dataclass
class ScoreResult:
    breakdown: ScoreBreakdown
    rationale: str

    @property
    def total(self) -> int:
        return self.breakdown.total


def _summarize_jobs(jobs: list[Job]) -> list[dict]:
    out = []
    for j in jobs:
        out.append({
            "id": j.id,
            "title": j.title,
            "location": j.location,
            "remote_friendly": j.remote_friendly,
            "days_open": j.days_open,
            "tech_stack": j.tech_stack,
            "description_excerpt": (j.raw_description or "")[:1500],
        })
    return out


def score_company(company: Company, jobs: list[Job]) -> ScoreResult:
    payload = {
        "company": {
            "name": company.name,
            "homepage": str(company.homepage) if company.homepage else None,
            "industry": company.industry,
            "size_estimate": company.size_estimate,
            "country": company.country,
        },
        "active_jobs": _summarize_jobs(jobs),
        "all_it_jobs_count": len(jobs),
    }
    raw = call_claude(
        model=MODEL,
        system=CachedPrompt(static=PROMPT),
        user=json.dumps(payload, ensure_ascii=False),
        max_tokens=600,
        temperature=0.0,
    )
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as e:
        log.warning("score parse failed for %s: %s", company.name, e)
        # Fallback: zero score (filtered out by threshold downstream)
        return ScoreResult(
            breakdown=ScoreBreakdown(qa_relevance=0, company_size=0, urgency=0, nearshore_fit=0, deal_size=0),
            rationale=f"score parse error: {e}",
        )
    clamped = {k: min(parsed.get(k, 0), CAPS[k]) for k in CAPS}
    breakdown = ScoreBreakdown(**clamped)
    return ScoreResult(breakdown=breakdown, rationale=parsed.get("rationale", ""))
```

- [ ] **Step 5: Run, confirm pass**

```bash
pytest tests/test_score.py -v
```

- [ ] **Step 6: Commit**

```bash
git add scraper/ai/prompts/score.txt scraper/ai/score.py tests/test_score.py
git commit -m "feat(ai): add Sonnet-based 5-signal lead scoring"
```

---

## Task 12: Outreach message generation (Sonnet 4.6) + linter

**Files:**
- Create: `scraper/ai/prompts/message.txt`, `scraper/ai/message.py`, `scraper/ai/linter.py`, `tests/test_message_linter.py`, `tests/test_message.py`

- [ ] **Step 1: Create `scraper/ai/prompts/message.txt`**

```
You write COLD OUTREACH EMAILS for Greensoft Technologies (Chicago LLC, nearshore IT staffing). Recipient: a hiring decision-maker (CTO, VP Eng, Head of Talent, Recruiter) at a US company we just identified as a lead.

You are writing the FIRST email — never sent before, no warm intro.

Hard rules:
- Total body length: ≤110 words.
- Subject line: ≤8 words. Specific, mentions a concrete role or beneficial number. NEVER generic ("Partnership opportunity", "Quick question", "Touching base").
- Open with ONE specific observation that proves you actually looked at the company. Reference their actual role or pain. NEVER open with "I hope this email finds you well."
- Mention social proof: name 2-3 of [Walmart, Coca-Cola FEMSA, Santander, Nike] — pick the ones most plausibly relevant to the recipient's industry.
- State the value prop in ONE sentence: 40-60% cost reduction, zero timezone gap, 14-day hiring timeline.
- Close with ONE closed question (yes/no). Suggest a 15-min call. Do not give multiple options.
- Voice: American executive. Direct. No diminutives. No emoji. No bullet points.

Forbidden phrases (never use any of these):
revolutionize, leverage synergies, game-changing, in today's fast-paced world, synergize, cutting-edge, world-class, best-in-class, paradigm shift, unlock potential, take to the next level, hope this email finds you well, just wanted to reach out, circle back, touch base, low-hanging fruit.

Output STRICT JSON only:
{
  "subject": string,
  "body": string
}

Body uses "\n\n" between paragraphs. Sign as "[Your name]\nGreensoft Technologies" — leave "[Your name]" literal so the user can fill it in.
```

- [ ] **Step 2: Write failing tests in `tests/test_message_linter.py`**

```python
import pytest
from scraper.ai.linter import lint_message, LintResult
from scraper.models import OutreachMessage


def test_lint_passes_clean_message():
    msg = OutreachMessage(
        subject="Helping Airtable close 8 IT roles",
        body=(
            "Hi there,\n\n"
            "Noticed Airtable's QA Automation role has been open 3+ weeks. "
            "Greensoft Technologies places senior nearshore engineers from "
            "Mexico and Latam — we do this for Walmart, Coca-Cola FEMSA, and Nike.\n\n"
            "40-60% cost reduction, zero timezone gap, 14-day hiring.\n\n"
            "Worth a 15-min call this week to walk through your QA pipeline?\n\n"
            "[Your name]\nGreensoft Technologies"
        ),
    )
    result = lint_message(msg)
    assert result.passed
    assert result.issues == []


def test_lint_flags_word_count():
    msg = OutreachMessage(subject="X", body="word " * 200)
    result = lint_message(msg)
    assert not result.passed
    assert any("word count" in i for i in result.issues)


def test_lint_flags_forbidden_phrase():
    msg = OutreachMessage(
        subject="Quick note",
        body="I hope this email finds you well. We can revolutionize your hiring. [Your name]\nGreensoft Technologies",
    )
    result = lint_message(msg)
    assert not result.passed
    assert any("forbidden" in i for i in result.issues)


def test_lint_flags_long_subject():
    msg = OutreachMessage(
        subject="A very long subject line with way more than eight words in it",
        body="Body. [Your name]\nGreensoft Technologies",
    )
    result = lint_message(msg)
    assert not result.passed
    assert any("subject" in i for i in result.issues)
```

- [ ] **Step 3: Run, confirm fail**

```bash
pytest tests/test_message_linter.py -v
```

- [ ] **Step 4: Implement `scraper/ai/linter.py`**

```python
import re
from dataclasses import dataclass, field
from scraper.models import OutreachMessage

FORBIDDEN_PHRASES = [
    "revolutionize", "leverage synergies", "game-changing",
    "in today's fast-paced world", "synergize", "cutting-edge",
    "world-class", "best-in-class", "paradigm shift",
    "unlock potential", "take to the next level",
    "hope this email finds you well", "just wanted to reach out",
    "circle back", "touch base", "low-hanging fruit",
]

MAX_WORDS = 110
MAX_SUBJECT_WORDS = 8


@dataclass
class LintResult:
    passed: bool
    issues: list[str] = field(default_factory=list)


def _word_count(text: str) -> int:
    return len(re.findall(r"\b\w+\b", text))


def lint_message(msg: OutreachMessage) -> LintResult:
    issues: list[str] = []
    body_words = _word_count(msg.body)
    if body_words > MAX_WORDS:
        issues.append(f"body word count {body_words} exceeds max {MAX_WORDS}")
    subj_words = _word_count(msg.subject)
    if subj_words > MAX_SUBJECT_WORDS:
        issues.append(f"subject word count {subj_words} exceeds max {MAX_SUBJECT_WORDS}")
    lower_body = msg.body.lower()
    lower_subj = msg.subject.lower()
    for phrase in FORBIDDEN_PHRASES:
        if phrase in lower_body or phrase in lower_subj:
            issues.append(f"forbidden phrase: '{phrase}'")
    if "?" not in msg.body:
        issues.append("missing closing question (CTA)")
    return LintResult(passed=len(issues) == 0, issues=issues)
```

- [ ] **Step 5: Run linter tests, confirm pass**

```bash
pytest tests/test_message_linter.py -v
```

- [ ] **Step 6: Write tests for message generator in `tests/test_message.py`**

```python
import json
from unittest.mock import patch
from datetime import date
from scraper.ai.message import generate_message
from scraper.models import Company, Job, ScoreBreakdown


def test_generate_message_returns_message_object():
    fake = json.dumps({
        "subject": "Helping Acme close 6 IT roles",
        "body": (
            "Hi there,\n\nNoticed Acme's Senior QA role has been open 4 weeks. "
            "Greensoft places nearshore engineers from Mexico — same model we use "
            "with Walmart, Coca-Cola FEMSA, and Nike.\n\n40-60% cost reduction, "
            "zero timezone gap, 14-day hiring.\n\nOpen to a 15-min call this week?\n\n"
            "[Your name]\nGreensoft Technologies"
        ),
    })
    company = Company(name="Acme", ats_provider="greenhouse", ats_slug="acme", country="US")
    breakdown = ScoreBreakdown(qa_relevance=20, company_size=18, urgency=15, nearshore_fit=15, deal_size=12)
    with patch("scraper.ai.message.call_claude", return_value=fake):
        msg = generate_message(company, [], breakdown, "rationale")
    assert msg.subject.startswith("Helping Acme")
    assert "Greensoft" in msg.body


def test_generate_message_falls_back_on_bad_json():
    company = Company(name="X", ats_provider="lever", ats_slug="x", country="US")
    breakdown = ScoreBreakdown(qa_relevance=10, company_size=10, urgency=10, nearshore_fit=10, deal_size=5)
    with patch("scraper.ai.message.call_claude", return_value="garbage"):
        msg = generate_message(company, [], breakdown, "rationale")
    assert msg.subject == "[needs review] X"
    assert "manual review" in msg.body.lower()
```

- [ ] **Step 7: Implement `scraper/ai/message.py`**

```python
import json
import logging
from pathlib import Path
from scraper.ai.client import call_claude, CachedPrompt
from scraper.models import Company, Job, OutreachMessage, ScoreBreakdown

log = logging.getLogger(__name__)

PROMPT = (Path(__file__).parent / "prompts" / "message.txt").read_text(encoding="utf-8")
MODEL = "claude-sonnet-4-6"


def generate_message(
    company: Company,
    jobs: list[Job],
    breakdown: ScoreBreakdown,
    rationale: str,
) -> OutreachMessage:
    payload = {
        "company": {
            "name": company.name,
            "industry": company.industry,
            "size_estimate": company.size_estimate,
        },
        "top_roles": [
            {"title": j.title, "days_open": j.days_open, "location": j.location}
            for j in jobs[:8]
        ],
        "all_it_jobs_count": len(jobs),
        "score_breakdown": breakdown.model_dump(),
        "rationale": rationale,
    }
    raw = call_claude(
        model=MODEL,
        system=CachedPrompt(static=PROMPT),
        user=json.dumps(payload, ensure_ascii=False),
        max_tokens=512,
        temperature=0.3,
    )
    try:
        parsed = json.loads(raw)
        return OutreachMessage(subject=parsed["subject"], body=parsed["body"])
    except (json.JSONDecodeError, KeyError) as e:
        log.warning("message parse failed for %s: %s", company.name, e)
        return OutreachMessage(
            subject=f"[needs review] {company.name}",
            body="Message generation failed — manual review required.\n\n[Your name]\nGreensoft Technologies",
        )
```

- [ ] **Step 8: Run all message tests**

```bash
pytest tests/test_message.py tests/test_message_linter.py -v
```

- [ ] **Step 9: Commit**

```bash
git add scraper/ai/prompts/message.txt scraper/ai/message.py scraper/ai/linter.py tests/test_message.py tests/test_message_linter.py
git commit -m "feat(ai): add Sonnet message generator + linter"
```

---

## Task 13: Pipeline orchestrator

**Files:**
- Create: `scraper/pipeline.py`, `tests/test_pipeline.py`

- [ ] **Step 1: Write failing tests in `tests/test_pipeline.py`**

```python
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
```

- [ ] **Step 2: Run, confirm fail**

```bash
pytest tests/test_pipeline.py -v
```

- [ ] **Step 3: Implement `scraper/pipeline.py`**

```python
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
```

- [ ] **Step 4: Run, confirm pass**

```bash
pytest tests/test_pipeline.py -v
```

- [ ] **Step 5: Commit**

```bash
git add scraper/pipeline.py tests/test_pipeline.py
git commit -m "feat(pipeline): add orchestrator with idempotency and per-company aggregation"
```

---

## Task 14: CLI entrypoint (`main.py`)

**Files:**
- Create: `scraper/main.py`
- Create: `seed/companies.json` (initial 10 companies — expand later)

- [ ] **Step 1: Create `seed/companies.json` with 10 starter companies**

(Pick companies with verified active Greenhouse/Lever boards. Verify slugs work via `curl https://boards-api.greenhouse.io/v1/boards/{slug}/jobs` before committing.)

```json
[
  {"name": "Airtable", "ats_provider": "greenhouse", "ats_slug": "airtable", "industry": "SaaS"},
  {"name": "Notion", "ats_provider": "greenhouse", "ats_slug": "notion", "industry": "SaaS"},
  {"name": "Anthropic", "ats_provider": "greenhouse", "ats_slug": "anthropic", "industry": "AI"},
  {"name": "Stripe", "ats_provider": "greenhouse", "ats_slug": "stripe", "industry": "Fintech"},
  {"name": "Discord", "ats_provider": "greenhouse", "ats_slug": "discord", "industry": "Consumer"},
  {"name": "Coinbase", "ats_provider": "greenhouse", "ats_slug": "coinbase", "industry": "Fintech"},
  {"name": "Plaid", "ats_provider": "lever", "ats_slug": "plaid", "industry": "Fintech"},
  {"name": "Figma", "ats_provider": "greenhouse", "ats_slug": "figma", "industry": "SaaS"},
  {"name": "Hashicorp", "ats_provider": "greenhouse", "ats_slug": "hashicorp", "industry": "DevOps"},
  {"name": "Snowflake", "ats_provider": "greenhouse", "ats_slug": "snowflake", "industry": "Data"}
]
```

(Verify each slug returns 200 from the public ATS endpoint before committing. If a slug fails, replace it.)

- [ ] **Step 2: Implement `scraper/main.py`**

```python
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
```

- [ ] **Step 3: Smoke test the CLI signature (no API call yet)**

```bash
python -m scraper.main --help
```

Expected: argparse help output, no errors.

- [ ] **Step 4: Run full pipeline against the seed list (consumes API tokens — ~$0.10)**

Make sure `.env` has `ANTHROPIC_API_KEY` set. Then:

```bash
python -m scraper.main
cat data/leads.json | python -m json.tool | head -100
```

Expected: leads.json contains valid leads. seen.json populated.

- [ ] **Step 5: Commit**

```bash
git add scraper/main.py seed/companies.json
git commit -m "feat(cli): add scraper.main entrypoint and seed company list"
```

---

## Task 15: GitHub Actions daily workflow

**Files:**
- Create: `.github/workflows/daily-leadgen.yml`

- [ ] **Step 1: Create `.github/workflows/daily-leadgen.yml`**

```yaml
name: Daily Leadgen

on:
  schedule:
    # 07:00 Chicago = 12:00 UTC (CST) / 13:00 UTC (CDT). Run at 12:00 and 13:00; the
    # scraper is idempotent so a second run is a no-op once seen.json is updated.
    - cron: "0 12 * * *"
  workflow_dispatch: {}

permissions:
  contents: write

jobs:
  run:
    runs-on: ubuntu-latest
    timeout-minutes: 20
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: "pip"

      - name: Install
        run: pip install -e ".[dev]"

      - name: Run pipeline
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          LEADGEN_LOG_LEVEL: INFO
        run: python -m scraper.main | tee summary.json

      - name: Sync data into dashboard build
        run: |
          mkdir -p dashboard/data
          cp data/leads.json dashboard/data/leads.json

      - name: Commit results
        run: |
          git config user.name "leadgen-bot"
          git config user.email "leadgen-bot@users.noreply.github.com"
          git add data/ dashboard/data/
          if git diff --cached --quiet; then
            echo "No changes to commit"
            exit 0
          fi
          SUMMARY=$(jq -c '{c:.companies_scraped, p:.new_postings, h:.hot, w:.warm, k:.cold}' summary.json)
          git commit -m "chore(leadgen): daily run $(date -u +%F) ${SUMMARY}"
          git push
```

- [ ] **Step 2: Required secret**

In GitHub UI (or via `gh`):

```bash
gh secret set ANTHROPIC_API_KEY  # paste key when prompted
```

(This step is manual — document in README if `gh` not available locally.)

- [ ] **Step 3: Validate YAML**

```bash
python -c "import yaml, sys; yaml.safe_load(open('.github/workflows/daily-leadgen.yml')); print('OK')"
```

- [ ] **Step 4: Commit**

```bash
git add .github/workflows/daily-leadgen.yml
git commit -m "ci: add daily leadgen workflow on cron 12:00 UTC"
```

---

## Task 16: Dashboard — HTML skeleton + Tailwind + Alpine

**Files:**
- Create: `dashboard/index.html`, `dashboard/styles.css`, `dashboard/app.js`

- [ ] **Step 1: Create `dashboard/index.html`**

```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Greensoft Leads</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script defer src="https://unpkg.com/alpinejs@3.13/dist/cdn.min.js"></script>
  <link rel="stylesheet" href="./styles.css" />
</head>
<body class="bg-slate-50 text-slate-900 antialiased">
  <div id="app" x-data="leadsApp()" x-init="init()" class="max-w-7xl mx-auto px-4 py-6">

    <header class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold">Greensoft Leads</h1>
      <div class="text-sm text-slate-500" x-text="lastUpdate"></div>
    </header>

    <section class="bg-white rounded-lg shadow-sm border border-slate-200 p-4 mb-4 flex flex-wrap gap-3 items-center">
      <select class="border rounded px-2 py-1" x-model="filters.country">
        <option value="">All countries</option>
        <option value="US">United States</option>
      </select>
      <label class="flex items-center gap-2">
        <span class="text-sm text-slate-600">Min score</span>
        <input type="number" class="border rounded w-20 px-2 py-1" x-model.number="filters.minScore" min="0" max="100" />
      </label>
      <select class="border rounded px-2 py-1" x-model="filters.status">
        <option value="">All statuses</option>
        <option value="new">New</option>
        <option value="contacted">Contacted</option>
        <option value="replied">Replied</option>
        <option value="client">Client</option>
        <option value="dead">Dead</option>
      </select>
      <input type="search" class="border rounded px-2 py-1 flex-1 min-w-[200px]" placeholder="Search company…" x-model="filters.q" />
      <select class="border rounded px-2 py-1" x-model="sort">
        <option value="score-desc">Score ↓</option>
        <option value="score-asc">Score ↑</option>
        <option value="newest">Newest first</option>
        <option value="name">Company A→Z</option>
      </select>
      <span class="ml-auto text-sm text-slate-500"><span x-text="filtered.length"></span> leads</span>
    </section>

    <section class="bg-white rounded-lg shadow-sm border border-slate-200 overflow-hidden">
      <table class="w-full text-sm">
        <thead class="bg-slate-100 text-slate-600 uppercase text-xs">
          <tr>
            <th class="px-3 py-2 text-left">Score</th>
            <th class="px-3 py-2 text-left">Company</th>
            <th class="px-3 py-2 text-left">Country</th>
            <th class="px-3 py-2 text-right">QA</th>
            <th class="px-3 py-2 text-right">All IT</th>
            <th class="px-3 py-2 text-left">Status</th>
          </tr>
        </thead>
        <tbody>
          <template x-for="lead in filtered" :key="lead.lead_id">
            <template x-if="true">
              <tbody>
                <tr class="border-t hover:bg-slate-50 cursor-pointer" @click="toggle(lead.lead_id)">
                  <td class="px-3 py-2 font-mono font-bold" :class="scoreClass(lead.lead_score)" x-text="lead.lead_score"></td>
                  <td class="px-3 py-2 font-medium" x-text="lead.company.name"></td>
                  <td class="px-3 py-2" x-text="lead.company.country"></td>
                  <td class="px-3 py-2 text-right" x-text="lead.qa_jobs_count"></td>
                  <td class="px-3 py-2 text-right" x-text="lead.all_it_jobs_count"></td>
                  <td class="px-3 py-2"><span class="inline-block px-2 py-0.5 rounded text-xs" :class="statusClass(getStatus(lead))" x-text="getStatus(lead)"></span></td>
                </tr>
                <tr x-show="expanded[lead.lead_id]" class="bg-slate-50">
                  <td colspan="6" class="px-6 py-4">
                    <div class="grid md:grid-cols-2 gap-6">
                      <div>
                        <h3 class="font-semibold mb-2">Why this score</h3>
                        <ul class="space-y-1 text-sm">
                          <template x-for="(label, key) in scoreLabels">
                            <li>
                              <span class="inline-block w-32" x-text="label"></span>
                              <span class="font-mono" x-text="lead.score_breakdown[key] + '/' + scoreCaps[key]"></span>
                              <span class="ml-2 inline-block bg-slate-200 rounded h-2 align-middle" :style="`width: ${(lead.score_breakdown[key]/scoreCaps[key])*100}px`"></span>
                            </li>
                          </template>
                        </ul>
                        <p class="text-sm text-slate-600 mt-3 italic" x-text="lead.score_rationale"></p>
                      </div>
                      <div>
                        <h3 class="font-semibold mb-2">Active roles (<span x-text="lead.active_jobs.length"></span>)</h3>
                        <ul class="space-y-1 text-sm max-h-48 overflow-auto">
                          <template x-for="job in lead.active_jobs">
                            <li>
                              <a :href="job.url" target="_blank" class="text-blue-700 hover:underline" x-text="job.title"></a>
                              <span class="text-slate-500 ml-2 text-xs" x-text="job.location + ' · ' + job.days_open + ' days'"></span>
                            </li>
                          </template>
                        </ul>
                      </div>
                    </div>
                    <div class="mt-6 bg-white rounded border border-slate-200 p-4">
                      <h3 class="font-semibold mb-2">Generated message</h3>
                      <p class="text-sm font-mono"><strong>Subject:</strong> <span x-text="lead.outreach_message.subject"></span></p>
                      <pre class="whitespace-pre-wrap text-sm mt-2 font-sans" x-text="lead.outreach_message.body"></pre>
                      <div class="mt-3 flex gap-2">
                        <button class="px-3 py-1 text-sm bg-slate-800 text-white rounded hover:bg-slate-700" @click="copyMessage(lead)">📋 Copy</button>
                        <a class="px-3 py-1 text-sm border border-slate-300 rounded hover:bg-slate-100" :href="gmailUrl(lead)" target="_blank">📨 Open in Gmail</a>
                      </div>
                    </div>
                    <div class="mt-4 flex gap-2">
                      <template x-for="s in ['contacted','replied','client','dead']">
                        <button class="px-3 py-1 text-sm border rounded hover:bg-slate-100" @click="setStatus(lead, s)" x-text="'Mark ' + s"></button>
                      </template>
                    </div>
                  </td>
                </tr>
              </tbody>
            </template>
          </template>
        </tbody>
      </table>
    </section>
  </div>

  <script src="./app.js"></script>
</body>
</html>
```

- [ ] **Step 2: Create `dashboard/styles.css`**

```css
body { font-family: -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; }
table tbody tbody:nth-child(even) tr:not([x-show]) { background-color: #fafafa; }
```

- [ ] **Step 3: Create `dashboard/app.js`**

```js
const SCORE_LABELS = {
  qa_relevance: "QA relevance",
  company_size: "Company size",
  urgency: "Urgency",
  nearshore_fit: "Nearshore fit",
  deal_size: "Deal size",
};
const SCORE_CAPS = {
  qa_relevance: 25, company_size: 20, urgency: 20,
  nearshore_fit: 20, deal_size: 15,
};

function leadsApp() {
  return {
    leads: [],
    filters: { country: "", minScore: 0, status: "", q: "" },
    sort: "score-desc",
    expanded: {},
    statuses: JSON.parse(localStorage.getItem("leadStatuses") || "{}"),
    lastUpdate: "",
    scoreLabels: SCORE_LABELS,
    scoreCaps: SCORE_CAPS,

    async init() {
      const resp = await fetch("./data/leads.json", { cache: "no-cache" });
      this.leads = await resp.json();
      const lm = resp.headers.get("last-modified");
      this.lastUpdate = lm ? `Last update: ${new Date(lm).toLocaleString()}` : "";
    },

    get filtered() {
      const f = this.filters;
      let list = this.leads.filter(l => {
        if (f.country && l.company.country !== f.country) return false;
        if (f.minScore && l.lead_score < f.minScore) return false;
        if (f.status && this.getStatus(l) !== f.status) return false;
        if (f.q && !l.company.name.toLowerCase().includes(f.q.toLowerCase())) return false;
        return true;
      });
      switch (this.sort) {
        case "score-asc": list.sort((a,b) => a.lead_score - b.lead_score); break;
        case "score-desc": list.sort((a,b) => b.lead_score - a.lead_score); break;
        case "newest": list.sort((a,b) => (b.first_seen || "").localeCompare(a.first_seen || "")); break;
        case "name": list.sort((a,b) => a.company.name.localeCompare(b.company.name)); break;
      }
      return list;
    },

    toggle(id) { this.expanded[id] = !this.expanded[id]; },

    getStatus(lead) { return this.statuses[lead.lead_id] || lead.status || "new"; },

    setStatus(lead, status) {
      this.statuses[lead.lead_id] = status;
      localStorage.setItem("leadStatuses", JSON.stringify(this.statuses));
    },

    scoreClass(s) {
      if (s >= 70) return "text-emerald-700";
      if (s >= 50) return "text-amber-700";
      return "text-slate-500";
    },

    statusClass(s) {
      const map = {
        new: "bg-blue-100 text-blue-800",
        contacted: "bg-amber-100 text-amber-800",
        replied: "bg-purple-100 text-purple-800",
        client: "bg-emerald-100 text-emerald-800",
        dead: "bg-slate-200 text-slate-600",
      };
      return map[s] || map.new;
    },

    copyMessage(lead) {
      const text = `Subject: ${lead.outreach_message.subject}\n\n${lead.outreach_message.body}`;
      navigator.clipboard.writeText(text).then(() => { alert("Copied"); });
    },

    gmailUrl(lead) {
      const subject = encodeURIComponent(lead.outreach_message.subject);
      const body = encodeURIComponent(lead.outreach_message.body);
      return `https://mail.google.com/mail/?view=cm&fs=1&su=${subject}&body=${body}`;
    },
  };
}
```

- [ ] **Step 4: Sanity-check locally**

Place a sample `dashboard/data/leads.json` with the output of a real run, then serve:

```bash
cd dashboard
python -m http.server 8000
# Open http://localhost:8000 in browser
```

Expected: leads render, filters work, click expansion shows score breakdown and message, "Copy" button copies. UI is clean.

- [ ] **Step 5: Commit**

```bash
git add dashboard/index.html dashboard/styles.css dashboard/app.js
git commit -m "feat(dashboard): add static SPA with filters, sort, and message copy"
```

---

## Task 17: AI quality golden-set test

**Files:**
- Create: `tests/fixtures/golden_leads.json`, `tests/test_ai_quality.py`

This task validates *real* end-to-end quality of the AI scoring against a hand-curated set. Marked `@pytest.mark.slow` so it doesn't run on every PR — only on demand or weekly.

- [ ] **Step 1: Create `tests/fixtures/golden_leads.json`**

Hand-curate 5 examples (3 obvious-hot, 2 obvious-cold) — small enough to maintain, big enough to catch regressions.

```json
[
  {
    "name": "obvious_hot_saas_midmarket",
    "company": {"name": "TestCo", "ats_provider": "greenhouse", "ats_slug": "x", "country": "US", "size_estimate": "500-1000", "industry": "SaaS"},
    "jobs": [
      {"id": "1", "title": "Senior QA Automation Engineer", "url": "https://x/y", "location": "Remote - US", "remote_friendly": true, "posted_date": "2026-04-04", "tech_stack": ["Cypress","TypeScript","AWS"], "raw_description": "Senior SDET with Cypress and Playwright. Distributed team across US and Latin America. Open 3+ weeks."},
      {"id": "2", "title": "DevOps Engineer", "url": "https://x/y", "location": "Remote - US", "remote_friendly": true, "posted_date": "2026-04-10", "tech_stack": ["AWS","Terraform"], "raw_description": "DevOps with AWS, Terraform"}
    ],
    "expected_score_min": 70
  },
  {
    "name": "obvious_cold_tiny_startup_no_qa",
    "company": {"name": "Tiny", "ats_provider": "lever", "ats_slug": "x", "country": "US", "size_estimate": "1-10", "industry": "Pre-seed"},
    "jobs": [
      {"id": "1", "title": "Founding Engineer", "url": "https://x/y", "location": "San Francisco, CA", "remote_friendly": false, "posted_date": "2026-04-23", "tech_stack": ["Rust"], "raw_description": "Founding eng in SF, equity heavy. Onsite required."}
    ],
    "expected_score_max": 40
  }
]
```

(Add 3 more curated examples covering: large enterprise with stale QA roles → expected_score_min 65; mid-market with onsite-only roles → expected_score_max 55; mid-market with multiple QA + DevOps remote → expected_score_min 75.)

- [ ] **Step 2: Write `tests/test_ai_quality.py`**

```python
"""
End-to-end IA quality check. Runs against the real Anthropic API. Marked `slow`
so CI runs it only on weekly schedule, not every PR.

Run manually:    pytest tests/test_ai_quality.py -m slow -v
"""
import json
import os
from pathlib import Path
import pytest
from datetime import date
from scraper.models import Company, Job
from scraper.ai.score import score_company

GOLDEN = json.loads((Path(__file__).parent / "fixtures" / "golden_leads.json").read_text())


@pytest.mark.slow
@pytest.mark.skipif(not os.environ.get("ANTHROPIC_API_KEY"), reason="No API key")
@pytest.mark.parametrize("case", GOLDEN, ids=[c["name"] for c in GOLDEN])
def test_golden_set_scoring(case):
    company = Company.model_validate(case["company"])
    jobs = [Job.model_validate({**j, "posted_date": date.fromisoformat(j["posted_date"])}) for j in case["jobs"]]
    result = score_company(company, jobs)
    if "expected_score_min" in case:
        assert result.total >= case["expected_score_min"], f"{case['name']}: score {result.total} < expected min {case['expected_score_min']}"
    if "expected_score_max" in case:
        assert result.total <= case["expected_score_max"], f"{case['name']}: score {result.total} > expected max {case['expected_score_max']}"
```

- [ ] **Step 3: Add `slow` marker to pytest config**

In `pyproject.toml`, append under `[tool.pytest.ini_options]`:

```toml
markers = [
    "slow: tests that hit external APIs (run weekly, not per PR)",
]
```

(Update existing `[tool.pytest.ini_options]` block — add the markers list.)

- [ ] **Step 4: Run, expect skipped without key (PR CI)**

```bash
pytest tests/test_ai_quality.py -v
```

Expected: skipped if no key.

- [ ] **Step 5: Commit**

```bash
git add tests/fixtures/golden_leads.json tests/test_ai_quality.py pyproject.toml
git commit -m "test: add IA quality golden-set tests (slow marker)"
```

---

## Task 18: Cloudflare Pages deployment runbook + README docs

**Files:**
- Modify: `README.md` (full version)
- Create: `docs/runbooks/cloudflare-deploy.md`

- [ ] **Step 1: Replace `README.md` with full docs**

```markdown
# Greensoft Leadgen

AI-driven B2B lead generation for Greensoft Technologies. Daily cron scrapes US ATS feeds (Greenhouse + Lever), classifies and scores prospects with Claude, generates personalized outreach copy, and serves the result at https://leads.greensofts.org.

Spec: `docs/superpowers/specs/2026-04-25-greensoft-leadgen-design.md`
Plan: `docs/superpowers/plans/2026-04-25-greensoft-leadgen-phase1.md`
Deploy: `docs/runbooks/cloudflare-deploy.md`

## Local development

```bash
python -m venv .venv
source .venv/bin/activate         # .venv\Scripts\activate on Windows
pip install -e ".[dev]"
cp .env.example .env              # add ANTHROPIC_API_KEY
pytest                            # all unit tests should pass
```

## Run the pipeline locally (consumes API tokens)

```bash
python -m scraper.main
```

Outputs:
- `data/leads.json` — full lead list
- `data/seen.json` — idempotency state
- stdout — JSON summary

## Add a company to the seed list

Edit `seed/companies.json`:

```json
{
  "name": "MyCompany",
  "ats_provider": "greenhouse",   // or "lever"
  "ats_slug": "mycompany",         // matches their boards.greenhouse.io/mycompany URL
  "industry": "Fintech"
}
```

Verify the slug works:

```bash
curl -s https://boards-api.greenhouse.io/v1/boards/mycompany/jobs | head
```

## Adjust scoring weights

Weights are encoded in `scraper/ai/prompts/score.txt` (instructions to the model) and `scraper/ai/score.py` (CAPS dict, used to clamp model output to declared maxes). Change both together.

## Add a partner (Cloudflare Access user)

1. Cloudflare → Zero Trust → Access → Applications → `leads.greensofts.org`
2. Edit the policy → add their Gmail address to "Include emails"
3. Save. They can immediately log in with magic link.

## Daily cron failure

GitHub will auto-email the repo admin. To re-run manually:
- GitHub → Actions → Daily Leadgen → Run workflow
- Or `gh workflow run daily-leadgen.yml`
```

- [ ] **Step 2: Create `docs/runbooks/cloudflare-deploy.md`**

```markdown
# Cloudflare Pages + Access deploy runbook

One-time setup. Estimated time: 15 min.

## Prerequisites
- Domain `greensofts.org` registered in Cloudflare (already done)
- GitHub repo `greensofttech-usa-mx/greensoft-leadgen` exists and is private
- You have admin access to both

## Step 1 — Create a Cloudflare Pages project

1. Cloudflare dashboard → Workers & Pages → Create application → Pages → Connect to Git
2. Authorize Cloudflare GitHub App if not already done; grant access to the `greensofttech-usa-mx` org
3. Select the `greensoft-leadgen` repo
4. Project name: `greensoft-leadgen`
5. Production branch: `main`
6. Build settings:
   - Framework preset: **None**
   - Build command: *(leave blank)*
   - Build output directory: `dashboard`
7. Click **Save and Deploy**. First deploy will succeed even before any cron runs (it'll just lack data).

## Step 2 — Custom domain

1. In the new Pages project → Custom domains → **Set up a custom domain**
2. Enter `leads.greensofts.org`
3. Cloudflare auto-creates the CNAME record in your zone (because the registrar is Cloudflare)
4. Wait ~30 sec for HTTPS cert to provision

## Step 3 — Cloudflare Access (auth)

1. Cloudflare → Zero Trust → Access → Applications → Add application → Self-hosted
2. App name: `Greensoft Leads`
3. Application domain: `leads.greensofts.org`
4. Identity providers: enable **One-time PIN** (default; sends magic links)
5. Click **Next**
6. Policy:
   - Action: **Allow**
   - Configure rules → Include → **Emails** → list each partner Gmail address one per row
7. Save policy
8. Save application
9. Test: open an incognito browser and visit `https://leads.greensofts.org`. You should see Cloudflare's login screen.

## Step 4 — Verify the cron workflow

1. GitHub → Repo → Settings → Secrets and variables → Actions → New repository secret
2. Name: `ANTHROPIC_API_KEY`, Value: your Anthropic key
3. Trigger a manual run: GitHub → Actions → Daily Leadgen → Run workflow
4. Wait ~5 min. Check the Actions log; the run should commit changes to `data/leads.json` and `dashboard/data/leads.json`
5. Cloudflare Pages auto-redeploys (~1 min after commit). Refresh `leads.greensofts.org` and your leads should appear.

## Adding a new partner

Cloudflare → Zero Trust → Access → Applications → `Greensoft Leads` → Policies → Allow → Add their email. Save. They can log in immediately.
```

- [ ] **Step 3: Commit**

```bash
git add README.md docs/runbooks/cloudflare-deploy.md
git commit -m "docs: full README and Cloudflare deploy runbook"
```

---

## Task 19: First production run + verification checklist

This task is a **manual checklist**, not code. It runs after the GitHub repo is created and the runbook from Task 18 is followed.

- [ ] **Step 1: Push the local repo to GitHub**

```bash
gh repo create greensofttech-usa-mx/greensoft-leadgen --private --source=. --remote=origin --push
```

(If `gh` is not installed: create the repo in the GitHub UI, then `git remote add origin git@github.com:greensofttech-usa-mx/greensoft-leadgen.git && git push -u origin main`.)

- [ ] **Step 2: Configure secrets**

```bash
gh secret set ANTHROPIC_API_KEY
```

Paste the key when prompted.

- [ ] **Step 3: Verify CI passes**

```bash
gh workflow list
gh run list --limit 3
```

Expected: any push triggers test runs. (Add a separate `test.yml` workflow if PR-on-push tests are needed — defer to Phase 2.)

- [ ] **Step 4: Manually trigger a production run**

```bash
gh workflow run daily-leadgen.yml
gh run watch
```

Expected: run completes in ≤10 min, commits to `data/leads.json` and `dashboard/data/leads.json`.

- [ ] **Step 5: Follow the Cloudflare runbook (Task 18 / `docs/runbooks/cloudflare-deploy.md`)**

After completing all steps in the runbook:

- [ ] `https://leads.greensofts.org` shows Cloudflare login
- [ ] After login with allowlisted Gmail, dashboard renders with leads from the latest run
- [ ] Filtering, sorting, search all work
- [ ] "Copy message" button works (test by pasting into a new email)
- [ ] "Mark contacted" persists across browser refresh (localStorage)

- [ ] **Step 6: Acceptance criteria check**

From the spec, verify each:

- [ ] `leads.greensofts.org` accessible, CF Access functioning
- [ ] Cron at 12:00 UTC runs daily (verify next morning)
- [ ] Generated message linter passes for all leads (no `[needs review]` subjects on real leads)
- [ ] Tests green in CI
- [ ] Anthropic console shows monthly cost projecting <$20 (after 7 days, extrapolate)
- [ ] README documents how to add seed companies, change scoring weights, invite a partner

- [ ] **Step 7: Final commit (touch-up if any docs were updated during verification)**

```bash
git add -A
git commit -m "chore: phase 1 verified in production" || echo "Nothing to commit"
git push
```

---

## Self-review (completed by writer of this plan)

Below is a verification of the plan against the spec, performed before handing off.

**Spec section coverage:**
- §1 Context → Task 1 README ✓
- §2 Out of scope → not implemented (correctly) ✓
- §3 Architecture → Tasks 5-13 build the 5 layers ✓
- §4 Stack → Tasks 1, 9, 16 ✓
- §5 Models → Task 3 ✓
- §6 IA layer → Tasks 9-12 ✓
- §7 Dashboard → Task 16 ✓
- §8 Auth → Task 18 (Cloudflare runbook) ✓
- §9 Error handling → Tasks 8, 11, 12 (each ATS isolated, AI parse failures swallowed) ✓
- §10 Testing → Tasks 3-13 each include unit tests; Task 17 adds quality tests ✓
- §11 Observability → Task 15 (workflow commit-message summary) ✓
- §12 Costs → covered in spec; not separately implemented ✓
- §13 Repo structure → Tasks 1-2 ✓
- §14 Roadmap → Phase 1 only is in this plan; Phases 2-4 are out of scope per spec ✓
- §15 Acceptance criteria → Task 19 step 6 ✓
- §16 Open questions → seed list (Task 14), weights (Task 11 prompt), forbidden phrases (Task 12 linter) ✓

**Type / signature consistency check:**
- `Lead.lead_id` format `{provider}:{slug}:{job_id}` — used in Tasks 3, 4, 13 consistently ✓
- `ScoreBreakdown` field names match across Tasks 3, 11, 13, 16 (qa_relevance, company_size, urgency, nearshore_fit, deal_size) ✓
- `OutreachMessage` field names (subject, body) match across Tasks 3, 12, 16 ✓
- `FilterResult` defined in Task 10, used in Task 13 ✓
- `ScoreResult` defined in Task 11, used in Task 13 ✓

**Placeholder / "TBD" scan:** None. Every step contains concrete code, exact commands, and expected outcomes.

**Open items intentionally left to manual judgment (not placeholders):**
- The 3 additional golden-set examples in Task 17 step 1 — engineer adds curated examples; the JSON skeleton is provided.
- Seed company slugs (Task 14): if any 404, engineer swaps; verification step is included.
- The 200-company seed: starts with 10 in Phase 1; expansion is a Phase 2 chore (out of scope).

---

**End of plan.**
