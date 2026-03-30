import json
import logging
from typing import Any, Optional, Dict, List, Union

logger = logging.getLogger(__name__)

def safe_json_loads(data: Union[str, bytes, None], default: Any = None) -> Any:
    """
    Safely load JSON data without throwing exceptions if it's malformed or None.
    
    Args:
        data: The JSON string or bytes to parse
        default: The fallback value to return if parsing fails (defaults to None)
        
    Returns:
        The parsed Python object, or the default value on failure
    """
    if data is None:
        return default
        
    try:
        return json.loads(data)
    except (json.JSONDecodeError, TypeError) as e:
        # We only log debug as this shouldn't pollute standard output for minor missing attributes
        logger.debug(f"Failed to parse JSON: {e}")
        return default
