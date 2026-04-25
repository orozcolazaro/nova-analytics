from datetime import date, datetime
from typing import Literal
from pydantic import BaseModel, Field, computed_field, HttpUrl


ATSProvider = Literal["greenhouse", "lever", "occ", "computrabajo"]
LeadStatus = Literal["new", "contacted", "replied", "client", "dead", "needs_retry", "needs_review", "archived"]


class SeedCompany(BaseModel):
    name: str
    ats_provider: ATSProvider
    ats_slug: str
    homepage: HttpUrl | None = None
    linkedin: HttpUrl | None = None
    industry: str | None = None
    notes: str | None = None


class Job(BaseModel):
    id: str
    title: str
    url: HttpUrl
    location: str
    remote_friendly: bool
    posted_date: date
    tech_stack: list[str] = Field(default_factory=list)
    raw_description: str | None = None  # full JD for IA, not persisted to leads.json

    @computed_field
    @property
    def days_open(self) -> int:
        return max(0, (date.today() - self.posted_date).days)


class Company(BaseModel):
    name: str
    ats_provider: ATSProvider
    ats_slug: str
    homepage: HttpUrl | None = None
    linkedin: HttpUrl | None = None
    country: str = "US"
    size_estimate: str | None = None
    industry: str | None = None
    first_seen: date = Field(default_factory=date.today)


class ScoreBreakdown(BaseModel):
    qa_relevance: int = Field(ge=0, le=25)
    company_size: int = Field(ge=0, le=20)
    urgency: int = Field(ge=0, le=20)
    nearshore_fit: int = Field(ge=0, le=20)
    deal_size: int = Field(ge=0, le=15)

    @computed_field
    @property
    def total(self) -> int:
        return (
            self.qa_relevance + self.company_size + self.urgency
            + self.nearshore_fit + self.deal_size
        )


class OutreachMessage(BaseModel):
    subject: str
    body: str
    channel: Literal["email"] = "email"


class Lead(BaseModel):
    lead_id: str
    company: Company
    active_jobs: list[Job]
    qa_jobs_count: int
    all_it_jobs_count: int
    lead_score: int = Field(ge=0, le=100)
    score_breakdown: ScoreBreakdown
    score_rationale: str
    outreach_message: OutreachMessage
    status: LeadStatus = "new"
    first_seen: date = Field(default_factory=date.today)
    last_updated: datetime = Field(default_factory=datetime.utcnow)
