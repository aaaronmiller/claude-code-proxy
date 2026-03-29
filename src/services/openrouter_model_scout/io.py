"""
Atomic file I/O utilities.
Provides crash-safe writes and corruption recovery.
"""

import json
import logging
import os
import tempfile
from datetime import datetime
from pathlib import Path
from datetime import timezone
from typing import Any, Optional

logger = logging.getLogger(__name__)


def atomic_json_write(data: Any, target_path: str | Path) -> None:
    """
    Write data to JSON file atomically (write to temp, then rename).

    Args:
        data: Serializable data to write
        target_path: Destination file path
    """
    target_path = Path(target_path)
    target_path.parent.mkdir(parents=True, exist_ok=True)

    # Write to temporary file in same directory (ensure atomic rename on POSIX)
    with tempfile.NamedTemporaryFile(
        mode='w',
        dir=target_path.parent,
        suffix='.tmp',
        delete=False,
        encoding='utf-8'
    ) as tmp:
        tmp_path = Path(tmp.name)
        json.dump(data, tmp, indent=2, ensure_ascii=False)
        tmp.flush()
        os.fsync(tmp.fileno())  # Force write to disk

    # Atomic replace
    tmp_path.replace(target_path)


def load_json(file_path: str | Path) -> Any:
    """
    Load and deserialize JSON file.

    Args:
        file_path: Path to JSON file

    Returns:
        Deserialized data

    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If file contains invalid JSON
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def backup_corrupted_file(corrupted_path: str | Path) -> Optional[str]:
    """
    Backup corrupted file with timestamp suffix.

    Args:
        corrupted_path: Path to corrupted file

    Returns:
        Path to backup file if created, None otherwise
    """
    path = Path(corrupted_path)
    if not path.exists():
        return None

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup_path = path.with_suffix(f".corrupt.{timestamp}{path.suffix}")

    try:
        path.rename(backup_path)
        logger.warning(f"Backed up corrupted file to: {backup_path}")
        return str(backup_path)
    except Exception as e:
        logger.error(f"Failed to backup corrupted file: {e}")
        return None
