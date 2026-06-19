"""Unit tests for secret-masking (FR-035).

Covers patterns from research.md R12:
  - OpenAI API keys   (sk-<48+ alphanum>)
  - OpenRouter keys   (sk-or-<32+>)
  - Anthropic legacy  (sk-ant-<...>)
  - Anthropic OAuth   (sk-ant-oat01-<...>)
  - Bearer tokens     (Bearer <...>)
  - JWT tokens        (xxx.yyy.zzz base64url)
  - Long-hex tokens   (40+ hex chars)

Also asserts that non-secret strings are returned unchanged.
"""

from __future__ import annotations

import pytest
from src.services.observability.audit_log import mask_secret


@pytest.mark.parametrize(
    "secret,expected",
    [
        # OpenAI key (>12 chars)
        ("sk-0123456789abcdefghijklmnopqrstuvwXYZ", "sk-012...XYZ"),
        # OpenRouter key
        ("sk-or-0123456789abcdefghijklmnopqrstuvwXYZ", "sk-or-012...XYZ"),
        # Anthropic legacy (sk-ant-*)
        ("sk-ant-0123456789abcdefghijklmnopqrstuvwXYZ", "sk-ant-012...XYZ"),
        # Anthropic OAuth
        ("sk-ant-oat01-0123456789abcdefghijklmnopqrstuvwXYZ", "sk-ant-oat01-012...XYZ"),
        # Bearer token (>=12)
        ("Bearer abcdefghijklmnopqrstuvwxyz", "Bearer abcd...xyz"),
        # JWT (3 base64url parts)
        (
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c",
            "eyJh...5c",
        ),  # simplified check; pattern matches full JWT; mask_first4_last4 applies
        # Long hex (GitHub token) — first 4 + last 4 of the full string
        ("0123456789abcdef" * 4, "0123...cdef"),
        # Short secret (<12) fully masked
        ("sk-abcd", "***"),
        ("Bearer abc", "***"),
    ],
)
def test_mask_secret_patterns(secret, expected):
    masked = mask_secret(secret)
    assert masked == expected


def test_mask_secret_non_secret():
    assert mask_secret("hello world") == "hello world"
    assert mask_secret("not-a-secret-key") == "not-a-secret-key"
    assert mask_secret("") == ""
    assert mask_secret(123) == "123"


def test_mask_dict_secrets_nested():
    from src.services.observability.audit_log import mask_dict_secrets

    data = {
        "api_key": "sk-0123456789abcdefghijklmnopqrstuvwXYZ",
        "nested": {"token": "Bearer abcdefghijklmnopqrstuvwxyz", "safe": "visible"},
        "list": ["sk-ant-0123456789abcdefghijklmnopqrstuvwXYZ", "plain"],
    }
    masked = mask_dict_secrets(data)
    assert masked["api_key"] == "sk-012...XYZ"
    assert masked["nested"]["token"] == "Bearer abcd...xyz"
    assert masked["nested"]["safe"] == "visible"
    assert masked["list"][0] == "sk-ant-012...XYZ"
    assert masked["list"][1] == "plain"
