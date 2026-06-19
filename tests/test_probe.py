"""L2/F03: latency-probe metric + classification logic (offline, injected HTTP)."""
from src.services.probe import probe_model, classify


def _post(status, body, elapsed):
    return lambda url, headers, json, timeout: (status, body, elapsed)


def test_ok_with_tps():
    r = probe_model("groq", "https://x/v1", "m", "k",
                    http_post=_post(200, {"usage": {"completion_tokens": 10}}, 0.5))
    assert r.ok and r.error_class == "ok"
    assert r.tokens_out == 10 and r.tokens_per_s == 20.0   # 10 / 0.5s


def test_rate_limit_and_server_and_network():
    assert probe_model("p", "u", "m", "k", http_post=_post(429, None, 0.1)).error_class == "rate_limit"
    assert probe_model("p", "u", "m", "k", http_post=_post(500, None, 0.1)).error_class == "server"
    n = probe_model("p", "u", "m", "k", http_post=_post(0, None, 0.1))
    assert n.error_class == "network" and n.ok is False


def test_no_tokens_no_tps():
    r = probe_model("p", "u", "m", "k", http_post=_post(200, {"usage": {"completion_tokens": 0}}, 0.3))
    assert r.ok and r.tokens_per_s is None


def test_classify_table():
    assert classify(200) == "ok"
    assert classify(401) == "auth" and classify(403) == "auth"
    assert classify(400) == "bad_request" and classify(422) == "bad_request"
    assert classify(503) == "server"
    assert classify(0) == "network"
    assert classify(418) == "other"
