import pytest
from datetime import date
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
