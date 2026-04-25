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
