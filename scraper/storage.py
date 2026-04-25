import json
import logging
import time
from datetime import date, datetime
from pathlib import Path
from typing import Iterable
from pydantic import ValidationError
from scraper.models import Lead

log = logging.getLogger(__name__)


def _json_default(obj):
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    raise TypeError(f"Cannot serialize {type(obj)}")


def _atomic_write_text(path: Path, content: str) -> None:
    """Write to a sibling .tmp then atomically rename. POSIX atomic, Windows best-effort."""
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(path)


def _quarantine_corrupt(path: Path, error: Exception) -> None:
    backup = path.with_suffix(f".corrupt.{int(time.time())}")
    log.error("Corrupt %s: %s — moved to %s", path, error, backup)
    path.rename(backup)


class LeadStore:
    def __init__(self, path: Path):
        self.path = Path(path)

    def load(self) -> list[Lead]:
        if not self.path.exists():
            return []
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            _quarantine_corrupt(self.path, e)
            return []
        leads: list[Lead] = []
        for item in raw:
            try:
                leads.append(Lead.model_validate(item))
            except ValidationError as e:
                log.warning("Skipping invalid lead in %s: %s", self.path, e)
        return leads

    def save(self, leads: Iterable[Lead]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        data = [lead.model_dump(mode="json") for lead in leads]
        _atomic_write_text(
            self.path,
            json.dumps(data, indent=2, default=_json_default, ensure_ascii=False),
        )

    def upsert(self, incoming: Iterable[Lead]) -> None:
        existing = {lead.lead_id: lead for lead in self.load()}
        for lead in incoming:
            existing[lead.lead_id] = lead
        self.save(existing.values())


class SeenStore:
    def __init__(self, path: Path):
        self.path = Path(path)
        self._cache: dict[str, str] = {}
        if self.path.exists():
            try:
                self._cache = json.loads(self.path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as e:
                _quarantine_corrupt(self.path, e)
                self._cache = {}

    def has_seen(self, lead_id: str) -> bool:
        return lead_id in self._cache

    def mark_seen(self, lead_id: str) -> None:
        self._cache[lead_id] = datetime.utcnow().isoformat()
        self._flush()

    def _flush(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        _atomic_write_text(self.path, json.dumps(self._cache, indent=2))
