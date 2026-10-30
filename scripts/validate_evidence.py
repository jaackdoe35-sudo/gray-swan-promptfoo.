#!/usr/bin/env python3
"""Validate evidence JSON records using only the Python standard library."""
import json
import sys
from pathlib import Path

ALLOWED = {"CONFIRMED_FAILURE", "CONFIRMED_BLOCK", "INCONCLUSIVE", "NOT_RUN"}
REQUIRED_TOP = {"schema_version", "case_id", "classification", "challenge",
                "execution", "inputs", "observations", "evidence", "analysis"}

def validate(path: Path) -> list[str]:
    errors = []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return [f"{path}: invalid JSON: {exc}"]
    if not isinstance(data, dict):
        return [f"{path}: top-level JSON value must be an object"]
    missing = sorted(REQUIRED_TOP - data.keys())
    if missing:
        errors.append(f"{path}: missing top-level keys: {', '.join(missing)}")
    classification = data.get("classification")
    if classification not in ALLOWED:
        errors.append(f"{path}: classification must be one of {', '.join(sorted(ALLOWED))}")
    for key in ("challenge", "execution", "inputs", "observations", "analysis"):
        if key in data and not isinstance(data[key], dict):
            errors.append(f"{path}: {key} must be an object")
    if "evidence" in data and not isinstance(data["evidence"], list):
        errors.append(f"{path}: evidence must be an array")
    observations = data.get("observations", {})
    if isinstance(observations, dict):
        for key in ("tool_calls", "tool_results", "side_effects", "official_success_criteria"):
            if key in observations and not isinstance(observations[key], list):
                errors.append(f"{path}: observations.{key} must be an array")
    if classification in {"CONFIRMED_FAILURE", "CONFIRMED_BLOCK"}:
        evidence = data.get("evidence", [])
        if not evidence:
            errors.append(f"{path}: confirmed classifications require at least one evidence reference")
        analysis = data.get("analysis", {})
        if isinstance(analysis, dict) and not analysis.get("evidence_basis"):
            errors.append(f"{path}: confirmed classifications require analysis.evidence_basis")
    if classification == "NOT_RUN":
        execution = data.get("execution", {})
        if isinstance(execution, dict) and execution.get("run_id"):
            errors.append(f"{path}: NOT_RUN record should not contain a run_id")
    return errors

def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python scripts/validate_evidence.py path/to/record.json [...]")
        return 2
    all_errors = []
    for name in sys.argv[1:]:
        all_errors.extend(validate(Path(name)))
    if all_errors:
        print("\n".join(all_errors))
        return 1
    print(f"Validated {len(sys.argv) - 1} evidence record(s).")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
