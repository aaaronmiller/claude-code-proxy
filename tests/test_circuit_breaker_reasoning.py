"""Reasoning models that truncate on token budget (reasoning tokens, empty content,
finish_reason=length) are RESPONSIVE - they must not be penalized by the circuit breaker
(misattribution would demote a healthy model). Verified live on Groq gpt-oss-120b."""
from src.core.circuit_breaker import CircuitBreaker


def _cb():
    return CircuitBreaker("m", failure_threshold=3, success_threshold=1, timeout=300)


# Real shape from a live Groq gpt-oss-120b call (max_tokens too low for the answer).
REASONING_TRUNCATED = {
    "choices": [{"finish_reason": "length",
                 "message": {"role": "assistant", "content": "", "reasoning": "User asks ..."}}],
    "usage": {"completion_tokens": 20, "completion_tokens_details": {"reasoning_tokens": 18}},
}


def test_reasoning_truncated_not_penalized():
    cb = _cb()
    assert cb.record_parse_ok(REASONING_TRUNCATED) is False   # no usable final answer
    assert cb.stats.soft_failure_count == 0                   # but model NOT penalized


def test_reasoning_via_usage_tokens_only():
    cb = _cb()
    resp = {"choices": [{"finish_reason": "length", "message": {"role": "assistant", "content": ""}}],
            "usage": {"completion_tokens_details": {"reasoning_tokens": 5}}}
    cb.record_parse_ok(resp)
    assert cb.stats.soft_failure_count == 0


def test_genuinely_empty_still_penalized():
    cb = _cb()
    resp = {"choices": [{"finish_reason": "stop", "message": {"role": "assistant", "content": ""}}]}
    assert cb.record_parse_ok(resp) is False
    assert cb.stats.soft_failure_count == 1                   # unchanged behavior


def test_length_no_reasoning_still_penalized():
    cb = _cb()
    resp = {"choices": [{"finish_reason": "length", "message": {"role": "assistant", "content": ""}}]}
    cb.record_parse_ok(resp)
    assert cb.stats.soft_failure_count == 1


def test_valid_content_ok():
    cb = _cb()
    resp = {"choices": [{"finish_reason": "stop", "message": {"role": "assistant", "content": "hi"}}]}
    assert cb.record_parse_ok(resp) is True
    assert cb.stats.soft_failure_count == 0


def test_stream_finish_reasoning_param():
    cb = _cb()
    assert cb.record_stream_finish("length", False, False, had_reasoning=True) is False
    assert cb.stats.soft_failure_count == 0
    cb2 = _cb()
    cb2.record_stream_finish("length", False, False)   # default had_reasoning=False
    assert cb2.stats.soft_failure_count == 1
