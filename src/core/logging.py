import logging
from src.core.config import config


class SessionContextFilter(logging.Filter):
    """Attach the active routing profile id to standard log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        if hasattr(record, "session_id"):
            return True
        try:
            from src.core.profiles import current_profile_name

            record.session_id = current_profile_name() or "-"
        except Exception:
            record.session_id = "-"
        return True


# Parse log level - extract just the first word to handle comments
log_level = config.log_level.split()[0].upper()

# Validate and set default if invalid
valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
if log_level not in valid_levels:
    log_level = "INFO"

_original_record_factory = logging.getLogRecordFactory()


def _session_log_record_factory(*args, **kwargs):
    record = _original_record_factory(*args, **kwargs)
    try:
        from src.core.profiles import current_profile_name

        record.session_id = current_profile_name() or "-"
    except Exception:
        record.session_id = "-"
    return record


logging.setLogRecordFactory(_session_log_record_factory)

# Logging Configuration
logging.basicConfig(
    level=getattr(logging, log_level),
    format="%(asctime)s - %(levelname)s - session=%(session_id)s - %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)

_session_filter = SessionContextFilter()
for _handler in logging.getLogger().handlers:
    _handler.addFilter(_session_filter)

# Configure uvicorn logging - show errors, warnings; control access separately
for uvicorn_logger in ["uvicorn"]:
    logging.getLogger(uvicorn_logger).setLevel(logging.WARNING)

# Always show uvicorn errors
logging.getLogger("uvicorn.error").setLevel(logging.ERROR)
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
