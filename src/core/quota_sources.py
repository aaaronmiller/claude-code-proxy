"""Quota source adapters for model-scan rotation decisions."""

from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Protocol


@dataclass(frozen=True)
class QuotaSample:
    provider: str
    remaining_fraction: float
    reset_at: str = ""
    unit: str = ""
    source: str = ""
    observed_at: float = 0.0


class QuotaSource(Protocol):
    name: str

    def samples(self) -> list[QuotaSample]:
        ...


def _sample(provider: str, remaining: float, source: str, **extra) -> QuotaSample:
    return QuotaSample(
        provider=provider.lower(),
        remaining_fraction=max(0.0, min(1.0, float(remaining))),
        source=source,
        observed_at=float(extra.pop("observed_at", 0.0) or time.time()),
        **extra,
    )


class TokscaleSQLiteSource:
    name = "tokscale"

    def __init__(self, db_path: str | os.PathLike[str] | None = None) -> None:
        self.db_path = Path(db_path or os.environ.get("TOKSCALE_DB", "~/.tokscale/tokscale.db")).expanduser()

    def samples(self) -> list[QuotaSample]:
        if not self.db_path.exists():
            return []
        conn = sqlite3.connect(str(self.db_path))
        try:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT provider, remaining_fraction, reset_at, unit FROM provider_quota"
            ).fetchall()
            return [
                _sample(r["provider"], r["remaining_fraction"], self.name, reset_at=r["reset_at"] or "", unit=r["unit"] or "")
                for r in rows
            ]
        except sqlite3.Error:
            return []
        finally:
            conn.close()


class CcusageSource:
    name = "ccusage"

    def samples(self) -> list[QuotaSample]:
        try:
            proc = subprocess.run(["ccusage", "--json"], capture_output=True, text=True, timeout=5)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return []
        if proc.returncode != 0:
            return []
        try:
            data = json.loads(proc.stdout)
        except json.JSONDecodeError:
            return []
        providers = data.get("providers", data if isinstance(data, dict) else {})
        result = []
        for provider, item in providers.items():
            if isinstance(item, dict) and "remaining_fraction" in item:
                result.append(_sample(provider, item["remaining_fraction"], self.name, unit=item.get("unit", "")))
        return result


class StaticQuotaSource:
    def __init__(self, name: str, data: dict[str, float]) -> None:
        self.name = name
        self.data = data

    def samples(self) -> list[QuotaSample]:
        return [_sample(provider, remaining, self.name) for provider, remaining in self.data.items()]


PRECEDENCE = {
    "tokscale": 100,
    "ccusage": 80,
    "model_scan_quota": 70,
    "billing": 60,
    "rate_limiter": 50,
    "usage_tracker": 40,
}


def merge_quota_samples(samples: Iterable[QuotaSample]) -> dict[str, QuotaSample]:
    """Merge by provider using source precedence, then freshness."""
    merged: dict[str, QuotaSample] = {}
    for sample in samples:
        current = merged.get(sample.provider)
        if current is None:
            merged[sample.provider] = sample
            continue
        score = (PRECEDENCE.get(sample.source, 0), sample.observed_at)
        cur_score = (PRECEDENCE.get(current.source, 0), current.observed_at)
        if score >= cur_score:
            merged[sample.provider] = sample
    return merged
