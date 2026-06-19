from __future__ import annotations

import sqlite3

from src.core.model_scan_binder import ResolvedBinding
from src.core.quota_sources import QuotaSample, TokscaleSQLiteSource, merge_quota_samples
from src.core.rotation import RotationState, choose_binding, record_rate_limit


def _binding(model: str, provider: str = "") -> ResolvedBinding:
    return ResolvedBinding(api_model=model, base_url="", cascade=(), source="snapshot", provider=provider)


def test_tokscale_sqlite_source_reads_provider_quota(tmp_path):
    db = tmp_path / "tokscale.db"
    conn = sqlite3.connect(db)
    conn.execute("CREATE TABLE provider_quota (provider TEXT, remaining_fraction REAL, reset_at TEXT, unit TEXT)")
    conn.execute("INSERT INTO provider_quota VALUES ('openrouter', 0.5, 'soon', 'tokens')")
    conn.commit()
    conn.close()

    samples = TokscaleSQLiteSource(db).samples()

    assert samples[0].provider == "openrouter"
    assert samples[0].remaining_fraction == 0.5


def test_quota_merge_uses_precedence_then_freshness():
    merged = merge_quota_samples(
        [
            QuotaSample("p", 0.9, source="usage_tracker", observed_at=100),
            QuotaSample("p", 0.2, source="tokscale", observed_at=1),
        ]
    )
    assert merged["p"].remaining_fraction == 0.2


def test_rotation_advances_when_provider_drained_and_free_floor_engages():
    primary = _binding("paid/model", "paid")
    fallback = _binding("openrouter/free:free", "openrouter")
    floor = _binding("free/floor:free", "free")
    quotas = {"paid": QuotaSample("paid", 0.0, source="tokscale")}

    assert choose_binding(primary, [fallback], lane="interactive", quotas=quotas, free_floor=floor) == fallback
    assert choose_binding(primary, [], lane="interactive", quotas=quotas, free_floor=floor) == floor


def test_standby_lane_spends_no_paid_quota():
    paid = _binding("paid/model", "paid")
    free = _binding("openrouter/free:free", "openrouter")

    assert choose_binding(paid, [free], lane="standby", quotas={}) == free


def test_cooldown_prevents_flapping():
    primary = _binding("paid/model", "paid")
    fallback = _binding("other/model", "other")
    state = RotationState(cooldown_until={})
    record_rate_limit(primary, state, cooldown_s=60)

    chosen = choose_binding(primary, [fallback], lane="interactive", quotas={}, state=state, now=1)

    assert chosen == fallback
