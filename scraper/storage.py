import json
from datetime import date, datetime
from pathlib import Path
from typing import Iterable
from scraper.models import Lead


def _json_default(obj):
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    raise TypeError(f"Cannot serialize {type(obj)}")


class LeadStore:
    def __init__(self, path: Path):
        self.path = Path(path)

    def load(self) -> list[Lead]:
        if not self.path.exists():
            return []
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        return [Lead.model_validate(item) for item in raw]

    def save(self, leads: Iterable[Lead]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        data = [l.model_dump(mode="json") for l in leads]
        self.path.write_text(
            json.dumps(data, indent=2, default=_json_default, ensure_ascii=False),
            encoding="utf-8",
        )

    def upsert(self, incoming: Iterable[Lead]) -> None:
        existing = {l.lead_id: l for l in self.load()}
        for lead in incoming:
            existing[lead.lead_id] = lead
        self.save(existing.values())


class SeenStore:
    def __init__(self, path: Path):
        self.path = Path(path)
        self._cache: dict[str, str] = {}
        if self.path.exists():
            self._cache = json.loads(self.path.read_text(encoding="utf-8"))

    def has_seen(self, lead_id: str) -> bool:
        return lead_id in self._cache

    def mark_seen(self, lead_id: str) -> None:
        self._cache[lead_id] = datetime.utcnow().isoformat()
        self._flush()

    def _flush(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self._cache, indent=2), encoding="utf-8")
