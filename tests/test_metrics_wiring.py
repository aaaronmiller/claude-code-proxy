"""Prometheus metrics must be fed from the real runtime paths, not just defined.

Covers the two metrics that previously had no callers (empty Grafana panels):
cascade switches (via log_cascade) and circuit-breaker state (via transitions).
"""
import asyncio

from src.api import metrics_api as M


def _val(metric, **labels):
    return metric.labels(**labels)._value.get()


def test_cascade_switch_increments_counter_via_log_cascade():
    from src.api.websocket_logs import log_cascade

    before = _val(M.cascade_switches_total, from_model="mA", to_model="mB", reason="rate_limit")
    log_cascade(model="mA", action="switch", from_model="mA", to_model="mB", reason="rate_limit")
    after = _val(M.cascade_switches_total, from_model="mA", to_model="mB", reason="rate_limit")
    assert after == before + 1


def test_non_switch_cascade_does_not_increment():
    from src.api.websocket_logs import log_cascade

    before = _val(M.cascade_switches_total, from_model="x", to_model="y", reason="ok")
    log_cascade(model="x", action="attempt", from_model="x", to_model="y", reason="ok")
    after = _val(M.cascade_switches_total, from_model="x", to_model="y", reason="ok")
    assert after == before  # only action=="switch" is counted


def test_circuit_breaker_state_gauge_tracks_transitions():
    from src.core.circuit_breaker import CircuitBreaker, CircuitState

    cb = CircuitBreaker(name="prov/model-x", failure_threshold=2)

    async def boom():
        raise RuntimeError("down")

    # closed → still 0 until threshold met
    asyncio.run(_fail(cb, boom))
    assert _val(M.circuit_breaker_state, model="prov/model-x") == 0  # 1 failure < threshold
    asyncio.run(_fail(cb, boom))
    # 2nd failure trips CLOSED → OPEN (gauge value 2)
    assert _val(M.circuit_breaker_state, model="prov/model-x") == 2
    assert cb.state == CircuitState.OPEN


async def _fail(cb, fn):
    try:
        await cb.execute(fn)
    except Exception:
        pass
