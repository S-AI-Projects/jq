#!/usr/bin/env python3
"""Verify anagram reference behavior and a contract-based scratch mutant."""

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
EXERCISE_REL = Path("exercises/practice/anagram")
EXERCISE = ROOT / EXERCISE_REL
CONFIG_PATH = EXERCISE / ".meta/config.json"
EVIDENCE_PATH = Path(__file__).resolve().parent / "evidence.json"
MUTATION = {
    "description": "remove only the case-insensitive self-match exclusion",
    "original": "(ascii_upcase != $subj) and (encode == $code)",
    "replacement": "(encode == $code)",
}
MINIMAL_DIAGNOSTIC = {
    "subject": "a",
    "candidates": ["a"],
}
MINIMAL_EXPECTED = "[]"
MUTATED_MINIMAL_EXPECTED = '["a"]'
REJECTING_TEST = "words are not anagrams of themselves"
NAMED_TESTS = {
    "no matches",
    "detects two anagrams",
    "does not detect anagram subsets",
}


class CheckError(Exception):
    """Raised when an expected input or result cannot be verified."""


def version(command):
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


def read_cases(test_path, solution_name):
    source = test_path.read_text(encoding="utf-8")
    declarations = list(
        re.finditer(r"""(?m)^@test\s+(["'])(.*?)\1\s*\{""", source)
    )
    if not declarations:
        raise CheckError("No Bats test cases found")
    cases = []
    for index, declaration in enumerate(declarations):
        end = (
            declarations[index + 1].start()
            if index + 1 < len(declarations)
            else len(source)
        )
        body = source[declaration.end() : end]
        input_match = re.search(
            r"(?ms)^[ \t]*run jq -c -f "
            + re.escape(solution_name)
            + r"[^\n]*<< 'END_INPUT'[ \t]*\n"
            r"(.*?)^[ \t]*END_INPUT[ \t]*$",
            body,
        )
        expected_match = re.search(r"(?m)^[ \t]*expected=(.+?)\s*$", body)
        if not input_match or not expected_match:
            raise CheckError(f"Could not parse Bats case {declaration.group(2)!r}")
        if (
            "assert_success" not in body
            or 'assert_equal "$output" "$expected"' not in body
        ):
            raise CheckError(f"Missing assertions in {declaration.group(2)!r}")
        expected_tokens = shlex.split(expected_match.group(1))
        if len(expected_tokens) != 1:
            raise CheckError(
                f"Unsupported expected output in {declaration.group(2)!r}"
            )
        cases.append(
            {
                "name": declaration.group(2),
                "input": json.loads(input_match.group(1)),
                "expected": expected_tokens[0],
                "skip_directive_active": bool(
                    re.search(
                        r"(?m)^\s*\[\[ \$BATS_RUN_SKIPPED == \"true\" \]\] \|\| skip\s*$",
                        body,
                    )
                ),
            }
        )
    return cases


def hash_solutions(paths):
    return {
        path.relative_to(ROOT).as_posix(): hashlib.sha256(
            path.read_bytes()
        ).hexdigest()
        for path in paths
    }


def run_input(reference_path, solution_name, test_input):
    with tempfile.TemporaryDirectory(prefix="anagram-input-") as temp:
        copied_reference = Path(temp) / solution_name
        copied_reference.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(reference_path, copied_reference)
        result = subprocess.run(
            ["jq", "-c", "-f", solution_name],
            cwd=copied_reference.parent,
            input=json.dumps(test_input),
            check=False,
            capture_output=True,
            text=True,
        )
    return {
        "return_code": result.returncode,
        "actual": result.stdout.rstrip("\n"),
        "stderr": result.stderr,
    }


def tap_results(output):
    plans = re.findall(r"(?m)^1\.\.(\d+)\s*$", output)
    rows = re.findall(r"(?mi)^(ok|not ok)\s+(\d+)\s*(.*)$", output)
    skipped = [
        row
        for row in rows
        if re.search(r"#\s*skip(?:\s|$)", row[2], re.IGNORECASE)
    ]
    failed = [row for row in rows if row[0].lower() == "not ok"]
    return {
        "plan_count": int(plans[0]) if len(plans) == 1 else None,
        "plan_entries": len(plans),
        "reported_count": len(rows),
        "executed_count": len(rows) - len(skipped),
        "skipped_count": len(skipped),
        "failed_count": len(failed),
        "failed_test_names": [
            re.sub(r"\s+#.*$", "", row[2]).strip() for row in failed
        ],
        "test_names": [
            re.sub(r"\s+#.*$", "", row[2]).strip() for row in rows
        ],
    }


def run_validator_copy(reference_path, mutated_bytes, expected_count):
    with tempfile.TemporaryDirectory(prefix="anagram-validator-") as temp:
        temporary_root = Path(temp)
        copied_exercise = temporary_root / EXERCISE_REL
        shutil.copytree(EXERCISE, copied_exercise)
        if mutated_bytes is not None:
            (copied_exercise / reference_path.relative_to(EXERCISE)).write_bytes(
                mutated_bytes
            )
        bin_directory = temporary_root / "bin"
        bin_directory.mkdir()
        (bin_directory / "validate_one_exercise").symlink_to(
            ROOT / "bin/validate_one_exercise"
        )
        child = subprocess.run(
            ["bin/validate_one_exercise", str(EXERCISE_REL)],
            cwd=temporary_root,
            check=False,
            capture_output=True,
            text=True,
        )
    result = tap_results(child.stdout + child.stderr)
    result.update(
        {
            "command": [
                "bin/validate_one_exercise",
                str(EXERCISE_REL),
            ],
            "return_code": child.returncode,
            "expected_test_count": expected_count,
            "stdout": child.stdout,
            "stderr": child.stderr,
            "temporary_copy_cleaned": not temporary_root.exists(),
        }
    )
    result["passed"] = (
        result["return_code"] == 0
        and result["plan_entries"] == 1
        and result["plan_count"] == expected_count
        and result["reported_count"] == expected_count
        and result["executed_count"] == expected_count
        and result["skipped_count"] == 0
        and result["failed_count"] == 0
    )
    return result


def main():
    evidence = {
        "exercise": EXERCISE_REL.as_posix(),
        "tool_versions": {},
        "inputs": {},
        "case_comparisons": [],
        "mutant": {},
        "validator_runs": {},
        "learner_solution_hashes": {},
        "failures": [],
    }
    solution_paths = []
    before_hashes = {}
    failures = []
    try:
        config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        files = resolve_files(config)
        solution_paths = files["solution"]
        solution_name = solution_paths[0].relative_to(EXERCISE).as_posix()
        test_path = files["test"][0]
        reference_path = (files.get("example") or files.get("exemplar"))[0]
        cases = read_cases(test_path, solution_name)
        reference_text = reference_path.read_text(encoding="utf-8")
        if reference_text.count(MUTATION["original"]) != 1:
            raise CheckError("Could not uniquely locate intended mutant condition")
        mutant_text = reference_text.replace(
            MUTATION["original"], MUTATION["replacement"], 1
        )
        before_hashes = hash_solutions(solution_paths)
        evidence["inputs"] = {
            "cases": cases,
            "solution_path": solution_paths[0].relative_to(ROOT).as_posix(),
            "test_path": test_path.relative_to(ROOT).as_posix(),
            "example_path": reference_path.relative_to(ROOT).as_posix(),
            "mutation": MUTATION,
        }
        evidence["tool_versions"] = {
            "python": sys.version.split()[0],
            "jq": version(["jq", "--version"]),
            "bats": version(["bats", "--version"]),
            "bash": version(["bash", "--version"]),
        }

        per_case = []
        for case in cases:
            original = run_input(reference_path, solution_name, case["input"])
            with tempfile.TemporaryDirectory(prefix="anagram-mutant-input-") as temp:
                mutant_path = Path(temp) / solution_name
                mutant_path.parent.mkdir(parents=True, exist_ok=True)
                mutant_path.write_text(mutant_text, encoding="utf-8")
                mutant_result = subprocess.run(
                    ["jq", "-c", "-f", solution_name],
                    cwd=mutant_path.parent,
                    input=json.dumps(case["input"]),
                    check=False,
                    capture_output=True,
                    text=True,
                )
            mutated = {
                "return_code": mutant_result.returncode,
                "actual": mutant_result.stdout.rstrip("\n"),
                "stderr": mutant_result.stderr,
            }
            per_case.append(
                {
                    "name": case["name"],
                    "input": case["input"],
                    "expected": case["expected"],
                    "original": original["actual"],
                    "mutated": mutated["actual"],
                    "original_return_code": original["return_code"],
                    "mutated_return_code": mutated["return_code"],
                    "original_passed": (
                        original["return_code"] == 0
                        and original["actual"] == case["expected"]
                    ),
                    "mutant_rejected": (
                        mutated["return_code"] != 0
                        or mutated["actual"] != case["expected"]
                    ),
                }
            )
        evidence["case_comparisons"] = per_case
        if any(not item["original_passed"] for item in per_case):
            failures.append("original reference failed a Bats input assertion")

        by_name = {item["name"]: item for item in per_case}
        if not NAMED_TESTS.issubset(by_name):
            failures.append("one or more required named tests are missing")

        rejecting_case = by_name.get(REJECTING_TEST)
        if not rejecting_case or not rejecting_case["mutant_rejected"]:
            failures.append("existing self-match test did not reject mutant")

        minimal_original = run_input(
            reference_path,
            solution_name,
            MINIMAL_DIAGNOSTIC,
        )
        with tempfile.TemporaryDirectory(prefix="anagram-minimal-mutant-") as temp:
            mutant_path = Path(temp) / solution_name
            mutant_path.parent.mkdir(parents=True, exist_ok=True)
            mutant_path.write_text(mutant_text, encoding="utf-8")
            minimal_mutant = subprocess.run(
                ["jq", "-c", "-f", solution_name],
                cwd=mutant_path.parent,
                input=json.dumps(MINIMAL_DIAGNOSTIC),
                check=False,
                capture_output=True,
                text=True,
            )
        evidence["mutant"] = {
            "description": MUTATION["description"],
            "changed_expression": {
                "before": MUTATION["original"],
                "after": MUTATION["replacement"],
            },
            "existing_rejecting_test": {
                "name": REJECTING_TEST,
                "input": rejecting_case["input"],
                "expected": rejecting_case["expected"],
                "original": rejecting_case["original"],
                "mutated": rejecting_case["mutated"],
                "rejected": rejecting_case["mutant_rejected"],
            }
            if rejecting_case
            else None,
            "smallest_diagnostic": {
                "input": MINIMAL_DIAGNOSTIC,
                "expected": MINIMAL_EXPECTED,
                "original": minimal_original["actual"],
                "mutant_expected_to_fail_as": MUTATED_MINIMAL_EXPECTED,
                "mutated": minimal_mutant.stdout.rstrip("\n"),
                "original_return_code": minimal_original["return_code"],
                "mutated_return_code": minimal_mutant.returncode,
                "passed": (
                    minimal_original["return_code"] == 0
                    and minimal_original["actual"] == MINIMAL_EXPECTED
                    and minimal_mutant.returncode == 0
                    and minimal_mutant.stdout.rstrip("\n")
                    == MUTATED_MINIMAL_EXPECTED
                ),
            },
        }
        if not evidence["mutant"]["smallest_diagnostic"]["passed"]:
            failures.append("minimal diagnostic did not distinguish original and mutant")

        original_validator = run_validator_copy(
            reference_path,
            None,
            len(cases),
        )
        evidence["validator_runs"]["original"] = original_validator
        if not original_validator["passed"]:
            failures.append("original reference validator did not pass all tests")

        mutated_validator = run_validator_copy(
            reference_path,
            mutant_text.encode("utf-8"),
            len(cases),
        )
        evidence["validator_runs"]["mutated"] = mutated_validator
        if (
            mutated_validator["return_code"] == 0
            or mutated_validator["failed_count"] == 0
            or mutated_validator["executed_count"] != len(cases)
            or REJECTING_TEST not in mutated_validator["failed_test_names"]
        ):
            failures.append("mutated reference validator did not reject the mutant")
    except (OSError, KeyError, ValueError, CheckError, json.JSONDecodeError) as error:
        evidence["error"] = str(error)
        failures.append(str(error))
    finally:
        try:
            after_hashes = hash_solutions(solution_paths) if solution_paths else {}
        except OSError as error:
            after_hashes = {}
            failures.append(f"Could not hash learner solution after check: {error}")
        evidence["learner_solution_hashes"] = {
            "before": before_hashes,
            "after": after_hashes,
            "unchanged": bool(before_hashes) and before_hashes == after_hashes,
        }
        if not evidence["learner_solution_hashes"]["unchanged"]:
            failures.append("learner solution changed during checking")
        evidence["failures"] = failures
        evidence["passed"] = not failures
        EVIDENCE_PATH.write_text(
            json.dumps(evidence, indent=2) + "\n", encoding="utf-8"
        )

    print(f"Evidence: {EVIDENCE_PATH.relative_to(ROOT)}")
    for item in evidence["case_comparisons"]:
        print(
            f"{item['name']}: original={item['original']!r} "
            f"mutated={item['mutated']!r}"
        )
    for name, run in evidence["validator_runs"].items():
        print(
            f"{name} validator: executed={run['executed_count']} "
            f"skipped={run['skipped_count']} failed={run['failed_count']} "
            f"rc={run['return_code']}"
        )
    print(
        "Minimal diagnostic: "
        f"original={evidence.get('mutant', {}).get('smallest_diagnostic', {}).get('original')!r} "
        f"mutant={evidence.get('mutant', {}).get('smallest_diagnostic', {}).get('mutated')!r}"
    )
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        return 1
    print("Mutant rejected by an existing case; all reference checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
