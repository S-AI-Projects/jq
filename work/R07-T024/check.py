#!/usr/bin/env python3
"""Compare resistor-color reference behavior and validate it in isolation."""

import hashlib
import json
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parents[2]
EXERCISE_REL = Path("exercises/practice/resistor-color")
EXERCISE = ROOT / EXERCISE_REL
CONFIG_PATH = EXERCISE / ".meta/config.json"
EVIDENCE_PATH = Path(__file__).resolve().parent / "evidence.json"


class CheckError(Exception):
    """Raised when a configured exercise or check result is invalid."""


def version(command):
    result = subprocess.run(
        command, check=False, capture_output=True, text=True
    )
    if result.returncode:
        raise CheckError(
            f"{command[0]} --version failed ({result.returncode}): "
            f"{result.stderr.strip()}"
        )
    return (result.stdout or result.stderr).splitlines()[0]


def configured_files(config):
    entries = config.get("files")
    if not isinstance(entries, dict):
        raise CheckError("config files must be an object")

    exercise_root = EXERCISE.resolve()
    resolved = {}
    for category, paths in entries.items():
        if not isinstance(paths, list):
            raise CheckError(f"files.{category} must be an array")
        resolved[category] = []
        for path in paths:
            if not isinstance(path, str) or not path:
                raise CheckError(f"files.{category} contains an invalid path")
            relative = PurePosixPath(path)
            if (
                relative.is_absolute()
                or "\\" in path
                or ".." in relative.parts
                or (relative.parts and relative.parts[0].endswith(":"))
            ):
                raise CheckError(f"Path is outside exercise: {path}")
            absolute = (exercise_root / Path(*relative.parts)).resolve()
            try:
                absolute.relative_to(exercise_root)
            except ValueError as error:
                raise CheckError(f"Path is outside exercise: {path}") from error
            if not absolute.is_file():
                raise CheckError(f"Missing file: {path}")
            resolved[category].append(absolute)

    for category in ("solution", "test"):
        if not resolved.get(category):
            raise CheckError(f"files.{category} must declare a file")
    if not (resolved.get("example") or resolved.get("exemplar")):
        raise CheckError("files.example or files.exemplar must declare a file")
    return resolved


def read_cases(test_path, solution_name):
    source = test_path.read_text(encoding="utf-8")
    test_matches = list(
        re.finditer(r"""(?m)^@test\s+(["'])(.*?)\1\s*\{""", source)
    )
    if not test_matches:
        raise CheckError("No Bats test cases found")

    cases = []
    for index, match in enumerate(test_matches):
        end = (
            test_matches[index + 1].start()
            if index + 1 < len(test_matches)
            else len(source)
        )
        body = source[match.end() : end]
        input_match = re.search(
            r"(?ms)^[ \t]*run jq -c -f "
            + re.escape(solution_name)
            + r"[^\n]*<< 'END_INPUT'[ \t]*\n"
            r"(.*?)^[ \t]*END_INPUT[ \t]*$",
            body,
        )
        expected_match = re.search(r"(?m)^[ \t]*expected=(.+?)\s*$", body)
        if not input_match or not expected_match:
            raise CheckError(f"Could not extract test case {match.group(2)!r}")
        if (
            "assert_success" not in body
            or 'assert_equal "$output" "$expected"' not in body
        ):
            raise CheckError(f"Missing assertions in {match.group(2)!r}")
        expected_parts = shlex.split(expected_match.group(1))
        if len(expected_parts) != 1:
            raise CheckError(f"Unsupported expected value in {match.group(2)!r}")
        cases.append(
            {
                "name": match.group(2),
                "input": json.loads(input_match.group(1)),
                "expected": expected_parts[0],
            }
        )
    return cases


def git_baseline_reference():
    merge_base = subprocess.run(
        ["git", "merge-base", "HEAD", "origin/main"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if merge_base.returncode:
        raise CheckError(f"git merge-base failed: {merge_base.stderr.strip()}")
    baseline = subprocess.run(
        [
            "git",
            "show",
            f"{merge_base.stdout.strip()}:{EXERCISE_REL}/.meta/example.jq",
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
    )
    if baseline.returncode:
        raise CheckError(
            f"Could not read baseline reference: {baseline.stderr.decode().strip()}"
        )
    return baseline.stdout, merge_base.stdout.strip()


def learner_hashes(solution_paths):
    return {
        path.relative_to(ROOT).as_posix(): hashlib.sha256(
            path.read_bytes()
        ).hexdigest()
        for path in solution_paths
    }


def run_case_outputs(label, source_bytes, cases, solution_name):
    records = []
    with tempfile.TemporaryDirectory(prefix=f"resistor-color-{label}-") as temp:
        copy = Path(temp) / solution_name
        copy.parent.mkdir(parents=True, exist_ok=True)
        copy.write_bytes(source_bytes)
        for case in cases:
            result = subprocess.run(
                ["jq", "-c", "-f", solution_name],
                cwd=copy.parent,
                input=json.dumps(case["input"]),
                check=False,
                capture_output=True,
                text=True,
            )
            actual = result.stdout.rstrip("\n")
            records.append(
                {
                    "name": case["name"],
                    "input": case["input"],
                    "expected": case["expected"],
                    "actual": actual,
                    "return_code": result.returncode,
                    "stderr": result.stderr,
                    "passed": (
                        result.returncode == 0
                        and actual == case["expected"]
                    ),
                }
            )
    return records


def run_validator(reference_bytes, files, cases):
    solution = files["solution"][0]
    with tempfile.TemporaryDirectory(prefix="resistor-color-validation-") as temp:
        temporary_root = Path(temp)
        copied_exercise = temporary_root / EXERCISE_REL
        shutil.copytree(EXERCISE, copied_exercise)
        (copied_exercise / solution.relative_to(EXERCISE)).write_bytes(
            reference_bytes
        )
        bin_directory = temporary_root / "bin"
        bin_directory.mkdir()
        (bin_directory / "validate_one_exercise").symlink_to(
            ROOT / "bin/validate_one_exercise"
        )
        result = subprocess.run(
            ["bin/validate_one_exercise", str(EXERCISE_REL)],
            cwd=temporary_root,
            check=False,
            capture_output=True,
            text=True,
        )

    output = result.stdout + result.stderr
    planned = re.findall(r"(?m)^1\.\.(\d+)\s*$", output)
    test_lines = re.findall(r"(?mi)^(ok|not ok)\s+\d+\s*(.*)$", output)
    skipped = [
        details
        for _, details in test_lines
        if re.search(r"#\s*skip(?:\s|$)", details, re.IGNORECASE)
    ]
    failed = sum(status.lower() == "not ok" for status, _ in test_lines)
    executed = len(test_lines) - len(skipped)
    planned_count = int(planned[0]) if len(planned) == 1 else None
    checks = {
        "child_return_code_zero": result.returncode == 0,
        "one_tap_plan": len(planned) == 1,
        "plan_matches_reported_tests": planned_count == len(test_lines),
        "reported_test_count_matches": len(test_lines) == len(cases),
        "nonzero_executed_count": executed > 0,
        "all_cases_executed": executed == len(cases),
        "no_skips": not skipped,
        "no_assertion_failures": failed == 0,
    }
    return {
        "command": [
            "bin/validate_one_exercise",
            str(EXERCISE_REL),
        ],
        "return_code": result.returncode,
        "planned_test_count": planned_count,
        "reported_test_count": len(test_lines),
        "executed_test_count": executed,
        "skipped_test_count": len(skipped),
        "assertion_failure_count": failed,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "checks": checks,
        "passed": all(checks.values()),
    }


def main():
    evidence = {
        "exercise": EXERCISE_REL.as_posix(),
        "tool_versions": {},
        "inputs": {},
        "before_after_cases": {},
        "validator": {},
        "learner_solution_hashes": {},
    }
    failures = []
    solution_paths = []
    before_hashes = {}
    try:
        config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        files = configured_files(config)
        solution_paths = files["solution"]
        solution_name = solution_paths[0].relative_to(EXERCISE).as_posix()
        test_path = files["test"][0]
        example_path = (files.get("example") or files.get("exemplar"))[0]
        cases = read_cases(test_path, solution_name)
        baseline_bytes, baseline_commit = git_baseline_reference()
        after_bytes = example_path.read_bytes()
        before_hashes = learner_hashes(solution_paths)

        evidence["inputs"] = {
            "cases": cases,
            "baseline_reference_commit": baseline_commit,
            "solution_paths": [
                path.relative_to(ROOT).as_posix() for path in solution_paths
            ],
            "test_path": test_path.relative_to(ROOT).as_posix(),
            "example_path": example_path.relative_to(ROOT).as_posix(),
        }
        evidence["tool_versions"] = {
            "python": sys.version.split()[0],
            "jq": version(["jq", "--version"]),
            "bats": version(["bats", "--version"]),
            "bash": version(["bash", "--version"]),
        }

        before = run_case_outputs("before", baseline_bytes, cases, solution_name)
        after = run_case_outputs("after", after_bytes, cases, solution_name)
        before_by_name = {record["name"]: record for record in before}
        after_by_name = {record["name"]: record for record in after}
        comparisons = []
        for case in cases:
            old = before_by_name[case["name"]]
            new = after_by_name[case["name"]]
            comparisons.append(
                {
                    "name": case["name"],
                    "input": case["input"],
                    "expected": case["expected"],
                    "before": old["actual"],
                    "after": new["actual"],
                    "outputs_equal": old["actual"] == new["actual"],
                    "before_passed": old["passed"],
                    "after_passed": new["passed"],
                    "return_codes": {
                        "before": old["return_code"],
                        "after": new["return_code"],
                    },
                }
            )
        evidence["before_after_cases"] = {
            "results": comparisons,
            "passed": (
                len(comparisons) == len(cases)
                and all(
                    item["outputs_equal"]
                    and item["before_passed"]
                    and item["after_passed"]
                    for item in comparisons
                )
            ),
        }
        if not evidence["before_after_cases"]["passed"]:
            failures.append("before/after case outputs differ or failed assertions")

        validator = run_validator(after_bytes, files, cases)
        evidence["validator"] = validator
        if not validator["passed"]:
            failures.append(
                "reference validator failed: "
                + ", ".join(
                    key for key, passed in validator["checks"].items() if not passed
                )
            )
        if len(cases) == 0:
            failures.append("zero enabled Bats cases found")
    except (OSError, KeyError, ValueError, CheckError, json.JSONDecodeError) as error:
        evidence["error"] = str(error)
        failures.append(str(error))
    finally:
        try:
            after_hashes = learner_hashes(solution_paths) if solution_paths else {}
        except OSError as error:
            after_hashes = {}
            failures.append(f"Could not hash learner solution after check: {error}")
        evidence["learner_solution_hashes"] = {
            "before": before_hashes,
            "after": after_hashes,
            "unchanged": before_hashes == after_hashes and bool(before_hashes),
        }
        if not evidence["learner_solution_hashes"]["unchanged"]:
            failures.append("learner solution files changed during the check")
        evidence["passed"] = not failures
        evidence["failures"] = failures
        EVIDENCE_PATH.write_text(
            json.dumps(evidence, indent=2) + "\n", encoding="utf-8"
        )

    print(f"Evidence: {EVIDENCE_PATH.relative_to(ROOT)}")
    for result in evidence.get("before_after_cases", {}).get("results", []):
        print(
            f"{result['name']}: before={result['before']!r} "
            f"after={result['after']!r} equal={result['outputs_equal']}"
        )
    if "validator" in evidence:
        print(
            "Validator cases executed: "
            f"{evidence['validator']['executed_test_count']} "
            f"(skipped: {evidence['validator']['skipped_test_count']})"
        )
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        return 1
    print("All before/after outputs and reference tests passed.")
    print("Learner solution files remain unchanged.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
