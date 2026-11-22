#!/usr/bin/env python3
"""Validate proverb exercise metadata and run its tests against the reference."""

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
EXERCISE = ROOT / "exercises/practice/proverb"
CONFIG = EXERCISE / ".meta/config.json"
VALIDATOR = ROOT / "bin/validate_one_exercise"
EVIDENCE = Path(__file__).resolve().parent / "evidence.json"


def command_environment() -> dict[str, str]:
    environment = os.environ.copy()
    brew = shutil.which("brew", path=environment.get("PATH"))
    if brew:
        prefix = subprocess.run([brew, "--prefix"], text=True, capture_output=True, check=False)
        if prefix.returncode == 0:
            environment["PATH"] = f"{Path(prefix.stdout.strip()) / 'bin'}:{environment.get('PATH', '')}"
    return environment


COMMAND_ENV = command_environment()


class MetadataError(ValueError):
    """Raised when a declared metadata path is invalid."""


def resolve_declared_files(config: dict[str, Any], exercise_root: Path) -> dict[str, list[Path]]:
    files = config.get("files")
    if not isinstance(files, dict):
        raise MetadataError("files must be an object")

    root = exercise_root.resolve()
    resolved: dict[str, list[Path]] = {}
    for category, entries in files.items():
        if not isinstance(entries, list):
            raise MetadataError(f"files.{category} must be an array")
        resolved[category] = []
        for entry in entries:
            if not isinstance(entry, str) or not entry:
                raise MetadataError(f"files.{category} entries must be non-empty paths")
            relative_path = Path(entry)
            if relative_path.is_absolute():
                raise MetadataError(f"Path is outside exercise: {entry}")
            candidate = (root / relative_path).resolve()
            try:
                candidate.relative_to(root)
            except ValueError as error:
                raise MetadataError(f"Path is outside exercise: {entry}") from error
            if not candidate.is_file():
                raise MetadataError(f"Missing file: {entry}")
            resolved[category].append(candidate)

    for category in ("solution", "test"):
        if not resolved.get(category):
            raise MetadataError(f"files.{category} must declare at least one file")
    if not (resolved.get("example") or resolved.get("exemplar")):
        raise MetadataError("files.example or files.exemplar must declare at least one file")
    return resolved


def load_config(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise MetadataError(f"Cannot read config: {error}") from error
    if not isinstance(data, dict):
        raise MetadataError("config must be a JSON object")
    return data


def make_fixture(root: Path, *, bad_path: tuple[str, str] | None = None) -> tuple[Path, dict[str, Any]]:
    (root / ".meta").mkdir(parents=True)
    for name in ("solution.jq", "test.bats", "bats-extra.bash", "bats-jq.bash"):
        (root / name).write_text("fixture\n", encoding="utf-8")
    (root / ".meta/example.jq").write_text("fixture\n", encoding="utf-8")
    config: dict[str, Any] = {
        "files": {
            "solution": ["solution.jq"],
            "test": ["test.bats"],
            "example": [".meta/example.jq"],
            "editor": ["bats-extra.bash", "bats-jq.bash"],
        }
    }
    if bad_path:
        category, path = bad_path
        config["files"][category] = [path]
    config_path = root / ".meta/config.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")
    return config_path, config


def check_metadata_fixtures() -> list[dict[str, Any]]:
    cases = [
        ("missing-reference", ("example", ".meta/missing.jq"), "Missing file: .meta/missing.jq"),
        ("missing-test", ("test", "missing-test.bats"), "Missing file: missing-test.bats"),
        ("outside-exercise", ("example", "../outside.jq"), "Path is outside exercise: ../outside.jq"),
    ]
    results = []
    with tempfile.TemporaryDirectory(prefix="proverb-metadata-") as temporary:
        for name, bad_path, expected in cases:
            fixture_root = Path(temporary) / name
            config_path, config = make_fixture(fixture_root, bad_path=bad_path)
            try:
                resolve_declared_files(load_config(config_path), fixture_root)
            except MetadataError as error:
                actual = str(error)
            else:
                actual = "accepted invalid metadata"
            results.append({
                "name": name,
                "input": config,
                "expected": expected,
                "actual": actual,
                "passed": actual == expected,
            })
    return results


def get_version(command: list[str]) -> str:
    try:
        result = subprocess.run(
            command, text=True, capture_output=True, check=False, env=COMMAND_ENV
        )
    except OSError as error:
        return f"unavailable: {error}"
    output = (result.stdout or result.stderr).strip().splitlines()
    return output[0] if output else f"exit {result.returncode}"


def run_reference_tests(files: dict[str, list[Path]]) -> dict[str, Any]:
    solution = files["solution"][0]
    test_file = files["test"][0]
    reference_files = files.get("example") or files.get("exemplar")
    reference = reference_files[0]
    test_text = test_file.read_text(encoding="utf-8")
    expected_cases = len(re.findall(r"^\s*@test\s+", test_text, flags=re.MULTILINE))
    stub_hash_before = hashlib.sha256(solution.read_bytes()).hexdigest()

    with tempfile.TemporaryDirectory(prefix="proverb-validation-") as temporary:
        temporary_root = Path(temporary)
        copied_exercise = temporary_root / "exercises/practice/proverb"
        shutil.copytree(EXERCISE, copied_exercise)
        shutil.copy2(reference, copied_exercise / solution.relative_to(EXERCISE))
        bin_directory = temporary_root / "bin"
        bin_directory.mkdir()
        (bin_directory / "validate_one_exercise").symlink_to(VALIDATOR)

        completed = subprocess.run(
            ["bin/validate_one_exercise", "exercises/practice/proverb"],
            cwd=temporary_root,
            text=True,
            capture_output=True,
            check=False,
            env=COMMAND_ENV,
        )

    output = completed.stdout + completed.stderr
    plan_match = re.search(r"(?m)^1\.\.(\d+)\s*$", output)
    executed_count = len(re.findall(r"(?m)^ok\s+\d+\b", output))
    has_skips = bool(re.search(r"(?m)^ok\s+\d+\b.*#\s*skip", output))
    stub_hash_after = hashlib.sha256(solution.read_bytes()).hexdigest()
    checks = {
        "return_code_is_zero": completed.returncode == 0,
        "planned_case_count_matches": bool(plan_match and int(plan_match.group(1)) == expected_cases),
        "executed_case_count_matches": executed_count == expected_cases,
        "no_cases_skipped": not has_skips,
        "learner_stub_unchanged": stub_hash_before == stub_hash_after,
    }
    return {
        "command": ["bin/validate_one_exercise", "exercises/practice/proverb"],
        "expected_case_count": expected_cases,
        "executed_case_count": executed_count,
        "return_code": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "learner_stub_sha256_before": stub_hash_before,
        "learner_stub_sha256_after": stub_hash_after,
        "checks": checks,
        "passed": all(checks.values()),
        "reference_path": reference.relative_to(ROOT).as_posix(),
        "test_path": test_file.relative_to(ROOT).as_posix(),
        "solution_path": solution.relative_to(ROOT).as_posix(),
    }


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
    failures = []
    config = load_config(CONFIG)
    evidence["inputs"]["real_config"] = config

    try:
        files = resolve_declared_files(config, EXERCISE)
        evidence["expected_vs_actual"]["real_metadata"] = {
            "expected": "all declared files resolve within the exercise directory",
            "actual": {
                category: [path.relative_to(ROOT).as_posix() for path in paths]
                for category, paths in files.items()
            },
            "passed": True,
        }
        runner = run_reference_tests(files)
        evidence["expected_vs_actual"]["reference_tests"] = runner
        if not runner["passed"]:
            failures.append("reference tests failed: " + ", ".join(
                name for name, passed in runner["checks"].items() if not passed
            ))
    except MetadataError as error:
        evidence["expected_vs_actual"]["real_metadata"] = {
            "expected": "all declared files resolve within the exercise directory",
            "actual": str(error),
            "passed": False,
        }
        failures.append(f"real metadata validation failed: {error}")

    fixtures = check_metadata_fixtures()
    evidence["expected_vs_actual"]["invalid_metadata_fixtures"] = fixtures
    for fixture in fixtures:
        if not fixture["passed"]:
            failures.append(f"invalid metadata fixture failed: {fixture['name']}")

    EVIDENCE.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print(f"Evidence written to {EVIDENCE.relative_to(ROOT)}")
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        return 1

    runner = evidence["expected_vs_actual"]["reference_tests"]
    print(f"PASS: {runner['executed_case_count']} reference cases executed")
    print("PASS: real metadata and all three invalid fixtures")
    print("PASS: learner stub unchanged")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
