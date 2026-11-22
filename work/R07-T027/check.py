#!/usr/bin/env python3
"""Validate leap metadata and reference behavior without changing the learner stub."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
EXERCISE = ROOT / "exercises/practice/leap"
CONFIG = EXERCISE / ".meta/config.json"
VALIDATOR = ROOT / "bin/validate_one_exercise"
EVIDENCE = Path(__file__).resolve().parent / "evidence.json"


class CheckError(ValueError):
    pass


def command_environment() -> dict[str, str]:
    environment = os.environ.copy()
    brew = shutil.which("brew", path=environment.get("PATH"))
    if brew:
        prefix = subprocess.run([brew, "--prefix"], text=True, capture_output=True, check=False)
        if prefix.returncode == 0:
            environment["PATH"] = f"{Path(prefix.stdout.strip()) / 'bin'}:{environment.get('PATH', '')}"
    return environment


COMMAND_ENV = command_environment()


def resolve_declared_files(config: dict[str, Any], exercise_root: Path) -> dict[str, list[Path]]:
    files = config.get("files")
    if not isinstance(files, dict):
        raise CheckError("files must be an object")

    root = exercise_root.resolve()
    resolved: dict[str, list[Path]] = {}
    for category, entries in files.items():
        if not isinstance(entries, list):
            raise CheckError(f"files.{category} must be an array")
        resolved[category] = []
        for entry in entries:
            if not isinstance(entry, str) or not entry:
                raise CheckError(f"files.{category} entries must be non-empty paths")
            relative = Path(entry)
            if relative.is_absolute():
                raise CheckError(f"Path is outside exercise: {entry}")
            candidate = (root / relative).resolve()
            try:
                candidate.relative_to(root)
            except ValueError as error:
                raise CheckError(f"Path is outside exercise: {entry}") from error
            if not candidate.is_file():
                raise CheckError(f"Missing file: {entry}")
            resolved[category].append(candidate)

    for category in ("solution", "test"):
        if not resolved.get(category):
            raise CheckError(f"files.{category} must declare at least one file")
    if not (resolved.get("example") or resolved.get("exemplar")):
        raise CheckError("files.example or files.exemplar must declare at least one file")
    return resolved


def load_config(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise CheckError(f"Cannot read config: {error}") from error
    if not isinstance(data, dict):
        raise CheckError("config must be a JSON object")
    return data


def get_version(command: list[str]) -> str:
    try:
        result = subprocess.run(command, text=True, capture_output=True, check=False, env=COMMAND_ENV)
    except OSError as error:
        return f"unavailable: {error}"
    output = (result.stdout or result.stderr).strip().splitlines()
    return output[0] if output else f"exit {result.returncode}"


def run_jq(expression: str, input_text: str) -> tuple[int, str]:
    result = subprocess.run(
        ["jq", "-r", expression],
        input=input_text,
        text=True,
        capture_output=True,
        check=False,
        env=COMMAND_ENV,
    )
    return result.returncode, (result.stdout or result.stderr).strip()


def micro_examples() -> dict[str, Any]:
    expression = '(if (.year // 0) == 0 then "missing" else (.year // 0 | tostring) end)'
    null_return, null_output = run_jq(expression, '{"year":null}')
    false_return, false_output = run_jq(expression, '{"year":false}')

    leap_expression = '(.year // 0) as $year | $year % 4 == 0 and $year % 100 != 0 or $year % 400 == 0'
    leap_return, leap_output = run_jq(leap_expression, '{"year":1996}')

    pitfall_expression = '(false // 0), (null // 0)'
    pitfall_return, pitfall_output = run_jq(pitfall_expression, 'null')

    cases = [
        {
            "name": "null field defaults with //",
            "expression": expression,
            "input": '{"year":null}',
            "expected": "missing",
            "actual": null_output,
            "return_code": null_return,
            "passed": null_return == 0 and null_output == "missing",
        },
        {
            "name": "false field defaults with //",
            "expression": expression,
            "input": '{"year":false}',
            "expected": "missing",
            "actual": false_output,
            "return_code": false_return,
            "passed": false_return == 0 and false_output == "missing",
        },
        {
            "name": "reference leap expression",
            "expression": leap_expression,
            "input": '{"year":1996}',
            "expected": "true",
            "actual": leap_output,
            "return_code": leap_return,
            "passed": leap_return == 0 and leap_output == "true",
        },
        {
            "name": "false and null are both fallbacks",
            "expression": pitfall_expression,
            "input": "null",
            "expected": "0\n0",
            "actual": pitfall_output,
            "return_code": pitfall_return,
            "passed": pitfall_return == 0 and pitfall_output == "0\n0",
        },
    ]
    return {"cases": cases, "passed": all(case["passed"] for case in cases)}


def run_reference_tests(files: dict[str, list[Path]]) -> dict[str, Any]:
    solution = files["solution"][0]
    test_file = files["test"][0]
    reference_files = files.get("example") or files.get("exemplar")
    reference = reference_files[0]

    test_text = test_file.read_text(encoding="utf-8")
    expected_cases = len(re.findall(r"(?m)^\s*@test\s+", test_text))
    stub_hash_before = hashlib.sha256(solution.read_bytes()).hexdigest()

    with tempfile.TemporaryDirectory(prefix="leap-validation-") as temporary:
        temporary_root = Path(temporary)
        copied_exercise = temporary_root / "exercises/practice/leap"
        shutil.copytree(EXERCISE, copied_exercise, copy_function=shutil.copy2)
        shutil.copy2(reference, copied_exercise / solution.relative_to(EXERCISE))

        bin_directory = temporary_root / "bin"
        bin_directory.mkdir()
        (bin_directory / "validate_one_exercise").symlink_to(VALIDATOR)

        completed = subprocess.run(
            ["bin/validate_one_exercise", "exercises/practice/leap"],
            cwd=temporary_root,
            text=True,
            capture_output=True,
            check=False,
            env=COMMAND_ENV,
        )

    output = completed.stdout + completed.stderr
    plan_match = re.search(r"(?m)^1\.\.([0-9]+)\s*$", output)
    planned_count = int(plan_match.group(1)) if plan_match else 0
    executed_count = len(re.findall(r"(?m)^ok\s+[0-9]+\b", output))
    skipped_count = len(re.findall(r"(?m)^ok\s+[0-9]+\b.*#\s*skip", output))

    checks = {
        "child_return_code_zero": completed.returncode == 0,
        "test_plan_nonzero": planned_count > 0,
        "test_count_matches_plan": planned_count == executed_count,
        "test_count_matches_suite": executed_count == expected_cases,
        "no_skipped_cases": skipped_count == 0,
        "learner_stub_unchanged": hashlib.sha256(solution.read_bytes()).hexdigest() == stub_hash_before,
    }
    return {
        "command": ["bin/validate_one_exercise", "exercises/practice/leap"],
        "suite_test_count": expected_cases,
        "planned_test_count": planned_count,
        "executed_test_count": executed_count,
        "skipped_test_count": skipped_count,
        "return_code": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "learner_stub_sha256_before": stub_hash_before,
        "learner_stub_sha256_after": hashlib.sha256(solution.read_bytes()).hexdigest(),
        "checks": checks,
        "passed": all(checks.values()),
        "reference_path": reference.relative_to(ROOT).as_posix(),
        "test_path": test_file.relative_to(ROOT).as_posix(),
        "solution_path": solution.relative_to(ROOT).as_posix(),
    }


def make_invalid_fixture(root: Path, category: str, entry: str) -> dict[str, Any]:
    (root / ".meta").mkdir(parents=True)
    for name in ("solution.jq", "test.bats", "bats-extra.bash", "bats-jq.bash"):
        (root / name).write_text("fixture\n", encoding="utf-8")
    (root / ".meta/example.jq").write_text("fixture\n", encoding="utf-8")
    config = {"files": {"solution": ["solution.jq"], "test": ["test.bats"], "example": [".meta/example.jq"]}}
    config["files"][category] = [entry]
    (root / ".meta/config.json").write_text(json.dumps(config), encoding="utf-8")
    return config


def invalid_metadata_checks() -> list[dict[str, Any]]:
    cases = [
        ("missing-reference", "example", ".meta/missing.jq", "Missing file: .meta/missing.jq"),
        ("missing-test", "test", "missing-test.bats", "Missing file: missing-test.bats"),
        ("outside-exercise", "example", "../outside.jq", "Path is outside exercise: ../outside.jq"),
    ]
    results = []
    with tempfile.TemporaryDirectory(prefix="leap-metadata-") as temporary:
        for name, category, entry, expected in cases:
            fixture_root = Path(temporary) / name
            config = make_invalid_fixture(fixture_root, category, entry)
            try:
                resolve_declared_files(load_config(fixture_root / ".meta/config.json"), fixture_root)
            except CheckError as error:
                actual = str(error)
            else:
                actual = "accepted invalid metadata"
            results.append({"name": name, "input": config, "expected": expected, "actual": actual, "passed": actual == expected})
    return results


def main() -> int:
    evidence: dict[str, Any] = {
        "inputs": {},
        "expected_vs_actual": {},
        "tool_versions": {
            "python": get_version([sys.executable, "--version"]),
            "jq": get_version(["jq", "--version"]),
            "bats": get_version(["bats", "--version"]),
            "bash": get_version(["bash", "--version"]),
        },
    }
    failures: list[str] = []

    config = load_config(CONFIG)
    evidence["inputs"]["real_config"] = config
    try:
        files = resolve_declared_files(config, EXERCISE)
        evidence["expected_vs_actual"]["real_metadata"] = {
            "expected": "all declared files resolve inside the exercise directory",
            "actual": {category: [path.relative_to(ROOT).as_posix() for path in paths] for category, paths in files.items()},
            "passed": True,
        }
        runner = run_reference_tests(files)
        evidence["expected_vs_actual"]["reference_tests"] = runner
        if not runner["passed"]:
            failures.append("reference tests failed: " + ", ".join(name for name, passed in runner["checks"].items() if not passed))
    except CheckError as error:
        evidence["expected_vs_actual"]["real_metadata"] = {"expected": "valid metadata", "actual": str(error), "passed": False}
        failures.append(f"real metadata failed: {error}")

    micro = micro_examples()
    evidence["expected_vs_actual"]["micro_examples"] = micro
    if not micro["passed"]:
        failures.append("micro-example assertion failed")

    fixtures = invalid_metadata_checks()
    evidence["expected_vs_actual"]["invalid_metadata_fixtures"] = fixtures
    for fixture in fixtures:
        if not fixture["passed"]:
            failures.append(f"invalid fixture failed: {fixture['name']}")

    EVIDENCE.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print(f"Evidence written to {EVIDENCE.relative_to(ROOT)}")
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        return 1

    runner = evidence["expected_vs_actual"]["reference_tests"]
    print(f"PASS: {runner['executed_test_count']} reference cases executed")
    print("PASS: real metadata and three invalid metadata fixtures")
    print("PASS: null/false and reference micro-example assertions")
    print("PASS: learner stub unchanged")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
