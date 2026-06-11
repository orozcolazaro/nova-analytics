import json
from unittest.mock import patch
from datetime import date
from scraper.ai.score import score_company
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
