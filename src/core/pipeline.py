"""
API Pipeline Orchestration — sequential API handoff chains.

Pipelines are defined in config/proxy_chain.json under the "pipelines" key:

    "pipelines": {
        "voice": {
            "description": "Whisper → Proxy (LLM) → Piper TTS",
            "steps": [
                {
                    "id": "transcribe",
                    "url": "http://127.0.0.1:9000/v1/audio/transcriptions",
                    "method": "POST",
                    "input_field": "audio_b64",
                    "output_field": "text",
                    "headers": {"Content-Type": "application/json"}
                },
                {
                    "id": "llm",
                    "url": "http://127.0.0.1:8082/v1/messages",
                    "method": "POST",
                    "input_field": "content",
                    "output_field": "content[0].text",
                    "headers": {"Content-Type": "application/json",
                                "x-api-key": "pass",
                                "anthropic-version": "2023-06-01"}
                },
                {
                    "id": "speak",
                    "url": "http://127.0.0.1:5500/synthesize",
                    "method": "POST",
                    "input_field": "text",
                    "output_field": "audio_b64",
                    "headers": {"Content-Type": "application/json"}
                }
            ]
        }
    }

Usage via HTTP:
    POST /v1/pipeline/{pipeline_name}
    Content-Type: application/json
    { "input": <initial_value>, "context": { ... optional extra fields ... } }

Output:
    { "pipeline": "voice", "steps": [...per-step results...], "output": <final_value> }
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)

_CHAIN_FILE = Path(os.environ.get("PROXY_CHAIN_FILE", "config/proxy_chain.json"))
_STEP_TIMEOUT = float(os.environ.get("PIPELINE_STEP_TIMEOUT", "30"))


def _load_pipelines() -> dict:
    """Load pipeline definitions from proxy_chain.json."""
    try:
        data = json.loads(_CHAIN_FILE.read_text(encoding="utf-8"))
        return data.get("pipelines", {})
    except Exception as e:
        logger.warning(f"Could not load pipelines from {_CHAIN_FILE}: {e}")
        return {}


def _get_nested(obj: Any, path: str) -> Any:
    """
    Extract a value from a nested dict/list using dot notation.
    e.g. "content[0].text" → obj["content"][0]["text"]
    """
    if not path:
        return obj
    for part in path.replace("[", ".").replace("]", "").split("."):
        if not part:
            continue
        try:
            if isinstance(obj, list):
                obj = obj[int(part)]
            elif isinstance(obj, dict):
                obj = obj[part]
            else:
                return None
        except (KeyError, IndexError, ValueError, TypeError):
            return None
    return obj


def _set_nested(obj: dict, field: str, value: Any) -> dict:
    """Set a top-level field in a dict (shallow, for building step payloads)."""
    obj[field] = value
    return obj


async def run_pipeline(
    name: str,
    initial_input: Any,
    context: Optional[dict] = None,
) -> dict:
    """
    Execute a named pipeline, threading output → input between steps.

    Returns:
        {
            "pipeline": name,
            "steps": [{"id": ..., "input": ..., "output": ..., "status": "ok"|"error", "error": ...}],
            "output": <final step output>,
            "ok": bool,
        }
    """
    pipelines = _load_pipelines()
    if name not in pipelines:
        available = list(pipelines.keys())
        raise ValueError(f"Pipeline '{name}' not found. Available: {available}")

    pipeline = pipelines[name]
    steps_cfg = pipeline.get("steps", [])
    if not steps_cfg:
        raise ValueError(f"Pipeline '{name}' has no steps configured")

    context = context or {}
    current_value = initial_input
    step_results = []

    # Resolve auth tokens for inherit_auth steps once upfront
    _proxy_auth = {
        "openrouter": os.environ.get("OPENROUTER_API_KEY", ""),
        "anthropic": os.environ.get("ANTHROPIC_API_KEY", "") or "pass",
        "openai": os.environ.get("OPENAI_API_KEY", ""),
    }

    async with httpx.AsyncClient(timeout=_STEP_TIMEOUT) as client:
        for step in steps_cfg:
            step_id = step.get("id", "step")
            url = step.get("url", "")
            method = step.get("method", "POST").upper()
            input_field = step.get("input_field", "input")
            output_field = step.get("output_field", "output")
            max_retries = int(step.get("max_retries", 1))
            inherit_auth = step.get("inherit_auth", "")  # "openrouter"|"anthropic"|"openai"|""

            # Build headers: start from step config, inject inherited auth if requested
            headers = dict(step.get("headers", {}))
            if inherit_auth and _proxy_auth.get(inherit_auth):
                auth_token = _proxy_auth[inherit_auth]
                if inherit_auth == "anthropic":
                    headers.setdefault("x-api-key", auth_token)
                    headers.setdefault("anthropic-version", "2023-06-01")
                else:
                    headers.setdefault("Authorization", f"Bearer {auth_token}")

            extra_body = step.get("extra_body", {})

            # Build payload: start from extra_body, inject current value at input_field
            payload = dict(extra_body)
            payload.update(context)
            _set_nested(payload, input_field, current_value)

            step_record = {"id": step_id, "input": current_value}
            last_err: Optional[str] = None

            for attempt in range(max(1, max_retries)):
                try:
                    if method == "GET":
                        resp = await client.get(url, headers=headers, params=payload)
                    else:
                        resp = await client.post(url, headers=headers, json=payload)

                    resp.raise_for_status()
                    resp_body = resp.json()
                    output_value = _get_nested(resp_body, output_field)

                    # Guard: if the expected output field was not found, fail loudly.
                    if output_value is None and output_field:
                        available = list(resp_body.keys()) if isinstance(resp_body, dict) else type(resp_body).__name__
                        raise ValueError(
                            f"output_field '{output_field}' not found in response. "
                            f"Available keys: {available}. "
                            f"Check step config or inspect: GET /api/pipelines"
                        )

                    step_record["output"] = output_value
                    step_record["status"] = "ok"
                    if attempt > 0:
                        step_record["retries"] = attempt
                    current_value = output_value
                    logger.debug(f"Pipeline '{name}' step '{step_id}': OK (attempt {attempt+1}) → {type(output_value).__name__}")
                    last_err = None
                    break  # success — exit retry loop

                except Exception as e:
                    last_err = str(e)[:200]
                    if attempt < max_retries - 1:
                        logger.warning(f"Pipeline '{name}' step '{step_id}' attempt {attempt+1} failed: {last_err} — retrying")
                    else:
                        logger.error(f"Pipeline '{name}' step '{step_id}' failed after {attempt+1} attempt(s): {last_err}")

            if last_err is not None:
                step_record["status"] = "error"
                step_record["error"] = last_err
                step_results.append(step_record)
                return {
                    "pipeline": name,
                    "steps": step_results,
                    "output": None,
                    "ok": False,
                    "error": f"Step '{step_id}' failed: {last_err}",
                }

            step_results.append(step_record)

    return {
        "pipeline": name,
        "steps": step_results,
        "output": current_value,
        "ok": True,
    }


def list_pipelines() -> dict:
    """Return available pipeline names and their descriptions."""
    pipelines = _load_pipelines()
    return {
        name: {
            "description": p.get("description", ""),
            "steps": [s.get("id", f"step{i}") for i, s in enumerate(p.get("steps", []))],
        }
        for name, p in pipelines.items()
    }
