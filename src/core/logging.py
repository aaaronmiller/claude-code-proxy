import logging
from src.core.config import config

# Parse log level - extract just the first word to handle comments
log_level = config.log_level.split()[0].upper()

# Validate and set default if invalid
valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
if log_level not in valid_levels:
    log_level = "INFO"

# Logging Configuration
logging.basicConfig(
    level=getattr(logging, log_level),
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Configure uvicorn logging - show errors, warnings; control access separately
for uvicorn_logger in ["uvicorn"]:
    logging.getLogger(uvicorn_logger).setLevel(logging.WARNING)

# Always show uvicorn errors
logging.getLogger("uvicorn.error").setLevel(logging.ERROR)
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
