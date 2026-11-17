#!/usr/bin/env python3
"""Automated check script for task R07-T051.

Validates the canonical case entries and rationales for prime-factors,
verifies that all enabled tests pass against the reference implementation
in a temporary copy without rewriting the working tree, and saves test evidence.
"""

import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
EXERCISE_REL = pathlib.Path("exercises/practice/prime-factors")
EXERCISE_DIR = REPO_ROOT / EXERCISE_REL
META_DIR = EXERCISE_DIR / ".meta"
CONFIG_FILE = META_DIR / "config.json"
TESTS_TOML = META_DIR / "tests.toml"
WORK_DIR = REPO_ROOT / "work/R07-T051"

SELECTED_UUIDS = {
    "924fc966-a8f5-4288-82f2-6b9224819ccd": {
        "test_name": "no factors",
        "input": {"value": 1},
        "expected": [],
        "expected_keywords": ["no factors", "until", "empty"],
    },
    "17e30670-b105-4305-af53-ddde182cb6ad": {
        "test_name": "prime number",
        "input": {"value": 2},
        "expected": [2],
        "expected_keywords": ["prime number", "until", ".number > 1"],
    },
    "238d57c8-4c12-42ef-af34-ae4929f94789": {
        "test_name": "another prime number",
        "input": {"value": 3},
        "expected": [3],
        "expected_keywords": ["another prime number", "until", ".number > 1"],
    },
}

ALL_CANONICAL_CASES = [
    {"name": "no factors", "input": {"value": 1}, "expected": []},
    {"name": "prime number", "input": {"value": 2}, "expected": [2]},
    {"name": "another prime number", "input": {"value": 3}, "expected": [3]},
    {"name": "square of a prime", "input": {"value": 9}, "expected": [3, 3]},
    {"name": "product of first prime", "input": {"value": 4}, "expected": [2, 2]},
    {"name": "cube of a prime", "input": {"value": 8}, "expected": [2, 2, 2]},
    {"name": "product of second prime", "input": {"value": 27}, "expected": [3, 3, 3]},
    {"name": "product of third prime", "input": {"value": 625}, "expected": [5, 5, 5, 5]},
    {"name": "product of first and second prime", "input": {"value": 6}, "expected": [2, 3]},
    {"name": "product of primes and non-primes", "input": {"value": 12}, "expected": [2, 2, 3]},
    {"name": "product of primes", "input": {"value": 901255}, "expected": [5, 17, 23, 461]},
    {"name": "factors include a large prime", "input": {"value": 93819012551}, "expected": [11, 9539, 894119]},
]


def collect_tool_versions() -> dict[str, str]:
    """Record versions of required tools."""
    versions = {"python": sys.version.split()[0]}

    def get_version(cmd: list[str]) -> str:
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return res.stdout.strip().splitlines()[0]
        except Exception as e:
            return f"error: {e}"

    versions["jq"] = get_version(["jq", "--version"])
    versions["bats"] = get_version(["bats", "--version"])
    versions["bash"] = get_version(["bash", "--version"])
    # GNU grep check
    grep_cmd = "ggrep" if shutil.which("ggrep") else "grep"
    versions["grep"] = get_version([grep_cmd, "--version"])
    return versions


def check_stub_unsolved(solution_path: pathlib.Path) -> None:
    """Ensure the learner solution stub in the working tree is unchanged and unsolved."""
    assert solution_path.exists(), f"Solution file not found at {solution_path}"
    content = solution_path.read_text(encoding="utf-8")
    assert "halt_error" in content or "Remove this line" in content, (
        f"Learner stub at {solution_path} appears modified or solved!"
    )
    # Test that executing stub directly halts with error
    proc = subprocess.run(
        ["jq", "-c", "-f", str(solution_path)],
        input=json.dumps({"value": 1}),
        capture_output=True,
        text=True,
    )
    assert proc.returncode != 0, "Learner stub must fail/halt on input"
    print("✓ Learner stub verified unsolved in working tree.")


def check_toml_and_rationales() -> dict:
    """Validate tests.toml structure, counts, and selected UUID rationales."""
    with open(TESTS_TOML, "rb") as f:
        tests_data = tomllib.load(f)

    total_cases = len(tests_data)
    assert total_cases == 12, f"Expected 12 canonical cases in tests.toml, found {total_cases}"

    included_count = 0
    excluded_count = 0
    for uuid_key, entry in tests_data.items():
        if entry.get("include", True):
            included_count += 1
        else:
            excluded_count += 1

    assert included_count == 12, f"Expected 12 included cases, found {included_count}"
    assert excluded_count == 0, f"Expected 0 excluded cases, found {excluded_count}"

    toml_text = TESTS_TOML.read_text(encoding="utf-8")
    rationales = {}

    for uuid, req in SELECTED_UUIDS.items():
        assert uuid in tests_data, f"UUID {uuid} not found in tests.toml"
        entry = tests_data[uuid]
        assert entry.get("description") == req["test_name"], (
            f"Description mismatch for {uuid}: expected '{req['test_name']}', got '{entry.get('description')}'"
        )

        comment_value = entry.get("comment", "")
        # Also check if comment appears in TOML text
        assert comment_value or f"[{uuid}]" in toml_text, f"No rationale found for {uuid}"
        full_text_for_entry = toml_text.split(f"[{uuid}]")[1].split("[")[0]

        rationale_text = (comment_value + "\n" + full_text_for_entry).lower()
        for kw in req["expected_keywords"]:
            assert kw.lower() in rationale_text, (
                f"Rationale for {uuid} ({req['test_name']}) missing required concept/keyword '{kw}'"
            )

        rationales[uuid] = {
            "test_name": req["test_name"],
            "comment": comment_value,
            "included": entry.get("include", True),
        }

    print(f"✓ tests.toml valid: {included_count} included, {excluded_count} excluded.")
    print("✓ All 3 UUID rationales verified and cite relevant jq operations.")
    return {
        "total_cases": total_cases,
        "included_count": included_count,
        "excluded_count": excluded_count,
        "rationales": rationales,
    }


def evaluate_reference_cases(example_path: pathlib.Path) -> list[dict]:
    """Run jq reference implementation on all canonical cases and record results."""
    results = []
    for case in ALL_CANONICAL_CASES:
        inp = case["input"]
        expected = case["expected"]
        proc = subprocess.run(
            ["jq", "-c", "-f", str(example_path)],
            input=json.dumps(inp),
            capture_output=True,
            text=True,
            check=True,
        )
        actual = json.loads(proc.stdout.strip())
        assert actual == expected, (
            f"Test case '{case['name']}' failed: expected {expected}, got {actual}"
        )
        results.append({
            "name": case["name"],
            "input": inp,
            "expected": expected,
            "actual": actual,
            "passed": True,
        })
    print(f"✓ All {len(results)} canonical cases passed against reference example.jq.")
    return results


def run_validation_in_temp_copy(paths: dict) -> dict:
    """Copy exercise to temp directory, substitute reference, and run bin/validate_one_exercise."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = pathlib.Path(tmpdir)
        tmp_exercise = tmp_path / EXERCISE_REL
        shutil.copytree(EXERCISE_DIR, tmp_exercise)

        # Substitute reference into solution in temporary copy ONLY
        tmp_solution = tmp_exercise / paths["solution"]
        tmp_example = tmp_exercise / paths["example"]
        shutil.copy2(tmp_example, tmp_solution)

        # Also copy bin/ for standalone validation if needed
        tmp_bin = tmp_path / "bin"
        shutil.copytree(REPO_ROOT / "bin", tmp_bin)

        # Run bin/validate_one_exercise from temp directory
        proc = subprocess.run(
            [str(REPO_ROOT / "bin/validate_one_exercise"), str(EXERCISE_REL)],
            cwd=str(tmp_path),
            capture_output=True,
            text=True,
        )
        output = proc.stdout + proc.stderr
        print(output.strip())

        assert proc.returncode == 0, f"Validation failed with code {proc.returncode}:\n{output}"

        # Parse TAP output for executed tests
        tap_plan = re.search(r"1\.\.(\d+)", output)
        assert tap_plan, f"Could not find TAP test plan in output:\n{output}"
        num_planned = int(tap_plan.group(1))
        assert num_planned > 0, "Zero tests planned!"

        ok_matches = re.findall(r"^ok \d+ (.*)$", output, flags=re.MULTILINE)
        num_passed = len(ok_matches)
        assert num_passed == num_planned, (
            f"Mismatch between planned ({num_planned}) and passed ({num_passed}) tests"
        )
        assert num_passed == 12, f"Expected 12 executed tests, got {num_passed}"

        # Ensure named cases are all present
        for req in SELECTED_UUIDS.values():
            assert req["test_name"] in ok_matches, (
                f"Named test '{req['test_name']}' not found in executed test list: {ok_matches}"
            )

        print(f"✓ Validation in temporary copy passed with {num_passed} passing tests.")
        return {
            "returncode": proc.returncode,
            "tests_planned": num_planned,
            "tests_passed": num_passed,
            "test_names": ok_matches,
        }


def main():
    print("=" * 60)
    print("Running R07-T051 Verification Checks")
    print("=" * 60)

    WORK_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Tool versions
    tool_versions = collect_tool_versions()
    print("Tool versions:", tool_versions)
    with open(WORK_DIR / "tool_versions.json", "w", encoding="utf-8") as f:
        json.dump(tool_versions, f, indent=2)

    # 2. Config paths
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        config = json.load(f)

    solution_file = config["files"]["solution"][0]
    test_file = config["files"]["test"][0]
    example_file = config["files"]["example"][0]

    paths = {
        "solution": solution_file,
        "test": test_file,
        "example": example_file,
    }

    # 3. Check working tree stub is unsolved
    check_stub_unsolved(EXERCISE_DIR / solution_file)

    # 4. Check tests.toml and rationales
    toml_check_results = check_toml_and_rationales()

    # 5. Evaluate all canonical cases directly
    case_results = evaluate_reference_cases(EXERCISE_DIR / example_file)
    with open(WORK_DIR / "test_results.json", "w", encoding="utf-8") as f:
        json.dump(case_results, f, indent=2)

    # 6. Validate via bin/validate_one_exercise in temporary copy
    validation_results = run_validation_in_temp_copy(paths)

    # 7. Check working tree stub is STILL unsolved
    check_stub_unsolved(EXERCISE_DIR / solution_file)

    # 8. Save overall summary
    summary = {
        "task_id": "R07-T051",
        "exercise": "prime-factors",
        "tool_versions": tool_versions,
        "counts_before": {"included": 12, "excluded": 0},
        "counts_after": {"included": 12, "excluded": 0},
        "toml_check": toml_check_results,
        "validation_results": validation_results,
        "all_cases_passed": True,
        "learner_stub_unsolved": True,
    }
    with open(WORK_DIR / "check_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print("=" * 60)
    print("✓ All checks completed successfully. Results saved to work/R07-T051/")
    print("=" * 60)


if __name__ == "__main__":
    main()
