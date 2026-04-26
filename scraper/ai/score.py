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
