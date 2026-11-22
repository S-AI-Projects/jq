#!/usr/bin/env python3
"""Review square-root canonical cases and validate the reference in isolation."""

import hashlib
import json
import re
import subprocess
import sys
import tempfile
import shutil
from pathlib import Path, PurePosixPath

try:
    import tomllib
    TOML_PARSER = "tomllib"
except ImportError:
    from pip._vendor import tomli as tomllib
    TOML_PARSER = "pip._vendor.tomli"


ROOT = Path(__file__).resolve().parents[2]
EXERCISE_REL = Path("exercises/practice/square-root")
EXERCISE = ROOT / EXERCISE_REL
CONFIG_PATH = EXERCISE / ".meta/config.json"
TESTS_TOML_PATH = EXERCISE / ".meta/tests.toml"
EVIDENCE_PATH = Path(__file__).resolve().parent / "evidence.json"
SELECTED_CASES = {
    "9b748478-7b0a-490c-b87a-609dacf631fd": {
        "name": "root of 1",
        "input": {"radicand": 1},
        "expected": "1",
    },
    "7d3aa9ba-9ac6-4e93-a18b-2e8b477139bb": {
        "name": "root of 4",
        "input": {"radicand": 4},
        "expected": "2",
    },
    "6624aabf-3659-4ae0-a1c8-25ae7f33c6ef": {
        "name": "root of 25",
        "input": {"radicand": 25},
        "expected": "5",
    },
}


class CheckError(Exception):
    """Raised when a validation requirement is not met."""


def get_version(command):
    result = subprocess.run(
        command, check=False, capture_output=True, text=True
    )
    if result.returncode:
        raise CheckError(
            f"{command[0]} version command failed ({result.returncode}): "
            f"{result.stderr.strip()}"
        )
    return (result.stdout or result.stderr).splitlines()[0]


def resolve_files(config):
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


def parse_tests_toml(text):
    """Parse tests.toml with Python's TOML parser."""
    try:
        records = tomllib.loads(text)
    except tomllib.TOMLDecodeError as error:
        raise CheckError(f"tests.toml is invalid TOML: {error}") from error
    if not isinstance(records, dict):
        raise CheckError("tests.toml must contain UUID tables")
    for case_id, entry in records.items():
        if not re.fullmatch(r"[0-9a-fA-F-]{36}", case_id):
            raise CheckError(f"Invalid UUID table in tests.toml: {case_id}")
        if not isinstance(entry, dict):
            raise CheckError(f"Expected a table for tests.toml UUID {case_id}")
        if not isinstance(entry.get("description"), str):
            raise CheckError(f"Missing description for tests.toml UUID {case_id}")
        if "include" in entry and not isinstance(entry["include"], bool):
            raise CheckError(f"include must be boolean for UUID {case_id}")
    return records


def inclusion_counts(records):
    included = sum(
        1 for entry in records.values() if entry.get("include", True)
    )
    excluded = sum(
        1 for entry in records.values() if entry.get("include", True) is False
    )
    return {"included": included, "excluded": excluded}


def parse_bats_cases(test_path, solution_name):
    source = test_path.read_text(encoding="utf-8")
    declarations = list(
        re.finditer(r"""(?m)^@test\s+(["'])(.*?)\1\s*\{""", source)
    )
    if not declarations:
        raise CheckError("No Bats tests found")
    cases = []
    for index, declaration in enumerate(declarations):
        end = (
            declarations[index + 1].start()
            if index + 1 < len(declarations)
            else len(source)
        )
        body = source[declaration.end() : end]
        input_match = re.search(
            r"(?ms)^[ \t]*run jq -r -f "
            + re.escape(solution_name)
            + r"[^\n]*<< 'END_INPUT'[ \t]*\n"
            r"(.*?)^[ \t]*END_INPUT[ \t]*$",
            body,
        )
        expected_match = re.search(
            r"(?m)^[ \t]*expected=(-?\d+)\s*$", body
        )
        if not input_match or not expected_match:
            raise CheckError(
                f"Could not read input/expected output: {declaration.group(2)}"
            )
        if (
            "assert_success" not in body
            or 'assert_equal "$output" "$expected"' not in body
        ):
            raise CheckError(
                f"Missing assertions in {declaration.group(2)!r}"
            )
        cases.append(
            {
                "name": declaration.group(2),
                "input": json.loads(input_match.group(1)),
                "expected": expected_match.group(1),
            }
        )
    return cases


def hash_solutions(solution_paths):
    return {
        path.relative_to(ROOT).as_posix(): hashlib.sha256(
            path.read_bytes()
        ).hexdigest()
        for path in solution_paths
    }


def run_case(reference_path, solution_name, case):
    with tempfile.TemporaryDirectory(prefix="square-root-case-") as temp:
        solution_copy = Path(temp) / solution_name
        solution_copy.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(reference_path, solution_copy)
        result = subprocess.run(
            ["jq", "-r", "-f", solution_name],
            cwd=solution_copy.parent,
            input=json.dumps(case["input"]),
            check=False,
            capture_output=True,
            text=True,
        )
    actual = result.stdout.rstrip("\n")
    return {
        "name": case["name"],
        "input": case["input"],
        "expected": case["expected"],
        "actual": actual,
        "return_code": result.returncode,
        "stderr": result.stderr,
        "passed": result.returncode == 0 and actual == case["expected"],
    }


def run_validator(files, cases, force_zero=False, reference_override=None):
    test_path = files["test"][0]
    example_path = (files.get("example") or files.get("exemplar"))[0]
    with tempfile.TemporaryDirectory(prefix="square-root-validation-") as temp:
        temporary_root = Path(temp)
        copied_exercise = temporary_root / EXERCISE_REL
        shutil.copytree(EXERCISE, copied_exercise)
        if reference_override is not None:
            (copied_exercise / example_path.relative_to(EXERCISE)).write_bytes(
                reference_override
            )
        if force_zero:
            copied_tests = copied_exercise / test_path.relative_to(EXERCISE)
            source = copied_tests.read_text(encoding="utf-8")
            source, replacements = re.subn(
                r"(?m)^(@test\b[^\n]*\{\s*)$",
                r'\1\n    skip "forced zero-test guard"',
                source,
            )
            if replacements != len(cases):
                raise CheckError(
                    f"Expected to skip {len(cases)} cases, skipped {replacements}"
                )
            copied_tests.write_text(source, encoding="utf-8")
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
    plans = re.findall(r"(?m)^1\.\.(\d+)\s*$", output)
    test_lines = re.findall(r"(?mi)^(ok|not ok)\s+\d+\s*(.*)$", output)
    skips = [
        details
        for _, details in test_lines
        if re.search(r"#\s*skip(?:\s|$)", details, re.IGNORECASE)
    ]
    failures = sum(status.lower() == "not ok" for status, _ in test_lines)
    executed = len(test_lines) - len(skips)
    plan = int(plans[0]) if len(plans) == 1 else None
    actual_names = [
        re.sub(r"\s+#.*$", "", details).strip()
        for _, details in test_lines
    ]
    expected_names = [case["name"] for case in cases]
    checks = {
        "child_return_code_zero": result.returncode == 0,
        "single_tap_plan": len(plans) == 1,
        "plan_matches_results": plan == len(test_lines),
        "reported_test_count_matches": len(test_lines) == len(cases),
        "nonzero_test_count": executed > 0,
        "all_tests_executed": executed == len(cases),
        "no_skips": not skips,
        "no_assertion_failures": failures == 0,
        "test_names_match": actual_names == expected_names,
    }
    return {
        "command": [
            "bin/validate_one_exercise",
            str(EXERCISE_REL),
        ],
        "return_code": result.returncode,
        "planned_test_count": plan,
        "reported_test_count": len(test_lines),
        "executed_test_count": executed,
        "skipped_test_count": len(skips),
        "assertion_failure_count": failures,
        "test_names": actual_names,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "checks": checks,
        "passed": all(checks.values()),
        "temporary_files_cleaned": not temporary_root.exists(),
    }


def main():
    evidence = {
        "tool_versions": {},
        "metadata": {},
        "selected_cases": [],
        "reference_tests": [],
        "validator": {},
        "learner_solution_hashes": {},
        "failures": [],
    }
    solutions = []
    initial_hashes = {}
    failures = []
    try:
        config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        files = resolve_files(config)
        solutions = files["solution"]
        solution_name = solutions[0].relative_to(EXERCISE).as_posix()
        test_path = files["test"][0]
        reference_path = (files.get("example") or files.get("exemplar"))[0]
        test_cases = parse_bats_cases(test_path, solution_name)
        metadata_text = TESTS_TOML_PATH.read_text(encoding="utf-8")
        records_after = parse_tests_toml(metadata_text)
        baseline = subprocess.run(
            ["git", "show", f"origin/main:{EXERCISE_REL}/.meta/tests.toml"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        if baseline.returncode:
            raise CheckError(
                f"Could not read baseline tests.toml: {baseline.stderr.strip()}"
            )
        records_before = parse_tests_toml(baseline.stdout)
        counts_before = inclusion_counts(records_before)
        counts_after = inclusion_counts(records_after)
        states_before = {
            case_id: entry.get("include", True)
            for case_id, entry in records_before.items()
        }
        states_after = {
            case_id: entry.get("include", True)
            for case_id, entry in records_after.items()
        }
        metadata_matches_tests = {
            entry["description"]: case_id
            for case_id, entry in records_after.items()
        }
        bats_names = {case["name"] for case in test_cases}
        if len(records_after) != 6:
            failures.append(f"Expected 6 canonical entries, found {len(records_after)}")
        if counts_before != {"included": 6, "excluded": 0}:
            failures.append(f"Unexpected before inclusion counts: {counts_before}")
        if counts_after != {"included": 6, "excluded": 0}:
            failures.append(f"Unexpected after inclusion counts: {counts_after}")
        if states_before != states_after:
            failures.append("Canonical include states changed")
        if set(metadata_matches_tests) != bats_names:
            failures.append(
                "Canonical metadata descriptions do not match Bats test names"
            )
        for case_id, selected in SELECTED_CASES.items():
            metadata = records_after.get(case_id)
            if not metadata:
                failures.append(f"Selected UUID missing from tests.toml: {case_id}")
                continue
            if metadata.get("description") != selected["name"]:
                failures.append(f"Unexpected description for UUID {case_id}")
            if selected["name"] not in bats_names:
                failures.append(f"No generated Bats case: {selected['name']}")

        evidence["metadata"] = {
            "input_path": str((EXERCISE_REL / ".meta/tests.toml").as_posix()),
            "included_excluded_before": counts_before,
            "included_excluded_after": counts_after,
            "include_states_unchanged": states_before == states_after,
            "toml_record_count": len(records_after),
            "metadata_description_to_uuid": metadata_matches_tests,
            "toml_parser": TOML_PARSER,
            "toml_parse_passed": len(records_after) == 6,
        }
        evidence["tool_versions"] = {
            "python": sys.version.split()[0],
            "jq": get_version(["jq", "--version"]),
            "bats": get_version(["bats", "--version"]),
            "bash": get_version(["bash", "--version"]),
        }
        initial_hashes = hash_solutions(solutions)
        all_case_results = [
            run_case(reference_path, solution_name, case) for case in test_cases
        ]
        evidence["reference_tests"] = all_case_results
        if len(all_case_results) != len(test_cases):
            failures.append("Not all Bats cases were run through the reference")
        if any(not result["passed"] for result in all_case_results):
            failures.append("At least one reference output assertion failed")
        evidence["selected_cases"] = [
            {
                "uuid": case_id,
                "test_name": selected["name"],
                "input": selected["input"],
                "expected": selected["expected"],
                "actual": next(
                    (
                        result["actual"]
                        for result in all_case_results
                        if result["name"] == selected["name"]
                    ),
                    None,
                ),
                "passed": any(
                    result["name"] == selected["name"] and result["passed"]
                    for result in all_case_results
                ),
            }
            for case_id, selected in SELECTED_CASES.items()
        ]
        if not all(item["passed"] for item in evidence["selected_cases"]):
            failures.append("A selected UUID rationale case did not pass")

        validator = run_validator(files, test_cases)
        evidence["validator"] = validator
        if not validator["passed"]:
            failures.append(
                "Reference validation failed: "
                + ", ".join(
                    name for name, passed in validator["checks"].items() if not passed
                )
            )
        zero_test_run = run_validator(
            files,
            test_cases,
            force_zero=True,
        )
        zero_test_rejected = (
            zero_test_run["executed_test_count"] == 0
            and zero_test_run["skipped_test_count"] == len(test_cases)
            and not zero_test_run["passed"]
            and not zero_test_run["checks"]["nonzero_test_count"]
        )
        evidence["zero_test_guard"] = {
            "expected": "reject a run with zero executed tests",
            "actual": zero_test_run,
            "rejected": zero_test_rejected,
        }
        if not zero_test_rejected:
            failures.append("zero-test validator run was not rejected")

        failing_reference = b'error("deliberate reference failure")\n'
        failing_run = run_validator(
            files,
            test_cases,
            reference_override=failing_reference,
        )
        assertion_failure_rejected = (
            failing_run["return_code"] != 0
            and failing_run["assertion_failure_count"] > 0
            and not failing_run["passed"]
        )
        evidence["assertion_failure_guard"] = {
            "expected": "reject a nonzero validator exit with assertion failures",
            "actual": failing_run,
            "rejected": assertion_failure_rejected,
        }
        if not assertion_failure_rejected:
            failures.append("deliberate assertion failure was not rejected")
    except (OSError, KeyError, ValueError, CheckError, json.JSONDecodeError) as error:
        evidence["error"] = str(error)
        failures.append(str(error))
    finally:
        try:
            final_hashes = hash_solutions(solutions) if solutions else {}
        except OSError as error:
            final_hashes = {}
            failures.append(f"Could not hash learner solution files: {error}")
        evidence["learner_solution_hashes"] = {
            "before": initial_hashes,
            "after": final_hashes,
            "unchanged": bool(initial_hashes) and initial_hashes == final_hashes,
        }
        if not evidence["learner_solution_hashes"]["unchanged"]:
            failures.append("Learner solution files changed during checking")
        evidence["failures"] = failures
        evidence["passed"] = not failures
        EVIDENCE_PATH.write_text(
            json.dumps(evidence, indent=2) + "\n", encoding="utf-8"
        )

    print(f"Evidence: {EVIDENCE_PATH.relative_to(ROOT)}")
    for result in evidence["selected_cases"]:
        print(
            f"{result['uuid']} ({result['test_name']}): "
            f"expected={result['expected']} actual={result['actual']}"
        )
    if evidence["validator"]:
        print(
            f"Executed tests: {evidence['validator']['executed_test_count']} "
            f"(skipped: {evidence['validator']['skipped_test_count']})"
        )
    print(
        "Canonical include counts: "
        f"{evidence['metadata'].get('included_excluded_before')} -> "
        f"{evidence['metadata'].get('included_excluded_after')}"
    )
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        return 1
    print("All selected rationales, metadata checks, and reference tests passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
