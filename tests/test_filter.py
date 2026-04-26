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
