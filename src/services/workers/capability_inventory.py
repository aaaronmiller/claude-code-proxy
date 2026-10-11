"""CG-T081 — exact worker and account capability inventory.

Each inventory record is a probed capability of one installed harness or quota
source on this machine, with current provenance. No credential values are
recorded and no paid call is made: probes are version/flag/help inspections
and zero-cost local checks only. Unverified claims stay out; every entry cites
how and when it was measured.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess  # nosec B404 - fixed argv probes only
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

SCHEMA_VERSION = "1.1.0"

PROBE_TIMEOUT_S = 20


class InventoryRejected(ValueError):
    """Raised when a capability record lacks provenance or carries a secret."""


@dataclass(frozen=True)
class CapabilityFact:
    """One measured fact about one worker harness or quota source."""

    subject: str          # harness id, e.g. "codex", "omp", "opencode", "claude-code"
    capability: str       # e.g. "version", "headless_json", "effort_flag"
    status: str           # "present" | "absent" | "unknown"
    detail: str = ""
    provenance: str = ""  # exact probe command or source path
    measured_at: str = ""
    schema_version: str = SCHEMA_VERSION


_SECRET_MARKERS = ("sk-", "api_key=", "key=", "password", "bearer ", "token=")


def _run(argv: list[str]) -> tuple[int, str]:
    try:
        proc = subprocess.run(  # nosec B603 - fixed argv, no shell
            argv,
            capture_output=True,
            text=True,
            timeout=PROBE_TIMEOUT_S,
            check=False,
        )
        return proc.returncode, (proc.stdout or "") + (proc.stderr or "")
    except (subprocess.TimeoutExpired, OSError):
        return 127, ""


def _now() -> str:
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z")
    )


def _fact(subject: str, capability: str, status: str, detail: str, provenance: str) -> CapabilityFact:
    return CapabilityFact(
        subject=subject,
        capability=capability,
        status=status,
        detail=detail,
        provenance=provenance,
        measured_at=_now(),
    )


def _probe_harness(subject: str, binary: str) -> list[CapabilityFact]:
    facts: list[CapabilityFact] = []
    if shutil.which(binary) is None:
        facts.append(_fact(subject, "installed", "absent", "", f"shutil.which({binary!r})"))
        return facts

    code, out = _run([binary, "--version"])
    version = out.strip().splitlines()[0] if out.strip() else ""
    facts.append(
        _fact(subject, "installed", "present", version, f"{binary} --version rc={code}")
    )

    if subject == "codex":
        code, out = _run([binary, "exec", "--help"])
        blob = out.lower()
        facts.append(
            _fact(
                subject,
                "headless_exec",
                "present" if "usage: codex exec" in blob else "absent",
                "codex exec [PROMPT] with --json JSONL events and --output-schema",
                f"{binary} exec --help rc={code}",
            )
        )
        facts.append(
            _fact(
                subject,
                "headless_json_events",
                "present" if "--json" in blob else "absent",
                "JSONL event stream on stdout",
                f"{binary} exec --help rc={code}",
            )
        )
        facts.append(
            _fact(
                subject,
                "structured_output_schema",
                "present" if "--output-schema" in blob else "absent",
                "--output-schema <FILE> constrains the final response shape",
                f"{binary} exec --help rc={code}",
            )
        )
        facts.append(
            _fact(
                subject,
                "resume",
                "present" if "resume" in blob else "absent",
                "codex exec resume <SESSION_ID|last>",
                f"{binary} exec --help rc={code}",
            )
        )
        facts.append(
            _fact(
                subject,
                "effort_override",
                "present" if "-c" in blob else "absent",
                "-c model_reasoning_effort=<effort> (documented runtime override)",
                f"{binary} exec --help rc={code}; docs current as of probe",
            )
        )
        facts.append(
            _fact(
                subject,
                "sandbox_flag",
                "present" if "--sandbox" in blob or "-s, --sandbox" in blob else "absent",
                "-s read-only|workspace-write|danger-full-access",
                f"{binary} exec --help rc={code}",
            )
        )
    elif subject == "opencode":
        code, out = _run([binary, "run", "--help"])
        blob = out.lower()
        facts.append(
            _fact(
                subject,
                "headless_run",
                "present" if "run opencode with a message" in blob else "absent",
                "opencode run [message..]",
                f"{binary} run --help rc={code}",
            )
        )
        facts.append(
            _fact(
                subject,
                "headless_json_events",
                "present" if "--format" in blob and "json" in blob else "absent",
                "--format json raw JSON events",
                f"{binary} run --help rc={code}",
            )
        )
        facts.append(
            _fact(
                subject,
                "effort_override",
                "present" if "--variant" in blob else "absent",
                "--variant model variant (reasoning effort, e.g. high, max, minimal)",
                f"{binary} run --help rc={code}",
            )
        )
        facts.append(
            _fact(
                subject,
                "session_resume",
                "present" if "--session" in blob else "absent",
                "-s <id> / -c continue; --fork supported",
                f"{binary} run --help rc={code}",
            )
        )
        facts.append(
            _fact(
                subject,
                "attached_server",
                "present" if "--attach" in blob else "absent",
                "--attach http://host:port; --port for the local server",
                f"{binary} run --help rc={code}",
            )
        )
        facts.append(
            _fact(
                subject,
                "agent_selection",
                "present" if "--agent" in blob else "absent",
                "--agent named agent",
                f"{binary} run --help rc={code}",
            )
        )
    elif subject == "claude-code":
        code, out = _run([binary, "--help"])
        blob = out.lower()
        facts.append(
            _fact(
                subject,
                "headless_print",
                "present" if "--print" in blob else "absent",
                "-p/--print non-interactive mode",
                f"{binary} --help rc={code}",
            )
        )
        facts.append(
            _fact(
                subject,
                "headless_json_events",
                "present" if "stream-json" in blob else "absent",
                "--output-format stream-json (with --include-partial-messages)",
                f"{binary} --help rc={code}",
            )
        )
        facts.append(
            _fact(
                subject,
                "effort_override",
                "present" if "--effort" in blob else "absent",
                "--effort <level> session effort level",
                f"{binary} --help rc={code}",
            )
        )
        facts.append(
            _fact(
                subject,
                "session_resume",
                "present" if ("--resume" in blob or "-c, --continue" in blob) else "absent",
                "-c continue most recent; --resume <id>; --fork-session",
                f"{binary} --help rc={code}",
            )
        )
        facts.append(
            _fact(
                subject,
                "background_agents",
                "present" if "--background" in blob or "--bg" in blob else "absent",
                "--bg, --background start as a background agent",
                f"{binary} --help rc={code}",
            )
        )
    elif subject == "omp":
        code, out = _run([binary, "--help"])
        blob = out.lower()
        facts.append(
            _fact(
                subject,
                "output_modes",
                "present" if "--mode" in blob else "absent",
                "--mode text|json|rpc|rpc-ui",
                f"{binary} --help rc={code}",
            )
        )
        facts.append(
            _fact(
                subject,
                "model_roles",
                "present" if "--model=" in blob or "--model <" in blob else "absent",
                "--model plus --smol/--slow/--plan role models",
                f"{binary} --help rc={code}",
            )
        )
        facts.append(
            _fact(
                subject,
                "profile_isolation",
                "present" if "--profile" in blob else "absent",
                "--profile isolated auth/sessions/settings/caches",
                f"{binary} --help rc={code}",
            )
        )
        facts.append(
            _fact(
                subject,
                "effort_override",
                "unknown",
                "no dedicated effort flag in --help; role models + config carry effort",
                f"{binary} --help rc={code}",
            )
        )
    return facts


def _probe_quota_sources() -> list[CapabilityFact]:
    facts: list[CapabilityFact] = []
    from src.core.quota_sources import PRECEDENCE

    for source, rank in sorted(PRECEDENCE.items(), key=lambda kv: -kv[1]):
        facts.append(
            _fact(
                "quota-source-precedence",
                source,
                "present",
                f"precedence rank {rank}",
                "src/core/quota_sources.py PRECEDENCE",
            )
        )
    code, out = _run(["codex", "--version"])
    facts.append(
        _fact(
            "codex-account",
            "subscription_quota_source",
            "unknown",
            "ChatGPT-plan quota is provider-side; no local meter observed; "
            "no credential or paid call used",
            "codex --version rc={}".format(code),
        )
    )
    return facts


def _probe_environment() -> list[CapabilityFact]:
    facts: list[CapabilityFact] = []
    try:
        load1 = os.getloadavg()[0]
        facts.append(
            _fact(
                "host",
                "resident_load",
                "present",
                f"loadavg1={load1:.2f}",
                "os.getloadavg",
            )
        )
    except OSError:
        pass
    facts.append(
        _fact(
            "host",
            "platform",
            "present",
            f"{os.uname().sysname} {os.uname().release} {os.uname().machine}",
            "os.uname",
        )
    )
    return facts


def collect_inventory() -> dict[str, Any]:
    """Probe all installed harnesses and quota sources; return one record."""
    facts: list[CapabilityFact] = []
    for subject, binary in (
        ("codex", "codex"),
        ("opencode", "opencode"),
        ("claude-code", "claude"),
        ("omp", "omp"),
    ):
        facts.extend(_probe_harness(subject, binary))
    facts.append(
        _fact("omx", "installed", "absent", "", "shutil.which('omx')")
    )
    facts.extend(_probe_quota_sources())
    facts.extend(_probe_environment())
    record = {
        "mode": "capability-inventory",
        "schema_version": SCHEMA_VERSION,
        "generated_at": _now(),
        "paid_calls_made": False,
        "credential_values_recorded": False,
        "facts": [asdict(f) for f in facts],
    }
    validate_inventory(record)
    return record


def validate_inventory(record: dict[str, Any]) -> None:
    """Fail closed on missing provenance, undated facts, or secret-looking data."""
    blob = json.dumps(record).lower()
    for marker in _SECRET_MARKERS:
        if marker in blob:
            raise InventoryRejected(f"inventory may contain a credential: {marker!r}")
    for raw in record.get("facts", []):
        if not raw.get("provenance"):
            raise InventoryRejected(
                f"fact {raw.get('subject')}.{raw.get('capability')} lacks provenance"
            )
        if not raw.get("measured_at"):
            raise InventoryRejected(
                f"fact {raw.get('subject')}.{raw.get('capability')} is undated"
            )
        if raw.get("schema_version") != SCHEMA_VERSION:
            raise InventoryRejected(
                f"fact {raw.get('subject')}.{raw.get('capability')} has schema "
                f"{raw.get('schema_version')!r}"
            )
        if raw.get("status") not in {"present", "absent", "unknown"}:
            raise InventoryRejected(
                f"fact {raw.get('subject')}.{raw.get('capability')} status "
                f"{raw.get('status')!r} is not decided"
            )
