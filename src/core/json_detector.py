"""
JSON detection utility for TOON conversion analysis.

Detects JSON in request/response content to analyze if TOON format
would provide token savings.
"""

import json
import re
from typing import Tuple, List, Dict, Any


class JSONDetector:
    """
    Detect and analyze JSON content in requests/responses.

    Used for session-level TOON conversion analysis, not per-request.
    """

    # Regex to find JSON-like structures
    JSON_PATTERN = re.compile(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}|\[[^\[\]]*(?:\[[^\[\]]*\][^\[\]]*)*\]')

    # Minimum JSON size to consider (bytes)
    MIN_JSON_SIZE = 100

    @staticmethod
    def detect_json_in_text(text: str) -> Tuple[bool, int, List[Dict[str, Any]]]:
        """
        Detect JSON structures in text content.

        Args:
            text: Text to analyze

        Returns:
            (has_json, total_bytes, json_objects)
        """
        if not text or len(text) < JSONDetector.MIN_JSON_SIZE:
            return False, 0, []

        json_objects = []
        total_bytes = 0

        # Find potential JSON structures
        matches = JSONDetector.JSON_PATTERN.finditer(text)

        for match in matches:
            json_str = match.group(0)

            # Try to parse as JSON
            try:
                obj = json.loads(json_str)
                size = len(json_str)

                # Only count significant JSON (not tiny objects)
                if size >= JSONDetector.MIN_JSON_SIZE:
                    json_objects.append({
                        "size": size,
                        "type": "object" if isinstance(obj, dict) else "array",
                        "depth": JSONDetector._get_depth(obj)
                    })
                    total_bytes += size

            except (json.JSONDecodeError, ValueError):
                # Not valid JSON, skip
                continue

        has_json = len(json_objects) > 0
        return has_json, total_bytes, json_objects

    @staticmethod
    def _get_depth(obj: Any, current_depth: int = 0) -> int:
        """Calculate nesting depth of JSON object."""
        if not isinstance(obj, (dict, list)):
            return current_depth

        if not obj:
            return current_depth

        if isinstance(obj, dict):
            return max((JSONDetector._get_depth(v, current_depth + 1) for v in obj.values()), default=current_depth)
        else:  # list
            return max((JSONDetector._get_depth(item, current_depth + 1) for item in obj), default=current_depth)

    @staticmethod
    def analyze_tool_calls(tool_calls: List[Dict[str, Any]]) -> Tuple[bool, int]:
        """
        Analyze tool calls for JSON content.

        Args:
            tool_calls: List of tool call dicts

        Returns:
            (has_json, total_bytes)
        """
        if not tool_calls:
            return False, 0

        total_bytes = 0

        for tool_call in tool_calls:
            if "function" in tool_call:
                args = tool_call["function"].get("arguments", "")
                if args:
                    try:
                        # Arguments are already JSON strings
                        json.loads(args)  # Validate
                        total_bytes += len(args)
                    except (json.JSONDecodeError, ValueError):
                        pass

        has_json = total_bytes > 0
        return has_json, total_bytes

    @staticmethod
    def estimate_toon_savings(json_bytes: int) -> int:
        """
        Estimate token savings with TOON format.

        TOON typically saves 20-40% for structured JSON.

        Args:
            json_bytes: Total JSON bytes

        Returns:
            Estimated bytes saved
        """
        # Conservative estimate: 25% savings
        return int(json_bytes * 0.25)

    @staticmethod
    def should_recommend_toon(total_requests: int, json_requests: int, total_json_bytes: int) -> bool:
        """
        Determine if TOON conversion is recommended.

        Args:
            total_requests: Total API requests in session
            json_requests: Requests with JSON content
            total_json_bytes: Total JSON bytes

        Returns:
            True if TOON recommended
        """
        if total_requests < 10:
            # Not enough data
            return False

        json_percentage = (json_requests / total_requests) * 100
        avg_json_size = total_json_bytes / json_requests if json_requests > 0 else 0

        # Recommend TOON if:
        # - More than 30% of requests have JSON
        # - Average JSON size > 500 bytes
        # - Total JSON > 10KB
        return (
            json_percentage > 30 and
            avg_json_size > 500 and
            total_json_bytes > 10000
        )


# Global instance
json_detector = JSONDetector()
