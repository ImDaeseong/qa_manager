"""Run one registered check through a bounded evidence-preserving loop."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _checklist_lib as lib  # noqa: E402
import _verification_loop as loop  # noqa: E402


def find_test_item(data: dict, check_id: str) -> dict:
    """Return the uniquely registered test item selected by ID."""
    matches = [item for _, _, item in lib.iter_test_items(data) if item.get("id") == check_id]
    if len(matches) != 1:
        raise ValueError(f"check ID must match exactly one test_item: {check_id!r}")
    return matches[0]


def parse_args(argv: list[str]) -> argparse.Namespace:
    """Parse one bounded-loop invocation."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("checklist", type=Path)
    parser.add_argument("check_id")
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--goal", default="registered check passes with regression evidence")
    parser.add_argument("--changed-file", action="append", default=[])
    parser.add_argument("--suspect-flaky", action="store_true")
    parser.add_argument("--high-risk", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    """Execute one check, persist its attempt, and return the loop decision."""
    args = parse_args(argv)
    data = lib.load(args.checklist)
    item = find_test_item(data, args.check_id)
    state = (loop.load_state(args.state) if args.state.exists()
             else loop.new_state(data.get("project", "<unknown>"), args.check_id, args.goal))
    if state.get("check_id") != args.check_id or state.get("project") != data.get("project"):
        raise ValueError("state file belongs to a different project or check")

    cwd = lib.project_root(data)
    live_status, output = lib.run_test_item(item, cwd)
    loop.record_attempt(
        state,
        live_status,
        output,
        changed_files=args.changed_file,
        suspect_flaky=args.suspect_flaky,
        high_risk=args.high_risk,
    )
    if state["next_action"] == "retry_without_change":
        print(f"{args.check_id}: {live_status} -> retry_without_change")
        live_status, output = lib.run_test_item(item, cwd)
        loop.record_attempt(state, live_status, output)
    loop.write_state(args.state, state)
    print(f"{args.check_id}: {live_status} -> {state['next_action']}")
    if output and live_status == "fail":
        print(output)
    if state["status"] == "complete":
        return 0
    if state["status"] == "hold":
        return 2
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
