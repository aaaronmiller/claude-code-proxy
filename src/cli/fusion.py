"""One-shot OpenRouter Fusion CLI."""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from typing import Any

import httpx

from src.core.fusion import OPENROUTER_BASE_URL, get_fusion_profile, openrouter_api_key


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ccp-fusion",
        description="Send a prompt through an OpenRouter Fusion profile.",
    )
    parser.add_argument(
        "profile_or_prompt",
        nargs="?",
        help="Fusion profile name, or the prompt when no explicit profile is needed.",
    )
    parser.add_argument("prompt_parts", nargs="*", help="Prompt text.")
    parser.add_argument(
        "--profile",
        "-p",
        help="Fusion profile name. Defaults to FUSION_PROFILE or 'free'.",
    )
    parser.add_argument(
        "--model",
        help="Outer model. Defaults to FUSION_OUTER_MODEL or openrouter/fusion.",
    )
    parser.add_argument(
        "--no-force",
        action="store_true",
        help="Do not set tool_choice=required.",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        help="Top-level max completion tokens.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the full OpenRouter JSON response.",
    )
    return parser


def _resolve_profile_and_prompt(args: argparse.Namespace) -> tuple[str | None, str]:
    profile = args.profile
    parts = list(args.prompt_parts)
    first = args.profile_or_prompt

    if first and profile is None and parts:
        profile = first
        prompt = " ".join(parts)
    elif first and profile is None and not sys.stdin.isatty():
        profile = first
        prompt = sys.stdin.read()
    elif first:
        prompt = " ".join([first] + parts)
    else:
        prompt = " ".join(parts)

    if not prompt and not sys.stdin.isatty():
        prompt = sys.stdin.read()

    prompt = prompt.strip()
    if not prompt:
        raise SystemExit("No prompt provided. Pass a prompt or pipe stdin.")
    return profile, prompt


async def _send(profile_name: str | None, prompt: str, args: argparse.Namespace) -> dict[str, Any]:
    api_key = openrouter_api_key()
    if not api_key:
        raise SystemExit("OPENROUTER_API_KEY or BIG_API_KEY is required.")

    profile = get_fusion_profile(profile_name)
    model = args.model or os.getenv("FUSION_OUTER_MODEL") or "openrouter/fusion"
    body: dict[str, Any] = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "plugins": [profile.plugin()],
    }
    if profile.force and not args.no_force:
        body["tool_choice"] = "required"
    elif not args.no_force:
        body["tool_choice"] = "required"
    if args.max_tokens:
        body["max_tokens"] = args.max_tokens

    url = os.getenv("OPENROUTER_BASE_URL", OPENROUTER_BASE_URL).rstrip("/")
    async with httpx.AsyncClient(timeout=float(os.getenv("FUSION_TIMEOUT", "600"))) as client:
        response = await client.post(
            f"{url}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=body,
        )
    if response.status_code >= 400:
        raise SystemExit(f"OpenRouter error {response.status_code}: {response.text}")
    return response.json()


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()
    profile, prompt = _resolve_profile_and_prompt(args)
    data = asyncio.run(_send(profile, prompt, args))
    if args.json:
        import json

        print(json.dumps(data, indent=2))
        return

    choices = data.get("choices") or []
    if not choices:
        raise SystemExit("OpenRouter returned no choices.")
    message = choices[0].get("message") or {}
    content = message.get("content")
    if content is None:
        raise SystemExit("OpenRouter returned no message content.")
    print(content)


if __name__ == "__main__":
    main()
