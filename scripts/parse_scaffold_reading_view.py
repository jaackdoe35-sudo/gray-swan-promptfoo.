#!/usr/bin/env python3
"""Best-effort parser for text copied from Gray Swan Scaffold Logs reading view.

This parses visible text, not an undocumented/native Scaffold Logs JSON schema.
It preserves unparsed text and reports malformed/truncated JSON rather than
silently repairing it.
"""
from __future__ import annotations
import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

# Accept observed dotted and underscore-style tool IDs, but require a separator
# so headings such as OUTPUT are not mistaken for tool names.
TOOL_RE = re.compile(r"^[A-Za-z][A-Za-z0-9]*(?:[_.-][A-Za-z0-9]+)+$")
SCORE_RE = re.compile(r"^(?P<case>(?:WB|BB)\w+)\s*[-–]\s*(?P<name>.+?)\s*$", re.I)
INDIRECT_RE = re.compile(r"^INDIRECT\s+(?P<score>\S+)", re.I)


def decode_object(lines: list[str], start: int) -> tuple[Any | None, str | None]:
    joined = "\n".join(lines)
    offset = sum(len(line) + 1 for line in lines[:start])
    brace = joined.find("{", offset)
    if brace < 0:
        return None, "no JSON object found"
    try:
        value, _ = json.JSONDecoder().raw_decode(joined[brace:])
    except json.JSONDecodeError as exc:
        return None, f"invalid or incomplete JSON: {exc.msg} at character {exc.pos}"
    return value, None


def parse_reading_view(text: str) -> dict[str, Any]:
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    result: dict[str, Any] = {
        "parser": "gray-swan-scaffold-reading-view/0.1",
        "source_format": "copied_reading_view_text",
        "native_scaffold_json_schema_verified": False,
        "challenge_scores": [],
        "used_tools_count": None,
        "tool_calls": [],
        "final_summary": None,
        "warnings": [
            "Best-effort parser for copied reading-view text; not a verified native export schema."
        ],
    }

    i = 0
    while i < len(lines):
        row = SCORE_RE.match(lines[i].strip())
        if row:
            score = None
            if i + 1 < len(lines):
                score_match = INDIRECT_RE.match(lines[i + 1].strip())
                if score_match:
                    score = score_match.group("score")
                    i += 1
            result["challenge_scores"].append({
                "case_id": row.group("case"),
                "name": row.group("name"),
                "score_text": score,
            })
        used = re.search(r"\bUsed\s+(\d+)\s+tools?\b", lines[i], re.I)
        if used:
            result["used_tools_count"] = int(used.group(1))
        if lines[i].strip().lower() in {"scaffold logs >", "scaffold logs"}:
            summary = []
            for candidate in lines[i + 1:]:
                if candidate.strip().lower() in {"payload launched", "payload 2 injections"}:
                    break
                summary.append(candidate)
            if "\n".join(summary).strip():
                result["final_summary"] = "\n".join(summary).strip()
        i += 1

    i = 0
    while i < len(lines):
        label = lines[i].strip()
        if not TOOL_RE.match(label):
            i += 1
            continue
        look_end = min(len(lines), i + 31)
        output_idx = next((j for j in range(i + 1, look_end)
                           if lines[j].strip().upper() == "OUTPUT"), None)
        json_idx = next((j for j in range(i + 1, look_end) if "{" in lines[j]), None)
        if output_idx is None and json_idx is None:
            i += 1
            continue
        call = {"tool_name": label, "input": None, "output": None,
                "input_parse_error": None, "output_parse_error": None}
        if output_idx is not None:
            input_idx = json_idx if json_idx is not None and json_idx < output_idx else None
            if input_idx is None:
                call["input_parse_error"] = "no input JSON object visible before OUTPUT"
            else:
                call["input"], call["input_parse_error"] = decode_object(lines[:output_idx], input_idx)
            output_json_idx = next((j for j in range(output_idx + 1, look_end)
                                    if "{" in lines[j]), None)
            if output_json_idx is None:
                call["output_parse_error"] = "no output JSON object visible after OUTPUT"
            else:
                call["output"], call["output_parse_error"] = decode_object(lines, output_json_idx)
        else:
            call["input"], call["input_parse_error"] = decode_object(lines, json_idx)
            call["output_parse_error"] = "OUTPUT marker not visible"
        result["tool_calls"].append(call)
        i += 1

    if not result["tool_calls"]:
        result["warnings"].append("No tool entry recognized; include a tool label and expanded input/output together.")
    return result


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("input", type=Path, help="text copied from Scaffold Logs reading view")
    ap.add_argument("-o", "--output", type=Path, help="output JSON path (default: stdout)")
    args = ap.parse_args()
    try:
        parsed = parse_reading_view(args.input.read_text(encoding="utf-8"))
    except OSError as exc:
        print(f"Cannot read {args.input}: {exc}", file=sys.stderr)
        return 2
    rendered = json.dumps(parsed, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
