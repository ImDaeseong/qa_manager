"""Track bounded verification attempts without modifying a target repository."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path


MAX_ITERATIONS = 3
MAX_UNCHANGED_RETRIES = 1
MAX_EDITS_PER_LOCATION = 2


def failure_signature(check_id: str, output: str) -> str:
    """Return a stable identifier for one check failure and its normalized output."""
    normalized = "\n".join(line.strip() for line in output.splitlines() if line.strip())
    digest = hashlib.sha256(f"{check_id}\n{normalized}".encode("utf-8")).hexdigest()[:16]
    return f"{check_id}:{digest}"


def new_state(project: str, check_id: str, goal: str) -> dict:
    """Create an empty bounded-loop record for one project check."""
    return {
        "project": project,
        "check_id": check_id,
        "goal": goal,
        "policy": {
            "max_iterations": MAX_ITERATIONS,
            "max_unchanged_retries": MAX_UNCHANGED_RETRIES,
            "max_edits_per_location": MAX_EDITS_PER_LOCATION,
        },
        "status": "running",
        "next_action": "run_check",
        "attempts": [],
    }


def record_attempt(
    state: dict,
    live_status: str,
    output: str,
    *,
    changed_files: list[str] | None = None,
    suspect_flaky: bool = False,
    high_risk: bool = False,
) -> dict:
    """Record one result and choose complete, retry, repair, or HOLD."""
    if state.get("status") != "running":
        raise ValueError("verification loop is already closed")
    if live_status not in {"pass", "fail"}:
        raise ValueError("live_status must be pass or fail")

    changed_files = sorted(set(changed_files or []))
    signature = None if live_status == "pass" else failure_signature(state["check_id"], output)
    attempt = {
        "iteration": len(state["attempts"]) + 1,
        "time_utc": datetime.now(timezone.utc).isoformat(),
        "status": live_status,
        "failure_signature": signature,
        "changed_files": changed_files,
    }
    state["attempts"].append(attempt)

    if high_risk:
        state.update(status="hold", next_action="human_review",
                     exit_reason="high_risk_change_requires_approval")
        return state

    if live_status == "pass":
        state.update(status="complete", next_action="stop", exit_reason="check_passed")
        return state

    file_counts: dict[str, int] = {}
    for previous in state["attempts"]:
        for path in previous["changed_files"]:
            file_counts[path] = file_counts.get(path, 0) + 1
    if any(count >= MAX_EDITS_PER_LOCATION for count in file_counts.values()):
        state.update(status="hold", next_action="human_review",
                     exit_reason="same_location_failed_after_two_edits")
        return state

    same_failures = sum(
        previous["failure_signature"] == signature for previous in state["attempts"]
    )
    if same_failures >= MAX_ITERATIONS or len(state["attempts"]) >= MAX_ITERATIONS:
        state.update(status="hold", next_action="human_review",
                     exit_reason="maximum_iterations_reached")
        return state

    unchanged_failures = sum(
        previous["status"] == "fail" and not previous["changed_files"]
        for previous in state["attempts"]
    )
    if suspect_flaky and unchanged_failures <= MAX_UNCHANGED_RETRIES:
        state.update(next_action="retry_without_change", exit_reason=None)
    else:
        state.update(next_action="repair_required", exit_reason=None)
    return state


def load_state(path: Path) -> dict:
    """Load one loop record from JSON."""
    return json.loads(path.read_text(encoding="utf-8"))


def write_state(path: Path, state: dict) -> None:
    """Atomically persist one loop record."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent,
                                         prefix=f".{path.name}.", suffix=".tmp",
                                         delete=False) as stream:
            temporary = Path(stream.name)
            json.dump(state, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
