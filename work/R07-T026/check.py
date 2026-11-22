#!/usr/bin/env python3
"""Compare phone-number reference and character-fold alternatives."""

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
EXERCISE_REL = Path("exercises/practice/phone-number")
EXERCISE = ROOT / EXERCISE_REL
CONFIG_PATH = EXERCISE / ".meta/config.json"
EVIDENCE_PATH = Path(__file__).resolve().parent / "evidence.json"
NAMED_CASES = {
    "cleans the number",
    "cleans numbers with dots",
    "cleans numbers with multiple spaces",
}

ALTERNATIVE = r'''
def assert(cond; err): if cond then . else (err | halt_error) end;
def refute(cond; err): assert(cond | not; err);

def clean:
  reduce (.phrase | explode[]) as $codepoint
    ("";
      . + (
        if ($codepoint == 32 or $codepoint == 40 or $codepoint == 41
            or $codepoint == 43 or $codepoint == 45 or $codepoint == 46) then
          ""
        else
          ([$codepoint] | implode)
        end
      )
    );

clean
| assert(length >= 10; "must not be fewer than 10 digits")
| assert(length <= 11; "must not be greater than 11 digits")
| if length == 11 then
    assert(startswith("1"); "11 digits must start with 1")
    | .[1:length]
  end
| refute(test("[[:alpha:]]"); "letters not permitted")
| refute(test("[^[:digit:]]"); "punctuations not permitted")
| refute(startswith("0"); "area code cannot start with zero")
| refute(startswith("1"); "area code cannot start with one")
| refute(test("^...0"); "exchange code cannot start with zero")
| refute(test("^...1"); "exchange code cannot start with one")
'''


class CheckError(Exception):
    """Raised when test extraction or runtime validation fails."""


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
        run_match = re.search(
            r"(?m)^[ \t]*run jq (-[rc]) -f "
            + re.escape(solution_name)
            + r"[^\n]*<< 'END_INPUT'[ \t]*$",
            body,
        )
        input_match = re.search(
            r"(?ms)^[ \t]*run jq -[rc] -f [^\n]+<< 'END_INPUT'[ \t]*\n"
            r"(.*?)^[ \t]*END_INPUT[ \t]*$",
            body,
        )
        expected_match = re.search(r"(?m)^[ \t]*expected=(.+?)\s*$", body)
        if not run_match or not input_match or not expected_match:
            raise CheckError(f"Could not parse Bats case {declaration.group(2)!r}")
        expected_tokens = shlex.split(expected_match.group(1))
        if len(expected_tokens) != 1:
            raise CheckError(
                f"Unsupported expected output in {declaration.group(2)!r}"
            )
        expected_failure = "assert_failure" in body
        if not expected_failure and "assert_success" not in body:
            raise CheckError(f"Missing success/failure assertion: {declaration.group(2)}")
        if 'assert_equal "$output" "$expected"' not in body:
            raise CheckError(f"Missing output assertion: {declaration.group(2)}")
        cases.append(
            {
                "name": declaration.group(2),
                "input": json.loads(input_match.group(1)),
                "expected": expected_tokens[0],
                "expected_failure": expected_failure,
                "jq_flag": run_match.group(1),
            }
        )
    return cases


def solution_hashes(paths):
    return {
        path.relative_to(ROOT).as_posix(): hashlib.sha256(
            path.read_bytes()
        ).hexdigest()
        for path in paths
    }


def run_case(source, solution_name, case, label):
    with tempfile.TemporaryDirectory(prefix=f"phone-number-{label}-") as temp:
        implementation = Path(temp) / solution_name
        implementation.parent.mkdir(parents=True, exist_ok=True)
        implementation.write_text(source, encoding="utf-8")
        result = subprocess.run(
            ["jq", case["jq_flag"], "-f", solution_name],
            cwd=implementation.parent,
            input=json.dumps(case["input"]),
            check=False,
            capture_output=True,
            text=True,
        )
    output = (result.stdout if result.returncode == 0 else result.stderr).rstrip("\n")
    return {
        "return_code": result.returncode,
        "expected_failure": case["expected_failure"],
        "actual_output": output,
        "stderr": result.stderr,
        "stdout": result.stdout,
        "passed": (
            (
                result.returncode != 0
                if case["expected_failure"]
                else result.returncode == 0
            )
            and output == case["expected"]
        ),
    }


def tap_report(stdout, stderr, expected_cases):
    output = stdout + stderr
    plans = re.findall(r"(?m)^1\.\.(\d+)\s*$", output)
    rows = re.findall(r"(?mi)^(ok|not ok)\s+\d+\s*(.*)$", output)
    skipped = [
        row
        for row in rows
        if re.search(r"#\s*skip(?:\s|$)", row[1], re.IGNORECASE)
    ]
    failed = [row for row in rows if row[0].lower() == "not ok"]
    plan = int(plans[0]) if len(plans) == 1 else None
    names = [re.sub(r"\s+#.*$", "", row[1]).strip() for row in rows]
    return {
        "plan_count": plan,
        "plan_entries": len(plans),
        "reported_test_count": len(rows),
        "executed_test_count": len(rows) - len(skipped),
        "skipped_test_count": len(skipped),
        "assertion_failure_count": len(failed),
        "failed_test_names": [
            re.sub(r"\s+#.*$", "", row[1]).strip() for row in failed
        ],
        "test_names": names,
        "checks": {
            "single_tap_plan": len(plans) == 1,
            "plan_matches_results": plan == len(rows),
            "reported_count_matches": len(rows) == expected_cases,
            "nonzero_test_count": len(rows) - len(skipped) > 0,
            "all_cases_executed": len(rows) - len(skipped) == expected_cases,
            "no_skips": not skipped,
            "no_assertion_failures": not failed,
        },
    }


def run_validator(files, reference_path, implementation_text, expected_cases, label):
    solution_path = files["solution"][0]
    with tempfile.TemporaryDirectory(prefix=f"phone-number-validate-{label}-") as temp:
        temporary_root = Path(temp)
        copied_exercise = temporary_root / EXERCISE_REL
        shutil.copytree(EXERCISE, copied_exercise)
        (copied_exercise / reference_path.relative_to(EXERCISE)).write_text(
            implementation_text, encoding="utf-8"
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
    report = tap_report(child.stdout, child.stderr, expected_cases)
    checks = report["checks"]
    checks["child_return_code_zero"] = child.returncode == 0
    report.update(
        {
            "label": label,
            "command": ["bin/validate_one_exercise", str(EXERCISE_REL)],
            "return_code": child.returncode,
            "stdout": child.stdout,
            "stderr": child.stderr,
            "temporary_copy_cleaned": not temporary_root.exists(),
            "passed": child.returncode == 0 and all(checks.values()),
        }
    )
    return report


def main():
    evidence = {
        "exercise": EXERCISE_REL.as_posix(),
        "tool_versions": {},
        "cases": [],
        "implementations": {},
        "comparisons": [],
        "validators": {},
        "learner_solution_hashes": {},
        "failures": [],
    }
    solution_paths = []
    hashes_before = {}
    failures = []
    try:
        config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        files = configured_files(config)
        solution_paths = files["solution"]
        hashes_before = solution_hashes(solution_paths)
        solution_name = solution_paths[0].relative_to(EXERCISE).as_posix()
        test_path = files["test"][0]
        reference_path = (files.get("example") or files.get("exemplar"))[0]
        reference_text = reference_path.read_text(encoding="utf-8")
        cases = read_cases(test_path, solution_name)
        alternative = ALTERNATIVE.strip() + "\n"
        evidence["cases"] = cases
        evidence["tool_versions"] = {
            "python": sys.version.split()[0],
            "jq": get_version(["jq", "--version"]),
            "bats": get_version(["bats", "--version"]),
            "bash": get_version(["bash", "--version"]),
        }
        evidence["implementations"] = {
            "reference": {
                "path": reference_path.relative_to(ROOT).as_posix(),
                "main_operation": 'gsub("[() +.-]"; "")',
                "input_copy_only": True,
            },
            "alternative": {
                "approach": "explode code points, reduce into normalized text, then apply identical validations",
                "source": alternative,
                "input_copy_only": True,
            },
        }

        named_found = {case["name"] for case in cases}
        missing_named = NAMED_CASES - named_found
        if missing_named:
            failures.append("Missing named cases: " + ", ".join(sorted(missing_named)))
        for case in cases:
            original = run_case(reference_text, solution_name, case, "reference")
            alternate = run_case(alternative, solution_name, case, "alternative")
            same_outcome = (
                original["return_code"] == alternate["return_code"]
                and original["actual_output"] == alternate["actual_output"]
            )
            comparison = {
                "name": case["name"],
                "input": case["input"],
                "expected": case["expected"],
                "expected_failure": case["expected_failure"],
                "reference": original,
                "alternative": alternate,
                "same_behavior": same_outcome,
                "passed_by_both": original["passed"] and alternate["passed"],
            }
            evidence["comparisons"].append(comparison)
            if not comparison["passed_by_both"]:
                failures.append(f"Case assertion failed: {case['name']}")
            if not same_outcome:
                failures.append(f"Implementations disagree: {case['name']}")

        worked_example = {
            "input": {"phrase": "223.456   7890"},
            "expected": "2234567890",
        }
        reference_worked = run_case(
            reference_text,
            solution_name,
            {
                **worked_example,
                "name": "worked trade-off example",
                "expected_failure": False,
                "jq_flag": "-r",
            },
            "reference-example",
        )
        alternative_worked = run_case(
            alternative,
            solution_name,
            {
                **worked_example,
                "name": "worked trade-off example",
                "expected_failure": False,
                "jq_flag": "-r",
            },
            "alternative-example",
        )
        evidence["worked_example"] = {
            **worked_example,
            "reference": reference_worked,
            "alternative": alternative_worked,
            "passed": reference_worked["passed"] and alternative_worked["passed"],
        }
        if not evidence["worked_example"]["passed"]:
            failures.append("Worked example failed")

        reference_validator = run_validator(
            files,
            reference_path,
            reference_text,
            len(cases),
            "reference",
        )
        alternative_validator = run_validator(
            files,
            reference_path,
            alternative,
            len(cases),
            "alternative",
        )
        evidence["validators"] = {
            "reference": reference_validator,
            "alternative": alternative_validator,
        }
        if not reference_validator["passed"]:
            failures.append("Reference validator failed its TAP/assertion checks")
        if not alternative_validator["passed"]:
            failures.append("Alternative validator failed its TAP/assertion checks")
    except (OSError, KeyError, ValueError, CheckError, json.JSONDecodeError) as error:
        evidence["error"] = str(error)
        failures.append(str(error))
    finally:
        try:
            hashes_after = solution_hashes(solution_paths) if solution_paths else {}
        except OSError as error:
            hashes_after = {}
            failures.append(f"Could not hash learner solution after check: {error}")
        evidence["learner_solution_hashes"] = {
            "before": hashes_before,
            "after": hashes_after,
            "unchanged": bool(hashes_before) and hashes_before == hashes_after,
        }
        if not evidence["learner_solution_hashes"]["unchanged"]:
            failures.append("Learner solution files changed during checking")
        evidence["failures"] = failures
        evidence["passed"] = not failures
        EVIDENCE_PATH.write_text(
            json.dumps(evidence, indent=2) + "\n", encoding="utf-8"
        )

    print(f"Evidence: {EVIDENCE_PATH.relative_to(ROOT)}")
    for comparison in evidence["comparisons"]:
        print(
            f"{comparison['name']}: "
            f"reference={comparison['reference']['actual_output']!r} "
            f"alternative={comparison['alternative']['actual_output']!r} "
            f"same={comparison['same_behavior']}"
        )
    for name, result in evidence["validators"].items():
        print(
            f"{name}: executed={result['executed_test_count']} "
            f"skipped={result['skipped_test_count']} "
            f"failed={result['assertion_failure_count']} "
            f"rc={result['return_code']}"
        )
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        return 1
    print("Both implementations passed every enabled phone-number case.")
    print("Learner solution files remain unchanged.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
