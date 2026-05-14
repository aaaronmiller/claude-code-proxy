#!/usr/bin/env python3
"""CI lint: fail if any file under src/ (excluding allowed exceptions) calls os.environ.get or os.getenv directly.

Allowed exceptions:
 - src/core/config_resolver.py (central env handling)
 - any file matching src/core/config*.py (legacy shim during deprecation)
 - Possibly tests? But scope limited to src/.

This enforces Constitution Principle VI: All env access must go through ConfigResolver
to guarantee provenance, change-events, and secret masking.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# Patterns that indicate direct os.environ access
BAD_PATTERNS = [
    re.compile(r"\bos\.environ\.get\s*\("),
    re.compile(r"\bos\.getenv\s*\("),
    re.compile(r"\bos\.environ\s*\[.*\]"),  # also block direct indexing os.environ["X"]
]

# Directories/files to exclude
EXCLUDE_PATHS = {
    Path("src/core/config_resolver.py"),
}


# Also exclude any file under src/core that starts with config (e.g., config.py shim)
def is_excluded(p: Path) -> bool:
    if p in EXCLUDE_PATHS:
        return True
    # Check if path matches src/core/config*.py
    if (
        p.parent == Path("src/core")
        and p.name.startswith("config")
        and p.suffix == ".py"
    ):
        return True
    return False


def main() -> int:
    root = Path(__file__).parent.parent  # repo root
    src_dir = root / "src"
    failures = []

    for pyfile in src_dir.rglob("*.py"):
        rel = pyfile.relative_to(root)
        if is_excluded(rel):
            continue
        try:
            content = pyfile.read_text(encoding="utf-8")
        except Exception:
            continue
        lines = content.splitlines()
        for lineno, line in enumerate(lines, start=1):
            # Skip comments/strings? We'll be simple: any occurrence is a violation
            for pat in BAD_PATTERNS:
                if pat.search(line):
                    failures.append((str(rel), lineno, line.strip()))
                    break
    if failures:
        print(
            "Direct os.environ access detected in the following locations:\n",
            file=sys.stderr,
        )
        for file, lineno, line in failures:
            print(f"  {file}:{lineno}: {line}", file=sys.stderr)
        print(
            "\nAll environment variable access must go through ConfigResolver.",
            file=sys.stderr,
        )
        return 1
    else:
        print(
            "✓ No direct os.environ calls found in src/ (allowed config files excluded).",
            file=sys.stderr,
        )
        return 0


if __name__ == "__main__":
    sys.exit(main())
