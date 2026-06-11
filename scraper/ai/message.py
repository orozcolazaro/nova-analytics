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
            body="Message generation failed — manual review required.\n\n[Your name]\nNova Analytics",
        )
