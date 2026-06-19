"""S1-04: dead models (OPEN circuit breaker) must be excluded from the OpenRouter
native model list so we never keep routing to a known-broken endpoint (the 404/500
storm the user repeatedly hit). Characterization test for existing behavior in
src/core/client.py:_build_or_models_list. See ai-gateway/plan/06-SPRINT-1-TICKETS.md."""
from src.core import client
from src.core.circuit_breaker import CircuitBreaker


def _open_breaker(name: str, threshold: int = 2) -> CircuitBreaker:
    cb = CircuitBreaker(name, failure_threshold=threshold, success_threshold=1, timeout=300)
    for _ in range(threshold + 1):
        cb._record_failure(Exception("boom"))
    return cb


def test_open_breaker_excluded_from_or_list(monkeypatch):
    dead, good, primary = "prov/dead-free", "prov/good-free", "prov/primary"
    breakers = {dead: _open_breaker(dead)}
    monkeypatch.setattr(client, "_circuit_breakers", breakers)
    assert breakers[dead].is_open
    out = client._build_or_models_list(primary, [dead, good])
    assert dead not in out
    assert primary in out and good in out


def test_unknown_model_not_open(monkeypatch):
    monkeypatch.setattr(client, "_circuit_breakers", {})
    assert client._is_cb_open("prov/never-seen") is False


def test_all_open_falls_back_to_primary(monkeypatch):
    primary, f1 = "prov/primary", "prov/f1"
    breakers = {primary: _open_breaker(primary), f1: _open_breaker(f1)}
    monkeypatch.setattr(client, "_circuit_breakers", breakers)
    out = client._build_or_models_list(primary, [f1])
    # never empty: OR still gets one valid model rather than a malformed request
    assert out == [primary]
