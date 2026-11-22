#!/usr/bin/env python3

"""Check leap-year reference cases and the documented jq alternative examples."""

import hashlib
import json
import pathlib
import platform
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone


ROOT = pathlib.Path(__file__).resolve().parents[2]
TASK_DIR = pathlib.Path(__file__).resolve().parent
EXERCISE_REL = pathlib.Path("exercises/practice/leap")
MICRO_EXAMPLES = (
    {
        "name": "null and false both select the alternative",
        "program": (
            "[({year: null} | (.year // 2024)), "
            "({year: false} | (.year // 2024))]"
        ),
        "expected": "[2024,2024]",
    },
    {
        "name": "false differs from null but still selects the alternative",
        "program": (
            "[({year: false} | (.year == null)), "
            "({year: false} | (.year // 0))]"
        ),
        "expected": "[false,0]",
    },
)
REQUIRED_CASES = (
    "year not divisible by 4 in common year",
    "year divisible by 2, not divisible by 4 in common year",
    "year divisible by 4, not divisible by 100 in leap year",
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


def get_test_names(contents):
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
        "platform": platform.platform(),
        "python": sys.version.split()[0],
        "exercise_validation": {},
        "micro_examples": [],
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
    for tool, command in (
        ("jq", ["jq", "--version"]),
        ("bats", ["bats", "--version"]),
        ("bash", ["bash", "--version"]),
    ):
        result = run(command, ROOT)
        check(result["returncode"] == 0, "{} version command failed".format(tool))
        versions[tool] = (result["stdout"] or result["stderr"]).splitlines()[0]
    evidence["tool_versions"] = versions

    test_contents = (exercise / test_rel).read_text()
    expected_names = get_test_names(test_contents)
    check(bool(expected_names), "The maintained Bats suite contains zero tests")
    check(
        len(expected_names) == len(set(expected_names)),
        "The maintained Bats suite contains duplicate test names",
    )
    for required in REQUIRED_CASES:
        check(required in expected_names, "Missing required case {!r}".format(required))
    evidence["exercise_validation"]["expected_count"] = len(expected_names)
    evidence["exercise_validation"]["expected_case_names"] = expected_names

    with tempfile.TemporaryDirectory(prefix="r07-t027-") as temp_name:
        temp_root = pathlib.Path(temp_name)
        scratch_exercise = temp_root / EXERCISE_REL
        shutil.copytree(str(exercise), str(scratch_exercise))
        validator_dir = temp_root / "bin"
        validator_dir.mkdir()
        shutil.copy2(
            str(ROOT / "bin/validate_one_exercise"),
            str(validator_dir / "validate_one_exercise"),
        )

        # Install the maintained reference only in this copy.
        shutil.copyfile(
            str(scratch_exercise / example_rel),
            str(scratch_exercise / solution_rel),
        )
        validation = run(
            ["bin/validate_one_exercise", EXERCISE_REL.as_posix()],
            temp_root,
        )
        passed_lines = re.findall(r"(?m)^ok \d+(?: .*)?$", validation["stdout"])
        failed_lines = re.findall(
            r"(?m)^not ok \d+.*$", validation["stdout"]
        )
        plans = re.findall(r"(?m)^1\.\.(\d+)\s*$", validation["stdout"])
        actual_names = [re.sub(r"^ok \d+ ", "", line) for line in passed_lines]
        evidence["exercise_validation"].update(
            {
                "command": validation["command"],
                "returncode": validation["returncode"],
                "tap_plans": [int(plan) for plan in plans],
                "executed_count": len(passed_lines),
                "passed_case_names": actual_names,
                "failed_lines": failed_lines,
                "stdout": validation["stdout"],
                "stderr": validation["stderr"],
            }
        )
        check(
            validation["returncode"] == 0,
            "Exercise validator exited with {}".format(validation["returncode"]),
        )
        check(bool(plans), "Exercise validator emitted no TAP plan")
        check(len(passed_lines) > 0, "Exercise validator executed zero tests")
        check(
            len(passed_lines) == len(expected_names),
            "Reference passed {} cases; expected {}".format(
                len(passed_lines), len(expected_names)
            ),
        )
        check(
            plans == [str(len(expected_names))],
            "TAP plan {} does not match {} expected tests".format(
                plans, len(expected_names)
            ),
        )
        check(not failed_lines, "Reference had failing cases: {}".format(failed_lines))
        check(
            actual_names == expected_names,
            "Executed test names differ from the maintained suite",
        )

        for example in MICRO_EXAMPLES:
            result = run(["jq", "-cn", example["program"]], scratch_exercise)
            actual = result["stdout"].strip()
            passed = result["returncode"] == 0 and actual == example["expected"]
            evidence["micro_examples"].append(
                {
                    "name": example["name"],
                    "program": example["program"],
                    "expected": example["expected"],
                    "actual": actual,
                    "returncode": result["returncode"],
                    "stderr": result["stderr"],
                    "passed": passed,
                }
            )
            check(
                passed,
                "Micro-example {!r} expected {}, got {!r}".format(
                    example["name"], example["expected"], actual
                ),
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
            evidence["exercise_validation"].get("executed_count", 0),
            len(expected_names),
        )
    )
    for example in evidence["micro_examples"]:
        print(
            "{}: {} (expected {}).".format(
                example["name"], example["actual"], example["expected"]
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
