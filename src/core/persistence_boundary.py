"""Context-local guard for computations that must never persist configuration."""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from typing import Iterator


class PersistenceBlocked(RuntimeError):
    """Raised when a preview path reaches a persistent mutation boundary."""


_PREVIEW_DEPTH: ContextVar[int] = ContextVar("non_persisting_preview_depth", default=0)


def preview_is_non_persisting() -> bool:
    """Return whether the current context is inside a non-persisting preview."""
    return _PREVIEW_DEPTH.get() > 0


def require_persistence_allowed(surface: str) -> None:
    """Fail before mutation when the current context is a preview."""
    if preview_is_non_persisting():
        raise PersistenceBlocked(
            f"preview cannot mutate persistent {surface} state"
        )


@contextmanager
def non_persisting_preview() -> Iterator[None]:
    """Mark a nest-safe context in which persistent writes are forbidden."""
    token = _PREVIEW_DEPTH.set(_PREVIEW_DEPTH.get() + 1)
    try:
        yield
    finally:
        _PREVIEW_DEPTH.reset(token)
