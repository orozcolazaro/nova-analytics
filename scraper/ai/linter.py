import re
from dataclasses import dataclass, field
from scraper.models import OutreachMessage

FORBIDDEN_PHRASES = [
    "revolutionize", "leverage synergies", "game-changing",
    "in today's fast-paced world", "synergize", "cutting-edge",
    "world-class", "best-in-class", "paradigm shift",
    "unlock potential", "take to the next level",
    "hope this email finds you well", "just wanted to reach out",
    "circle back", "touch base", "low-hanging fruit",
]

MAX_WORDS = 110
MAX_SUBJECT_WORDS = 8


@dataclass
class LintResult:
    passed: bool
    issues: list[str] = field(default_factory=list)


def _word_count(text: str) -> int:
    return len(re.findall(r"\b\w+\b", text))


def lint_message(msg: OutreachMessage) -> LintResult:
    issues: list[str] = []
    body_words = _word_count(msg.body)
    if body_words > MAX_WORDS:
        issues.append(f"body word count {body_words} exceeds max {MAX_WORDS}")
    subj_words = _word_count(msg.subject)
    if subj_words > MAX_SUBJECT_WORDS:
        issues.append(f"subject word count {subj_words} exceeds max {MAX_SUBJECT_WORDS}")
    lower_body = msg.body.lower()
    lower_subj = msg.subject.lower()
    for phrase in FORBIDDEN_PHRASES:
        if phrase in lower_body or phrase in lower_subj:
            issues.append(f"forbidden phrase: '{phrase}'")
    if "?" not in msg.body:
        issues.append("missing closing question (CTA)")
    return LintResult(passed=len(issues) == 0, issues=issues)
