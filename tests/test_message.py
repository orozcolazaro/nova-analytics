import json
from unittest.mock import patch
from scraper.ai.message import generate_message
from scraper.models import Company, ScoreBreakdown


def test_generate_message_returns_message_object():
    fake = json.dumps({
        "subject": "Helping Acme close 6 IT roles",
        "body": (
            "Hi there,\n\nNoticed Acme's Senior QA role has been open 4 weeks. "
            "Nova Analytics places nearshore engineers from Mexico — same model we use "
            "with Walmart, Coca-Cola FEMSA, and Nike.\n\n40-60% cost reduction, "
            "zero timezone gap, 14-day hiring.\n\nOpen to a 15-min call this week?\n\n"
            "[Your name]\nNova Analytics"
        ),
    })
    company = Company(name="Acme", ats_provider="greenhouse", ats_slug="acme", country="US")
    breakdown = ScoreBreakdown(qa_relevance=20, company_size=18, urgency=15, nearshore_fit=15, deal_size=12)
    with patch("scraper.ai.message.call_claude", return_value=fake):
        msg = generate_message(company, [], breakdown, "rationale")
    assert msg.subject.startswith("Helping Acme")
    assert "Nova Analytics" in msg.body


def test_generate_message_falls_back_on_bad_json():
    company = Company(name="X", ats_provider="lever", ats_slug="x", country="US")
    breakdown = ScoreBreakdown(qa_relevance=10, company_size=10, urgency=10, nearshore_fit=10, deal_size=5)
    with patch("scraper.ai.message.call_claude", return_value="garbage"):
        msg = generate_message(company, [], breakdown, "rationale")
    assert msg.subject == "[needs review] X"
    assert "manual review" in msg.body.lower()
