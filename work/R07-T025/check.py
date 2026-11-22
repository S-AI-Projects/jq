#!/usr/bin/env python3

"""Validate isogram's reference and record a small, reproducible cost sample."""

import hashlib
import json
import pathlib
import platform
import re
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone


ROOT = pathlib.Path(__file__).resolve().parents[2]
TASK_DIR = pathlib.Path(__file__).resolve().parent
EXERCISE_REL = pathlib.Path("exercises/practice/isogram")
REPETITIONS = 5
INPUT_SIZES = (16, 256, 4096)
ALPHABET = "abcdefghijklmnopqrstuvwxyz"
ANCHOR_CASES = (
    "empty string",
    "isogram with only lower case characters",
    "word with one duplicated character",
)


def run(command, cwd, input_text=None):
    try:
        result = subprocess.run(
            command,
            cwd=str(cwd),
            input=input_text,
            text=True,
            capture_output=True,
            check=False,
        )
    except OSError as error:
        return {
            "command": command,
            "returncode": None,
            "stdout": "",
            "stderr": str(error),
        }
    return {
        "command": command,
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def make_phrase(size):
    return (ALPHABET * ((size + len(ALPHABET) - 1) // len(ALPHABET)))[:size]


def is_isogram(phrase):
    letters = [character.lower() for character in phrase if "a" <= character.lower() <= "z"]
    return len(letters) == len(set(letters))


def tap_test_names(contents):
    names = []
    for line in contents.splitlines():
        match = re.match(r"^@test (.+) \{$", line)
        if match:
            name = match.group(1)
            if name.startswith("'") and name.endswith("'"):
                name = name[1:-1]
            names.append(name)
    return names


def main():
    failures = []
    evidence = {
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "environment": {
            "platform": platform.platform(),
            "python": sys.version.split()[0],
            "timing_clock": "time.perf_counter_ns",
            "timing_repetitions_per_size": REPETITIONS,
            "timing_scope": (
                "Wall time for each jq subprocess invocation, including process "
                "startup and filter parsing; no separate compilation step."
            ),
        },
        "validation": {},
        "benchmarks": [],
        "failures": failures,
    }

    def check(condition, message):
        if not condition:
            failures.append(message)

    exercise = ROOT / EXERCISE_REL
    config = json.loads((exercise / ".meta/config.json").read_text())
    solution_rel = pathlib.Path(config["files"]["solution"][0])
    test_rel = pathlib.Path(config["files"]["test"][0])
    example_rel = pathlib.Path(config["files"]["example"][0])
    learner_solution = exercise / solution_rel
    learner_hash_before = hashlib.sha256(learner_solution.read_bytes()).hexdigest()

    versions = {}
    version_commands = {
        "jq": ["jq", "--version"],
        "bats": ["bats", "--version"],
        "bash": ["bash", "--version"],
    }
    for tool, command in version_commands.items():
        result = run(command, ROOT)
        check(result["returncode"] == 0, "{} version command failed".format(tool))
        versions[tool] = (result["stdout"] or result["stderr"]).splitlines()[0]
    evidence["environment"]["tool_versions"] = versions

    original_tests = (exercise / test_rel).read_text()
    test_names = tap_test_names(original_tests)
    check(bool(test_names), "The maintained Bats file has no discovered tests")
    check(len(test_names) == len(set(test_names)), "Bats test names are not unique")
    for case_name in ANCHOR_CASES:
        check(case_name in test_names, "Missing required case: {}".format(case_name))
    evidence["validation"]["test_file"] = (EXERCISE_REL / test_rel).as_posix()
    evidence["validation"]["expected_test_names"] = test_names
    evidence["validation"]["expected_case_count"] = len(test_names)

    with tempfile.TemporaryDirectory(prefix="r07-t025-") as temp_name:
        temp_root = pathlib.Path(temp_name)
        scratch_exercise = temp_root / EXERCISE_REL
        shutil.copytree(str(exercise), str(scratch_exercise))
        (temp_root / "bin").mkdir()
        shutil.copy2(
            str(ROOT / "bin/validate_one_exercise"),
            str(temp_root / "bin/validate_one_exercise"),
        )

        # Substitute the reference only in this copied exercise.
        shutil.copyfile(
            str(scratch_exercise / example_rel),
            str(scratch_exercise / solution_rel),
        )
        validator = run(
            ["bin/validate_one_exercise", EXERCISE_REL.as_posix()],
            temp_root,
        )
        validator_stdout = validator["stdout"]
        passing = re.findall(r"(?m)^ok \d+(?: .*)?$", validator_stdout)
        failed = re.findall(r"(?m)^not ok \d+.*$", validator_stdout)
        plans = re.findall(r"(?m)^1\.\.(\d+)\s*$", validator_stdout)
        reported_names = [
            re.sub(r"^ok \d+ ", "", line) for line in passing
        ]
        evidence["validation"].update(
            {
                "command": validator["command"],
                "returncode": validator["returncode"],
                "tap_plans": [int(plan) for plan in plans],
                "executed_count": len(passing),
                "passed_names": reported_names,
                "failed_lines": failed,
                "stdout": validator_stdout,
                "stderr": validator["stderr"],
            }
        )
        check(
            validator["returncode"] == 0,
            "Reference validator exited with {}".format(validator["returncode"]),
        )
        check(bool(plans), "Reference validator did not emit a TAP test plan")
        check(len(passing) > 0, "Reference validator executed zero passing tests")
        check(
            len(passing) == len(test_names),
            "Reference validator passed {} cases; expected {}".format(
                len(passing), len(test_names)
            ),
        )
        check(
            plans == [str(len(test_names))],
            "Reference TAP plan {} does not match {} cases".format(
                plans, len(test_names)
            ),
        )
        check(not failed, "Reference validator emitted failed tests: {}".format(failed))
        check(
            reported_names == test_names,
            "Executed Bats test names differ from the maintained suite",
        )

        jq_command = ["jq", "-r", "-f", solution_rel.as_posix()]
        for size in INPUT_SIZES:
            phrase = make_phrase(size)
            expected = is_isogram(phrase)
            payload = json.dumps({"phrase": phrase}, separators=(",", ":"))
            correctness = run(jq_command, scratch_exercise, payload)
            actual = correctness["stdout"].strip()
            correctness_passed = (
                correctness["returncode"] == 0
                and actual == str(expected).lower()
            )
            check(
                correctness_passed,
                "Correctness check failed for {} symbols: expected {}, got {!r}".format(
                    size, expected, actual
                ),
            )
            if not correctness_passed:
                evidence["benchmarks"].append(
                    {
                        "input_symbols": size,
                        "input": {"phrase": phrase},
                        "expected": expected,
                        "correctness_actual": actual,
                        "correctness_returncode": correctness["returncode"],
                        "correctness_stderr": correctness["stderr"],
                        "correctness_passed": False,
                        "timing_skipped": True,
                        "repetitions": 0,
                    }
                )
                continue

            samples = []
            timed_outputs = []
            for repetition in range(1, REPETITIONS + 1):
                start = time.perf_counter_ns()
                timed = run(jq_command, scratch_exercise, payload)
                elapsed = time.perf_counter_ns() - start
                timed_actual = timed["stdout"].strip()
                check(
                    timed["returncode"] == 0
                    and timed_actual == str(expected).lower(),
                    "Timed run {} failed for {} symbols".format(repetition, size),
                )
                samples.append(elapsed / 1_000_000)
                timed_outputs.append(timed_actual)

            evidence["benchmarks"].append(
                {
                    "input_symbols": size,
                    "input": {"phrase": phrase},
                    "expected": expected,
                    "correctness_actual": actual,
                    "correctness_passed": correctness_passed,
                    "timed_actual_outputs": timed_outputs,
                    "repetitions": REPETITIONS,
                    "elapsed_milliseconds": samples,
                    "median_elapsed_milliseconds": statistics.median(samples),
                    "includes_process_startup": True,
                    "algorithm_only_timing": False,
                }
            )

    learner_hash_after = hashlib.sha256(learner_solution.read_bytes()).hexdigest()
    evidence["learner_solution"] = {
        "path": (EXERCISE_REL / solution_rel).as_posix(),
        "sha256_before": learner_hash_before,
        "sha256_after": learner_hash_after,
        "unchanged": learner_hash_before == learner_hash_after,
    }
    check(learner_hash_before == learner_hash_after, "Learner solution was modified")
    evidence["failures"] = failures

    evidence_path = TASK_DIR / "evidence.json"
    evidence_path.write_text(json.dumps(evidence, indent=2) + "\n")
    print(
        "Reference validation: {} of {} tests passed.".format(
            evidence["validation"].get("executed_count", 0), len(test_names)
        )
    )
    for result in evidence["benchmarks"]:
        print(
            "{} symbols: median {:.3f} ms ({} subprocess repetitions).".format(
                result["input_symbols"],
                result["median_elapsed_milliseconds"],
                result["repetitions"],
            )
        )
    print("Evidence: {}".format(evidence_path.relative_to(ROOT)))
    if failures:
        for failure in failures:
            print("FAIL: {}".format(failure), file=sys.stderr)
        return 1
    print("All checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
