#!/usr/bin/env python3
"""Verify the allergies reference implementation without editing the learner stub."""

import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EXERCISE_REL = Path("exercises/practice/allergies")
EXERCISE = ROOT / EXERCISE_REL
CONFIG_PATH = EXERCISE / ".meta/config.json"
EVIDENCE_PATH = Path(__file__).resolve().parent / "evidence.json"
CASES = [
    {
        "name": "testing for eggs allergy:not allergic to anything",
        "input": {
            "property": "allergicTo",
            "input": {"item": "eggs", "score": 0},
        },
        "expected": "false",
    },
    {
        "name": "testing for eggs allergy:allergic only to eggs",
        "input": {
            "property": "allergicTo",
            "input": {"item": "eggs", "score": 1},
        },
        "expected": "true",
    },
    {
        "name": "testing for eggs allergy:allergic to eggs and something else",
        "input": {
            "property": "allergicTo",
            "input": {"item": "eggs", "score": 3},
        },
        "expected": "true",
    },
]


def configured_file(config, key, fallback=None):
    files = config["files"]
    entries = files.get(key) or (files.get(fallback) if fallback else None)
    if not entries:
        raise ValueError(f"Missing .meta/config.json files.{key} entry")
    return entries[0]


def run_version(command):
    result = subprocess.run(
        command, check=False, capture_output=True, text=True
    )
    if result.returncode:
        raise RuntimeError(
            f"Could not get version for {command[0]} "
            f"(exit {result.returncode}): {result.stderr.strip()}"
        )
    return (result.stdout or result.stderr).splitlines()[0]


def main():
    config = json.loads(CONFIG_PATH.read_text())
    solution_name = configured_file(config, "solution")
    tests_name = configured_file(config, "test")
    example_name = configured_file(config, "example", "exemplar")
    solution_path = EXERCISE / solution_name
    example_path = EXERCISE / example_name
    tests_path = EXERCISE / tests_name
    for path in (solution_path, example_path, tests_path):
        if not path.is_file():
            raise FileNotFoundError(f"Configured exercise file is missing: {path}")
    original_solution_hash = hashlib.sha256(solution_path.read_bytes()).hexdigest()
    tests_source = tests_path.read_text()

    evidence = {
        "exercise": str(EXERCISE_REL),
        "reference": example_name,
        "learner_solution": solution_name,
        "tool_versions": {
            "python": sys.version.split()[0],
            "jq": run_version(["jq", "--version"]),
            "bats": run_version(["bats", "--version"]),
            "bash": run_version(["bash", "--version"]),
        },
        "cases": [],
        "validation": {},
        "learner_solution_unchanged": None,
    }
    failures = []

    with tempfile.TemporaryDirectory(prefix="allergies-reference-") as temp:
        scratch_root = Path(temp)
        scratch_exercise = scratch_root / EXERCISE_REL
        shutil.copytree(EXERCISE, scratch_exercise)
        (scratch_root / "bin").mkdir()
        shutil.copy2(
            ROOT / "bin/validate_one_exercise",
            scratch_root / "bin/validate_one_exercise",
        )
        shutil.copy2(example_path, scratch_exercise / solution_name)

        for case in CASES:
            test_block = re.search(
                r"(?ms)^@test '"
                + re.escape(case["name"])
                + r"' \{\s*(.*?)(?=^@test |\Z)",
                tests_source,
            )
            if not test_block:
                failures.append(f"Could not find Bats case: {case['name']}")
                continue
            input_match = re.search(
                r"(?ms)^\s*run jq -r -f [^\n]+<< 'END_INPUT'\s*"
                r"(.*?)^\s*END_INPUT\s*$",
                test_block.group(1),
            )
            expected_match = re.search(
                r"(?m)^\s*expected=(true|false)\s*$", test_block.group(1)
            )
            if not input_match or not expected_match:
                failures.append(
                    f"Could not extract input and expected assertion for {case['name']}"
                )
                continue
            if (
                "assert_success" not in test_block.group(1)
                or 'assert_equal "$output" "$expected"' not in test_block.group(1)
            ):
                failures.append(
                    f"Missing expected Bats assertions for {case['name']}"
                )
                continue
            selected_input = json.loads(input_match.group(1))
            if selected_input != case["input"]:
                failures.append(
                    f"{case['name']}: Bats input changed: {selected_input!r}"
                )
                continue
            if expected_match.group(1) != case["expected"]:
                failures.append(
                    f"{case['name']}: Bats expected value changed to "
                    f"{expected_match.group(1)!r}"
                )
                continue
            result = subprocess.run(
                ["jq", "-r", "-f", solution_name],
                cwd=scratch_exercise,
                input=json.dumps(case["input"]),
                check=False,
                capture_output=True,
                text=True,
            )
            actual = result.stdout.strip()
            case_result = {
                "name": case["name"],
                "input": case["input"],
                "expected": case["expected"],
                "actual": actual,
                "return_code": result.returncode,
                "stderr": result.stderr.strip(),
            }
            evidence["cases"].append(case_result)
            if result.returncode:
                failures.append(
                    f"{case['name']}: jq exited {result.returncode}: "
                    f"{result.stderr.strip()}"
                )
            elif actual != case["expected"]:
                failures.append(
                    f"{case['name']}: expected {case['expected']!r}, got {actual!r}"
                )

        validation = subprocess.run(
            ["bin/validate_one_exercise", str(EXERCISE_REL)],
            cwd=scratch_root,
            check=False,
            capture_output=True,
            text=True,
        )
        output = validation.stdout + validation.stderr
        plan_match = re.search(r"(?m)^1\.\.(\d+)\s*$", output)
        result_lines = re.findall(r"(?m)^(?:ok|not ok) \d+(?: .*)?$", output)
        skipped_count = sum("# SKIP" in line.upper() for line in result_lines)
        executed_count = len(result_lines) - skipped_count
        failed_count = sum(line.startswith("not ok ") for line in result_lines)
        plan_count = int(plan_match.group(1)) if plan_match else None
        evidence["validation"] = {
            "command": ["bin/validate_one_exercise", str(EXERCISE_REL)],
            "return_code": validation.returncode,
            "planned_tests": plan_count,
            "reported_test_results": len(result_lines),
            "executed_tests": executed_count,
            "skipped_tests": skipped_count,
            "failed_tests": failed_count,
            "stdout": validation.stdout,
            "stderr": validation.stderr,
        }
        if validation.returncode:
            failures.append(
                f"validator exited {validation.returncode}: "
                f"{validation.stderr.strip() or validation.stdout.strip()}"
            )
        if plan_count is None:
            failures.append("validator output did not include a TAP test plan")
        elif plan_count != len(result_lines):
            failures.append(
                f"TAP plan reports {plan_count} tests but "
                f"{len(result_lines)} result lines were found"
            )
        if executed_count == 0:
            failures.append("validator ran zero tests")
        if failed_count:
            failures.append(f"validator reported {failed_count} failed tests")

    current_solution_hash = hashlib.sha256(solution_path.read_bytes()).hexdigest()
    evidence["learner_solution_unchanged"] = (
        current_solution_hash == original_solution_hash
    )
    if not evidence["learner_solution_unchanged"]:
        failures.append("learner solution changed during reference validation")

    EVIDENCE_PATH.write_text(json.dumps(evidence, indent=2) + "\n")
    print(f"Evidence: {EVIDENCE_PATH.relative_to(ROOT)}")
    for case in evidence["cases"]:
        print(
            f"{case['name']}: expected={case['expected']} "
            f"actual={case['actual']} rc={case['return_code']}"
        )
    print(
        "Executed tests: "
        f"{evidence['validation'].get('executed_tests', 0)} "
        f"(skipped: {evidence['validation'].get('skipped_tests', 0)})"
    )
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        return 1
    print("All selected cases and reference tests passed.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, KeyError, ValueError, RuntimeError, json.JSONDecodeError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        sys.exit(1)
