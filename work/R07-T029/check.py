#!/usr/bin/env python3
"""Check the diamond reference and verify failure handling in isolated copies."""

import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EXERCISE_REL = Path("exercises/practice/diamond")
EXERCISE = ROOT / EXERCISE_REL
CONFIG_PATH = EXERCISE / ".meta/config.json"
EVIDENCE_PATH = Path(__file__).resolve().parent / "evidence.json"


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


def learner_hashes(solution_paths):
    return {
        str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in solution_paths
    }


def tracked_run(command, cwd, evidence, label, input_text=None):
    run_record = {
        "label": label,
        "command": [str(part) for part in command],
        "learner_hashes_before": learner_hashes(evidence["_solution_paths"]),
    }
    evidence["subprocess_runs"].append(run_record)
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            input=input_text,
            check=False,
            capture_output=True,
            text=True,
        )
        run_record.update(
            {
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }
        )
        return result
    except KeyboardInterrupt:
        run_record["interrupted"] = True
        raise
    finally:
        run_record["learner_hashes_after"] = learner_hashes(
            evidence["_solution_paths"]
        )
        run_record["learner_hashes_unchanged"] = (
            run_record["learner_hashes_before"]
            == run_record["learner_hashes_after"]
        )
        if not run_record["learner_hashes_unchanged"]:
            evidence["integrity_failures"].append(
                f"Learner solution changed during {label}"
            )


def read_test_cases(test_source, solution_name):
    starts = list(
        re.finditer(r"""(?m)^@test\s+(["'])(.*?)\1\s*\{""", test_source)
    )
    if not starts:
        raise ValueError("No Bats test cases found")

    cases = []
    for index, match in enumerate(starts):
        body_end = starts[index + 1].start() if index + 1 < len(starts) else len(test_source)
        body = test_source[match.end() : body_end]
        input_match = re.search(
            r"(?ms)^[ \t]*run jq -r -f "
            + re.escape(solution_name)
            + r"[^\n]*<< 'END_INPUT'[ \t]*\n"
            r"(.*?)^[ \t]*END_INPUT[ \t]*$",
            body,
        )
        expected_match = re.search(
            r"(?ms)^[ \t]*expected=\$\(cat << END_EXPECTED[ \t]*\n"
            r"(.*?)^[ \t]*END_EXPECTED[ \t]*\n[ \t]*\)",
            body,
        )
        if not input_match or not expected_match:
            raise ValueError(
                f"Could not read test input/expected output: {match.group(2)}"
            )
        if (
            "assert_success" not in body
            or 'assert_equal "$output" "$expected"' not in body
        ):
            raise ValueError(f"Missing expected assertions: {match.group(2)}")
        cases.append(
            {
                "name": match.group(2),
                "input": json.loads(input_match.group(1)),
                "expected": expected_match.group(1).rstrip("\n"),
            }
        )
    return cases


def tap_summary(output, expected_names):
    plan_matches = re.findall(r"(?m)^1\.\.(\d+)\s*$", output)
    result_lines = re.findall(
        r"(?mi)^(ok|not ok)\s+(\d+)(?:\s+(.*))?$", output
    )
    skipped = [
        line
        for line in result_lines
        if re.search(r"#\s*skip(?:\s|$)", line[2] or "", re.IGNORECASE)
    ]
    failed = [line for line in result_lines if line[0].lower() == "not ok"]
    executed = len(result_lines) - len(skipped)
    test_names = [(line[2] or "").split(" #", 1)[0] for line in result_lines]
    missing_names = sorted(set(expected_names) - set(test_names))
    reasons = []
    if len(plan_matches) != 1:
        reasons.append("expected exactly one TAP test plan")
        plan = None
    else:
        plan = int(plan_matches[0])
        if plan != len(result_lines):
            reasons.append(
                f"TAP plan says {plan}, but {len(result_lines)} result lines were found"
            )
    if executed == 0:
        reasons.append("zero tests executed")
    if failed:
        reasons.append(f"{len(failed)} Bats assertion(s) failed")
    if missing_names:
        reasons.append("test results missing: " + ", ".join(missing_names))
    return {
        "planned_tests": plan,
        "reported_test_results": len(result_lines),
        "executed_tests": executed,
        "skipped_tests": len(skipped),
        "failed_tests": len(failed),
        "missing_test_names": missing_names,
        "reasons": reasons,
    }


def validate_in_copy(
    evidence,
    solution_name,
    tests_name,
    example_name,
    reference_bytes,
    cases,
    label,
    empty_selection=False,
):
    with tempfile.TemporaryDirectory(prefix=f"diamond-{label}-") as temp:
        scratch_root = Path(temp)
        scratch_exercise = scratch_root / EXERCISE_REL
        shutil.copytree(EXERCISE, scratch_exercise)
        (scratch_root / "bin").mkdir()
        shutil.copy2(
            ROOT / "bin/validate_one_exercise",
            scratch_root / "bin/validate_one_exercise",
        )

        solution_copy = scratch_exercise / solution_name
        solution_copy.write_bytes(reference_bytes)
        (scratch_exercise / example_name).write_bytes(reference_bytes)

        if empty_selection:
            tests_copy = scratch_exercise / tests_name
            tests_source = tests_copy.read_text()
            tests_source, replaced = re.subn(
                r"(?m)^(@test\b[^\n]*\{\s*)$",
                r'\1\n    skip "forced empty test selection"',
                tests_source,
            )
            if replaced != len(cases):
                raise ValueError(
                    f"Expected to disable {len(cases)} tests; disabled {replaced}"
                )
            tests_copy.write_text(tests_source)

        run = tracked_run(
            ["bin/validate_one_exercise", str(EXERCISE_REL)],
            scratch_root,
            evidence,
            f"{label} validator",
        )
    summary = tap_summary(
        run.stdout + run.stderr,
        [case["name"] for case in cases],
    )
    summary.update(
        {
            "return_code": run.returncode,
            "stdout": run.stdout,
            "stderr": run.stderr,
            "success": run.returncode == 0 and not summary["reasons"],
        }
    )
    summary["checker_exit_status"] = 0 if summary["success"] else 1
    summary["temporary_directory_cleaned"] = not scratch_root.exists()
    if run.returncode:
        summary["reasons"].insert(
            0, f"validator exited with status {run.returncode}"
        )
    evidence["validation_runs"][label] = summary
    return summary


def save_evidence(evidence):
    evidence.pop("_solution_paths", None)
    EVIDENCE_PATH.write_text(json.dumps(evidence, indent=2) + "\n")


def main():
    evidence = {
        "exercise": str(EXERCISE_REL),
        "tool_versions": {},
        "cases": [],
        "subprocess_runs": [],
        "validation_runs": {},
        "failures": [],
        "integrity_failures": [],
        "learner_hashes_final": {},
    }
    solution_paths = []
    evidence["_solution_paths"] = solution_paths
    status = 0

    try:
        config = json.loads(CONFIG_PATH.read_text())
        solution_names = config["files"]["solution"]
        if not solution_names:
            raise ValueError("No learner solution files configured")
        solution_paths.extend(EXERCISE / name for name in solution_names)
        solution_name = configured_file(config, "solution")
        tests_name = configured_file(config, "test")
        example_name = configured_file(config, "example", "exemplar")
        example_path = EXERCISE / example_name
        tests_path = EXERCISE / tests_name
        for path in [*solution_paths, example_path, tests_path]:
            if not path.is_file():
                raise FileNotFoundError(f"Configured exercise file missing: {path}")

        evidence["learner_hashes_initial"] = learner_hashes(solution_paths)
        evidence["tool_versions"] = {
            "python": sys.version.split()[0],
            "jq": run_version(["jq", "--version"]),
            "bats": run_version(["bats", "--version"]),
            "bash": run_version(["bash", "--version"]),
        }
        reference_bytes = example_path.read_bytes()
        cases = read_test_cases(tests_path.read_text(), solution_name)
        evidence["cases"] = cases
        evidence["case_runs"] = []

        with tempfile.TemporaryDirectory(prefix="diamond-cases-") as temp:
            scratch_exercise = Path(temp) / EXERCISE_REL
            shutil.copytree(EXERCISE, scratch_exercise)
            (scratch_exercise / solution_name).write_bytes(reference_bytes)
            for case in cases:
                run = tracked_run(
                    ["jq", "-r", "-f", solution_name],
                    scratch_exercise,
                    evidence,
                    f"reference case: {case['name']}",
                    json.dumps(case["input"]),
                )
                actual = run.stdout[:-1] if run.stdout.endswith("\n") else run.stdout
                case_result = {
                    "name": case["name"],
                    "input": case["input"],
                    "expected": case["expected"],
                    "actual": actual,
                    "return_code": run.returncode,
                    "stderr": run.stderr,
                    "passed": run.returncode == 0 and actual == case["expected"],
                }
                evidence["case_runs"].append(case_result)
                if not case_result["passed"]:
                    evidence["failures"].append(
                        f"Reference output assertion failed: {case['name']}"
                    )

        real = validate_in_copy(
            evidence,
            solution_name,
            tests_name,
            example_name,
            reference_bytes,
            cases,
            "real-reference",
        )
        if not real["success"]:
            evidence["failures"].append(
                "Real reference validator failed: " + "; ".join(real["reasons"])
            )
        if real["executed_tests"] != len(cases):
            evidence["failures"].append(
                f"Expected {len(cases)} executed reference tests, "
                f"got {real['executed_tests']}"
            )
        if real["checker_exit_status"] != 0:
            evidence["failures"].append(
                "Successful real-reference run did not produce checker status 0"
            )

        failing_reference = b"error(\"deliberate checker failure\")\n"
        failing = validate_in_copy(
            evidence,
            solution_name,
            tests_name,
            example_name,
            failing_reference,
            cases,
            "failing-reference",
        )
        if (
            failing["return_code"] == 0
            or failing["failed_tests"] == 0
            or failing["checker_exit_status"] != 1
        ):
            evidence["failures"].append(
                "Deliberately failing reference did not produce assertion failure"
            )

        empty = validate_in_copy(
            evidence,
            solution_name,
            tests_name,
            example_name,
            reference_bytes,
            cases,
            "empty-selection",
            empty_selection=True,
        )
        if (
            empty["executed_tests"] != 0
            or empty["return_code"] != 0
            or empty["success"]
            or empty["checker_exit_status"] != 1
        ):
            evidence["failures"].append(
                "Empty test selection was not rejected as a zero-test run"
            )

        if evidence["failures"]:
            status = 1
    except KeyboardInterrupt:
        evidence["interrupted"] = True
        status = 130
    except (OSError, KeyError, ValueError, RuntimeError, json.JSONDecodeError) as error:
        evidence["error"] = str(error)
        print(f"FAIL: {error}", file=sys.stderr)
        status = 1
    finally:
        try:
            if solution_paths:
                evidence["learner_hashes_final"] = learner_hashes(solution_paths)
                if (
                    evidence.get("learner_hashes_initial")
                    and evidence["learner_hashes_initial"]
                    != evidence["learner_hashes_final"]
                ):
                    evidence["integrity_failures"].append(
                        "Learner solution hashes changed during checker run"
                    )
                    status = 1
        except OSError as error:
            evidence["error"] = f"Could not hash learner files after run: {error}"
            status = 1
        if evidence["integrity_failures"]:
            status = 1
        save_evidence(evidence)

    for result in evidence.get("case_runs", []):
        print(
            f"{result['name']}: "
            f"{'PASS' if result['passed'] else 'FAIL'} "
            f"(jq rc={result['return_code']})"
        )
    for label, result in evidence["validation_runs"].items():
        print(
            f"{label}: executed={result['executed_tests']} "
            f"skipped={result['skipped_tests']} "
            f"failed={result['failed_tests']} rc={result['return_code']}"
        )
        if result["reasons"]:
            print("  " + "; ".join(result["reasons"]))
    print(f"Evidence: {EVIDENCE_PATH.relative_to(ROOT)}")
    print(f"Learner hashes unchanged: {not evidence['integrity_failures']}")
    if status:
        print("FAIL: one or more diamond checker assertions failed.", file=sys.stderr)
        for failure in evidence["failures"] + evidence["integrity_failures"]:
            print(f"  {failure}", file=sys.stderr)
    else:
        print("All diamond reference, failure, and zero-test checks passed.")
    return status


if __name__ == "__main__":
    sys.exit(main())
