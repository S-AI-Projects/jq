#!/usr/bin/env python3
"""Verify eliuds-eggs examples against its reference in a temporary copy."""

import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import textwrap


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
EXERCISE_REL = pathlib.Path("exercises/practice/eliuds-eggs")
EXERCISE_DIR = REPO_ROOT / EXERCISE_REL
WORK_DIR = pathlib.Path(__file__).resolve().parent

EXPECTED_CASES = [
    {"name": "0 eggs", "input": {"number": 0}, "expected": 0},
    {"name": "1 egg", "input": {"number": 16}, "expected": 1},
    {"name": "4 eggs", "input": {"number": 89}, "expected": 4},
    {"name": "13 eggs", "input": {"number": 2_000_000_000}, "expected": 13},
]


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def first_line(command: list[str]) -> str:
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode:
        raise RuntimeError(
            f"{' '.join(command)} failed ({result.returncode}): {result.stderr.strip()}"
        )
    output = result.stdout or result.stderr
    return output.strip().splitlines()[0]


def tool_versions() -> dict[str, str]:
    grep = shutil.which("ggrep") or shutil.which("grep")
    if grep is None:
        raise RuntimeError("grep is required")
    return {
        "jq": first_line(["jq", "--version"]),
        "bats": first_line(["bats", "--version"]),
        "bash": first_line(["bash", "--version"]),
        "grep": first_line([grep, "--version"]),
        "grep_executable": grep,
        "python": sys.version.split()[0],
    }


def configured_path(config: dict, key: str) -> pathlib.Path:
    paths = config["files"][key]
    if not paths:
        raise ValueError(f"config.json has no files.{key} entry")
    return pathlib.Path(paths[0])


def extract_cases(test_file: pathlib.Path) -> list[dict]:
    contents = test_file.read_text(encoding="utf-8")
    blocks = re.findall(r"(?ms)^@test '([^']+)' \{\n(.*?)^\}", contents)
    cases = []
    for name, body in blocks:
        input_match = re.search(
            r"(?ms)^\s*run jq -r -f .*?<< 'END_INPUT'\n(.*?)\nEND_INPUT\s*$",
            body,
        )
        expected_match = re.search(r"(?m)^\s*expected=(\d+)\s*$", body)
        if input_match is None or expected_match is None:
            raise ValueError(f"Could not read input and expected result for {name!r}")
        cases.append(
            {
                "name": name,
                "input": json.loads(textwrap.dedent(input_match.group(1))),
                "expected": int(expected_match.group(1)),
            }
        )
    return cases


def write_json(path: pathlib.Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    versions = tool_versions()
    write_json(WORK_DIR / "tool_versions.json", versions)

    config_path = EXERCISE_DIR / ".meta/config.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    solution_rel = configured_path(config, "solution")
    test_rel = configured_path(config, "test")
    example_rel = configured_path(config, "example")
    cases = extract_cases(EXERCISE_DIR / test_rel)
    errors: list[str] = []

    require(cases == EXPECTED_CASES, "Bats inputs/results differ from the expected cases", errors)
    learner_solution = EXERCISE_DIR / solution_rel
    learner_contents = learner_solution.read_bytes()
    require(
        b"halt_error" in learner_contents,
        "Learner solution no longer contains its unsolved stub",
        errors,
    )

    results = []
    validator_result = None
    validator_summary = {}
    with tempfile.TemporaryDirectory(prefix="eliuds-eggs-check-") as tmp:
        temp_root = pathlib.Path(tmp)
        temp_exercise = temp_root / EXERCISE_REL
        shutil.copytree(EXERCISE_DIR, temp_exercise)
        shutil.copy2(
            temp_exercise / example_rel,
            temp_exercise / solution_rel,
        )
        temp_bin = temp_root / "bin"
        temp_bin.mkdir()
        shutil.copy2(REPO_ROOT / "bin/validate_one_exercise", temp_bin)

        reference = temp_exercise / example_rel
        for case in cases:
            proc = subprocess.run(
                ["jq", "-r", "-f", str(reference)],
                input=json.dumps(case["input"]),
                capture_output=True,
                text=True,
                check=False,
            )
            actual = proc.stdout.strip()
            passed = proc.returncode == 0 and actual == str(case["expected"])
            results.append(
                {
                    **case,
                    "actual": actual,
                    "returncode": proc.returncode,
                    "stderr": proc.stderr.strip(),
                    "passed": passed,
                }
            )
            require(
                proc.returncode == 0,
                f"{case['name']}: jq exited with {proc.returncode}: {proc.stderr.strip()}",
                errors,
            )
            require(
                actual == str(case["expected"]),
                f"{case['name']}: expected {case['expected']}, got {actual!r}",
                errors,
            )

        env = os.environ.copy()
        env["BATS_RUN_SKIPPED"] = "true"
        validator_result = subprocess.run(
            ["bin/validate_one_exercise", EXERCISE_REL.as_posix()],
            cwd=temp_root,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        output = validator_result.stdout + validator_result.stderr
        planned_match = re.search(r"(?m)^1\.\.(\d+)\s*$", output)
        statuses = re.findall(r"(?m)^(ok|not ok) \d+(?:\s|$)", output)
        skipped = re.findall(r"(?m)^ok \d+.*# skip", output)
        validator_summary = {
            "command": ["bin/validate_one_exercise", EXERCISE_REL.as_posix()],
            "returncode": validator_result.returncode,
            "planned_tests": int(planned_match.group(1)) if planned_match else None,
            "reported_test_results": len(statuses),
            "passed_tests": statuses.count("ok"),
            "failed_tests": statuses.count("not ok"),
            "skipped_tests": len(skipped),
            "stdout": validator_result.stdout,
            "stderr": validator_result.stderr,
        }

    require(
        learner_solution.read_bytes() == learner_contents,
        "Working-tree learner solution changed during the check",
        errors,
    )
    require(
        validator_result is not None and validator_result.returncode == 0,
        "bin/validate_one_exercise exited non-zero",
        errors,
    )
    require(
        validator_summary.get("planned_tests") == len(cases),
        f"Expected {len(cases)} planned Bats tests, got {validator_summary.get('planned_tests')}",
        errors,
    )
    require(
        validator_summary.get("reported_test_results") == len(cases),
        "Validator did not report every test case",
        errors,
    )
    require(
        validator_summary.get("passed_tests") == len(cases)
        and validator_summary.get("failed_tests") == 0
        and validator_summary.get("skipped_tests") == 0,
        "Validator did not pass all cases without skips",
        errors,
    )

    write_json(WORK_DIR / "test_results.json", results)
    summary = {
        "exercise": EXERCISE_REL.as_posix(),
        "cases_expected": len(EXPECTED_CASES),
        "cases_reproduced": len(results),
        "cases_passed": sum(result["passed"] for result in results),
        "validator": validator_summary,
        "learner_stub_unchanged": learner_solution.read_bytes() == learner_contents,
        "errors": errors,
    }
    write_json(WORK_DIR / "check_summary.json", summary)
    if errors:
        raise SystemExit("\n".join(errors))
    print(
        f"PASS: {len(results)} reference cases and "
        f"{validator_summary['passed_tests']} validator tests passed."
    )


if __name__ == "__main__":
    main()
