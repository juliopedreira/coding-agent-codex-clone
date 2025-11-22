from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict


def load_coverage(path: Path) -> Dict[str, object]:
    if not path.exists():
        raise FileNotFoundError(f"Coverage file not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def verify_threshold(data: Dict[str, object], threshold: float) -> int:
    files: Dict[str, object] = data.get("files", {}) if isinstance(data, dict) else {}
    failures: list[str] = []
    for filename, info in files.items():
        if not isinstance(info, dict):
            continue
        summary = info.get("summary", {})
        percent = summary.get("percent_covered", 0.0)
        # Only enforce for source files under codax package.
        if "src/codax" not in filename:
            continue
        if percent < threshold:
            failures.append(f"{filename}: {percent:.1f}% (min {threshold}%)")
    if failures:
        print("Coverage threshold failed per file:", file=sys.stderr)
        for fail in failures:
            print(f" - {fail}", file=sys.stderr)
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Check per-file coverage threshold.")
    parser.add_argument(
        "coverage_json",
        nargs="?",
        default="coverage.json",
        help="Path to coverage JSON report (produced by coverage/pytest-cov).",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=80.0,
        help="Minimum percent coverage required per source file.",
    )
    args = parser.parse_args()
    data = load_coverage(Path(args.coverage_json))
    return verify_threshold(data, args.threshold)


if __name__ == "__main__":
    raise SystemExit(main())
