from __future__ import annotations

import argparse
from pathlib import Path


RUNTIME_FILES = (
    Path("data/runtime/forward-plans.jsonl"),
    Path("data/runtime/forward-results.json"),
    Path("data/runtime/seen-zones.json"),
    Path("data/runtime/live-snapshot.json"),
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Clear old forward-demo runtime state before starting a new "
            "authoritative strategy-contract demo."
        )
    )
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Required acknowledgement that old forward-demo runtime will be deleted.",
    )
    args = parser.parse_args()

    if not args.confirm:
        parser.error("Pass --confirm to clear old forward-demo runtime state.")

    removed = []
    for path in RUNTIME_FILES:
        if path.exists():
            path.unlink()
            removed.append(str(path))

    print("Phase 0 forward-demo runtime reset.")
    if removed:
        for path in removed:
            print(f"  removed {path}")
    else:
        print("  no old runtime files were present")
    print("Calibration files were NOT deleted.")


if __name__ == "__main__":
    main()
