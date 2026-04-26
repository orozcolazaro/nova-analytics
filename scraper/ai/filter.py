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
