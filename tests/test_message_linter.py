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
