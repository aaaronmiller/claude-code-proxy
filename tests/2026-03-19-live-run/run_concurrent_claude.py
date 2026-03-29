import argparse
import json
import os
import shutil
import sqlite3
import tempfile
import threading
import time
from pathlib import Path
from subprocess import Popen, PIPE

CLAUDE_BIN = os.environ.get("CLAUDE_BIN", "claude")
PROXY_URL = os.environ.get("PROXY_URL", "http://127.0.0.1:8082")
USAGE_DB = Path(os.environ.get("PROXY_USAGE_DB", "/home/cheta/code/claude-code-proxy/usage_tracking.db"))
TOOL_LIST = ",".join(
    [
        "Write",
        "Bash",
        "Edit",
        "Read",
        "glob",
        "grep",
        "askuserquestion",
        "webfetch",
        "websearch",
        "croncreate",
        "crondelete",
        "cronlist",
    ]
)

DEFAULT_PROMPTS = {
    "tetris": "You are orchestrating a Tetris assistant that runs a simulated play-by-play, uses at least 35 tool calls (Write/Bash/Edit/Read, websearch, webfetch, cron tools, etc.), and logs every turn in a structured file.",
    "recipe": "You are coordinating a culinary assistant who must issue at least 35 tool calls (Write/Bash/Edit/Read, websearch, webfetch, cron tools) while logging each multi-course step.",
    "build": "You are directing a robotics construction plan with at least 35 tool calls for diagnostics, scheduling, status logging, and narrative explanation.",
}
TASK_ALIASES = {
    "t": "tetris",
    "r": "recipe",
    "b": "build",
}


def create_workspace(label: str) -> Path:
    workspace = Path(tempfile.mkdtemp(prefix=f"claude_{label}_"))
    claude_dir = workspace / ".claude"
    claude_dir.mkdir()
    settings = {
        "permissions": {"allow": ["Bash(*)", "Read(*)", "Write(*)", "Edit(*)"], "deny": []},
        "mcpServers": {},
        "enableAllProjectMcpServers": False,
    }
    (claude_dir / "settings.local.json").write_text(json.dumps(settings))
    (claude_dir / "CLAUDE.md").write_text("# Execution workspace\nno additional instructions.")
    return workspace


def _stream_pipe(pipe, path, header):
    with path.open("w") as out:
        for line in iter(pipe.readline, ""):
            stripped = line.rstrip()
            if stripped:
                print(f"{header} {stripped}")
            out.write(line)
            out.flush()


def run_session(label: str, prompt: str, timeout: int, model: str | None, results: dict):
    workspace = create_workspace(label)
    env = os.environ.copy()
    env.update(
        {
            "ANTHROPIC_BASE_URL": PROXY_URL,
            "ANTHROPIC_API_KEY": "pass",
            "NO_PROXY": "localhost,127.0.0.1",
        }
    )
    cmd = [
        "timeout",
        str(timeout),
        CLAUDE_BIN,
        "--dangerously-skip-permissions",
        "--no-chrome",
        "--no-session-persistence",
    ]
    if model:
        cmd.extend(["--model", model])
    cmd.extend(
        [
        "-p",
        prompt,
        "--allowedTools",
        TOOL_LIST,
        ]
    )
    log_dir = Path("/tmp") / f"claude_live_run_{label}"
    log_dir.mkdir(exist_ok=True)
    for stale_log in ("stdout.log", "stderr.log"):
        log_path = log_dir / stale_log
        if log_path.exists():
            log_path.unlink()
    print(f"{label} session starting: cmd={' '.join(cmd)}")
    proc = Popen(cmd, cwd=workspace, env=env, stdout=PIPE, stderr=PIPE, text=True)
    stdout_path = log_dir / "stdout.log"
    stderr_path = log_dir / "stderr.log"
    stdout_thread = threading.Thread(
        target=_stream_pipe,
        args=(proc.stdout, stdout_path, f"[{label}][stdout]"),
        daemon=True,
    )
    stderr_thread = threading.Thread(
        target=_stream_pipe,
        args=(proc.stderr, stderr_path, f"[{label}][stderr]"),
        daemon=True,
    )
    stdout_thread.start()
    stderr_thread.start()
    start_time = time.time()
    last_heartbeat = time.time()
    while proc.poll() is None:
        current = time.time()
        if current - last_heartbeat >= 10:
            elapsed = int(current - start_time)
            print(f"[{label}][heartbeat] still running (elapsed={elapsed}s timeout={timeout}s)")
            last_heartbeat = current
        time.sleep(0.25)
    stdout_thread.join()
    stderr_thread.join()
    if (workspace / "hello.txt").exists():
        shutil.copy(workspace / "hello.txt", log_dir / "hello.txt")
    for artifact in workspace.iterdir():
        if artifact.is_file() and artifact.name.endswith(".txt"):
            shutil.copy(artifact, log_dir / artifact.name)
    results[label] = {
        "returncode": proc.returncode,
        "workspace": str(workspace),
        "log_dir": str(log_dir),
        "elapsed_seconds": round(time.time() - start_time, 1),
    }
    print(f"{label} session finished with returncode {proc.returncode}")


def resolve_prompt(task_key: str) -> str:
    candidate = task_key.lower()
    candidate = TASK_ALIASES.get(candidate, candidate)
    return DEFAULT_PROMPTS.get(candidate, task_key)


def parse_args():
    parser = argparse.ArgumentParser(description="Fire multiple Claude sessions through the proxy.")
    parser.add_argument(
        "-t",
        "--tasks",
        nargs="+",
        default=["tetris", "tetris", "tetris"],
        help="Task keys or custom prompts for each session (default: three 'tetris' tasks).",
    )
    parser.add_argument(
        "-l",
        "--labels",
        nargs="+",
        default=["alpha", "beta", "gamma"],
        help="Session labels to run in parallel.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=180,
        help="Timeout in seconds applied to each Claude process (passes to `timeout`).",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Optional Claude model alias/full id to force for every session, e.g. 'opus', 'sonnet', or 'haiku'.",
    )
    parser.add_argument(
        "--stagger-seconds",
        type=float,
        default=2.0,
        help="Delay between launching sessions to reduce bursty rate-limit failures.",
    )
    return parser.parse_args()


def print_proxy_summary(start_epoch: float):
    if not USAGE_DB.exists():
        print(f"proxy summary unavailable: db not found at {USAGE_DB}")
        return

    start_ts = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(start_epoch - 5))
    conn = sqlite3.connect(USAGE_DB)
    cur = conn.cursor()
    rows = list(
        cur.execute(
            """
            SELECT timestamp, original_model, routed_model, status, error_message
            FROM api_requests
            WHERE timestamp >= ?
            ORDER BY timestamp ASC
            """,
            (start_ts,),
        )
    )
    conn.close()

    print(f"proxy summary rows since {start_ts}: {len(rows)}")
    for timestamp, original_model, routed_model, status, error_message in rows[-20:]:
        line = f"[proxy] {timestamp} {original_model} -> {routed_model} status={status}"
        if error_message:
            line += f" error={error_message[:220]}"
        print(line)


def main():
    args = parse_args()
    labels = args.labels
    sessions = []
    results = {}
    start_epoch = time.time()
    print(
        f"launching {len(labels)} sessions via {CLAUDE_BIN} -> {PROXY_URL} "
        f"with timeout={args.timeout}s model={args.model or 'default'} stagger={args.stagger_seconds}s"
    )
    for i, label in enumerate(labels):
        task_key = args.tasks[i] if i < len(args.tasks) else args.tasks[-1]
        prompt = resolve_prompt(task_key)
        prompt_preview = prompt.replace("\n", " ")
        if len(prompt_preview) > 140:
            prompt_preview = prompt_preview[:137] + "..."
        print(f"{label} task_key={task_key!r}")
        print(f"{label} prompt_preview={prompt_preview}")
        thread = threading.Thread(
            target=run_session,
            args=(label, prompt, args.timeout, args.model, results),
        )
        sessions.append(thread)
        thread.start()
        time.sleep(args.stagger_seconds)
    for thread in sessions:
        thread.join()
    summary_path = Path("/tmp") / "claude_live_run_summary.json"
    summary_path.write_text(json.dumps(results, indent=2, sort_keys=True))
    print(f"summary written to {summary_path}")
    print_proxy_summary(start_epoch)
    print("Concurrent run complete; inspect /tmp/claude_live_run_<label> for logs.")


if __name__ == "__main__":
    main()
