"""Atomic local persistence for typed quota meters."""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import asdict, fields
from pathlib import Path
from typing import Iterable

from src.core.quota_sources import QuotaMeter

STORE_SCHEMA_VERSION = "1.0.0"
_METER_FIELDS = {field.name for field in fields(QuotaMeter)}


class QuotaMeterStore:
    """Persist last-known quota facts without provider credentials or payloads."""

    def __init__(self, path: str | os.PathLike[str]) -> None:
        self.path = Path(path).expanduser()

    def load(self) -> list[QuotaMeter]:
        """Return validated meters, or an empty list for missing/corrupt state."""
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, TypeError):
            return []

        if (
            not isinstance(payload, dict)
            or payload.get("schema_version") != STORE_SCHEMA_VERSION
            or not isinstance(payload.get("meters"), list)
        ):
            return []

        meters: list[QuotaMeter] = []
        for raw in payload["meters"]:
            meter = self._parse_meter(raw)
            if meter is None:
                return []
            meters.append(meter)
        return meters

    def save(self, meters: Iterable[QuotaMeter]) -> None:
        """Atomically replace the store with a complete typed snapshot."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": STORE_SCHEMA_VERSION,
            "meters": [asdict(meter) for meter in meters],
        }
        fd, tmp_name = tempfile.mkstemp(
            prefix=f".{self.path.name}.",
            suffix=".tmp",
            dir=str(self.path.parent),
        )
        tmp_path = Path(tmp_name)
        try:
            os.chmod(tmp_path, 0o600)
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                fd = -1
                json.dump(payload, handle, separators=(",", ":"), sort_keys=True)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(tmp_path, self.path)
        except Exception:
            if fd >= 0:
                try:
                    os.close(fd)
                except OSError:
                    pass
            try:
                tmp_path.unlink(missing_ok=True)
            except OSError:
                pass
            raise

    @staticmethod
    def _parse_meter(raw) -> QuotaMeter | None:
        if not isinstance(raw, dict) or set(raw) - _METER_FIELDS:
            return None
        required = {
            "id",
            "provider",
            "unit",
            "window_seconds",
            "limit",
            "remaining",
        }
        if not required.issubset(raw):
            return None
        try:
            meter = QuotaMeter(**raw)
            valid = (
                bool(meter.id)
                and bool(meter.provider)
                and meter.window_seconds >= 0
                and meter.limit >= 0
                and 0 <= meter.remaining <= meter.limit
                and 0.0 <= meter.confidence <= 1.0
            )
        except (TypeError, ValueError):
            return None
        if not valid:
            return None
        return meter
