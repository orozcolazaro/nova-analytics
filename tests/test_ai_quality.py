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
