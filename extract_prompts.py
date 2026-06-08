#!/usr/bin/env python3
"""Extract user prompts from Claude Code session logs for this project."""
import json
import os
import sys
from pathlib import Path
from datetime import datetime

REPO_ROOT = Path(__file__).resolve().parent
PROJECT_DIR = Path.home() / ".claude" / "projects" / str(REPO_ROOT).replace("/", "-")
OUTPUT_DIR = REPO_ROOT / "archive" / "session-prompts"
OUTPUT_FILE = OUTPUT_DIR / "USERPROMPTS.md"
OUTPUT_FILE_V2 = OUTPUT_DIR / "USERPROMPTS-v2.md"

def extract_text_from_content(content):
    """Extract readable text from message content (string or list)."""
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict):
                btype = block.get("type", "")
                if btype == "text":
                    parts.append(block.get("text", ""))
                # Skip tool_result, tool_use, etc — not user-authored text
        text = "\n".join(p for p in parts if p.strip())
        return text.strip()
    return ""


def extract_prompts_from_jsonl(jsonl_path: Path) -> list[dict]:
    """Extract user prompts from a single JSONL session file."""
    prompts = []
    try:
        with open(jsonl_path, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue

                # Claude Code JSONL: type="user", message.role="user", message.content=...
                if entry.get("type") != "user":
                    continue

                message = entry.get("message", {})
                if message.get("role") != "user":
                    continue

                content = message.get("content", "")
                text = extract_text_from_content(content)

                # Skip entries that are purely tool results (no user text)
                if not text or len(text.strip()) == 0:
                    continue

                # Skip if it's just tool result content (starts with typical tool output)
                # We want real user prompts, not automated tool returns
                parent = entry.get("parentUuid")
                is_first_msg = parent is None

                # If content is a list and ALL items are tool_result, skip
                if isinstance(content, list):
                    all_tool_results = all(
                        isinstance(b, dict) and b.get("type") == "tool_result"
                        for b in content
                        if isinstance(b, dict)
                    )
                    if all_tool_results and not any(
                        isinstance(b, dict) and b.get("type") == "text"
                        for b in content
                    ):
                        continue

                timestamp = entry.get("timestamp", "")

                prompts.append({
                    "text": text,
                    "timestamp": timestamp,
                    "session": jsonl_path.stem,
                    "line": line_num,
                    "is_first": is_first_msg,
                })
    except Exception as e:
        print(f"  Error reading {jsonl_path.name}: {e}", file=sys.stderr)
    return prompts


def normalize_for_dedup(text: str) -> str:
    """Normalize text for deduplication: collapse whitespace, lowercase, strip."""
    import re
    return re.sub(r'\s+', ' ', text.strip().lower())


def deduplicate_prompts(prompts: list[dict]) -> tuple[list[dict], int]:
    """Remove duplicate prompts, keeping the first occurrence.

    Returns (deduped_list, num_removed).
    """
    seen = set()
    result = []
    for p in prompts:
        key = normalize_for_dedup(p["text"])
        if key in seen:
            continue
        seen.add(key)
        result.append(p)
    return result, len(prompts) - len(result)


def write_prompts_md(prompts: list[dict], output_path: Path, num_sessions: int,
                     dupes_removed: int = 0, truncate: bool = False):
    """Write prompts to a markdown file."""
    with open(output_path, "w", encoding="utf-8") as out:
        out.write("# User Prompts — Claude Code Sessions\n\n")
        out.write(f"> Extracted **{len(prompts)}** unique prompts from {num_sessions} sessions\n")
        if dupes_removed > 0:
            out.write(f"> Deduplicated: {dupes_removed} duplicate prompts removed\n")
        out.write(f"> Project: `~/code/claude-code-proxy`\n")
        out.write(f"> Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        if not truncate:
            out.write(f"> Full-length prompts (no truncation)\n")
        out.write("\n---\n\n")

        current_session = None
        prompt_num = 0
        for p in prompts:
            if p["session"] != current_session:
                current_session = p["session"]
                prompt_num = 0
                out.write(f"\n## Session: `{current_session}`\n\n")

            prompt_num += 1
            ts = p["timestamp"]
            ts_str = str(ts) if ts else "(no timestamp)"

            marker = "🟢 INITIAL" if p["is_first"] else ""
            out.write(f"### Prompt {prompt_num} {marker} — {ts_str}\n\n")

            text = p["text"]
            if truncate and len(text) > 3000:
                text = text[:3000] + f"\n\n... (truncated, {len(p['text'])} chars total)"

            out.write(f"```\n{text}\n```\n\n")


def main():
    if not PROJECT_DIR.exists():
        print(f"Project dir not found: {PROJECT_DIR}", file=sys.stderr)
        sys.exit(1)

    jsonl_files = sorted(PROJECT_DIR.glob("*.jsonl"), key=lambda p: p.stat().st_mtime)
    print(f"Found {len(jsonl_files)} session files in {PROJECT_DIR}")

    all_prompts = []
    for jf in jsonl_files:
        size_kb = jf.stat().st_size / 1024
        mtime = datetime.fromtimestamp(jf.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
        print(f"  Processing {jf.name} ({size_kb:.0f}KB, modified {mtime})")
        prompts = extract_prompts_from_jsonl(jf)
        all_prompts.extend(prompts)
        print(f"    → {len(prompts)} user prompts extracted")

    # Deduplicate
    deduped, dupes_removed = deduplicate_prompts(all_prompts)
    print(f"\nDeduplication: {len(all_prompts)} → {len(deduped)} ({dupes_removed} duplicates removed)")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Write v2: full-length, deduplicated
    write_prompts_md(deduped, OUTPUT_FILE_V2, len(jsonl_files),
                     dupes_removed=dupes_removed, truncate=False)
    print(f"✅ Written {len(deduped)} prompts to {OUTPUT_FILE_V2} (full-length, deduped)")

    # Also update the original (truncated) for backwards compat
    write_prompts_md(deduped, OUTPUT_FILE, len(jsonl_files),
                     dupes_removed=dupes_removed, truncate=True)
    print(f"✅ Updated {OUTPUT_FILE} (truncated, deduped)")


if __name__ == "__main__":
    main()
