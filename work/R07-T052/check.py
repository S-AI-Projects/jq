#!/usr/bin/env python3
"""Automated check script for task R07-T052.

Validates the canonical case entries and reproduction path for spiral-matrix,
verifies that all enabled tests pass against the reference implementation
in a temporary copy without rewriting the working tree, checks regeneration
reproducibility across temporary copies, and saves comprehensive test evidence.
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
EXERCISE_REL = pathlib.Path("exercises/practice/spiral-matrix")
EXERCISE_DIR = REPO_ROOT / EXERCISE_REL
META_DIR = EXERCISE_DIR / ".meta"
CONFIG_FILE = META_DIR / "config.json"
TESTS_TOML = META_DIR / "tests.toml"
WORK_DIR = REPO_ROOT / "work/R07-T052"
MAINTENANCE_DOC = REPO_ROOT / "docs/maintenance/spiral-matrix.md"
COURSE_CHECK_SCRIPT = REPO_ROOT / "tools/course_checks/r07-t052.py"

ANCHOR_CASES = {
    "8f584201-b446-4bc9-b132-811c8edd9040": {
        "name": "empty spiral",
        "input": {"size": 0},
        "expected": [],
    },
    "e40ae5f3-e2c9-4639-8116-8a119d632ab2": {
        "name": "trivial spiral",
        "input": {"size": 1},
        "expected": [[1]],
    },
    "cf05e42d-eb78-4098-a36e-cdaf0991bc48": {
        "name": "spiral of size 2",
        "input": {"size": 2},
        "expected": [
            [1, 2],
            [4, 3],
        ],
    },
}

ALL_CANONICAL_CASES = [
    {
        "uuid": "8f584201-b446-4bc9-b132-811c8edd9040",
        "name": "empty spiral",
        "input": {"size": 0},
        "expected": [],
    },
    {
        "uuid": "e40ae5f3-e2c9-4639-8116-8a119d632ab2",
        "name": "trivial spiral",
        "input": {"size": 1},
        "expected": [[1]],
    },
    {
        "uuid": "cf05e42d-eb78-4098-a36e-cdaf0991bc48",
        "name": "spiral of size 2",
        "input": {"size": 2},
        "expected": [
            [1, 2],
            [4, 3],
        ],
    },
    {
        "uuid": "1c475667-c896-4c23-82e2-e033929de939",
        "name": "spiral of size 3",
        "input": {"size": 3},
        "expected": [
            [1, 2, 3],
            [8, 9, 4],
            [7, 6, 5],
        ],
    },
    {
        "uuid": "05ccbc48-d891-44f5-9137-f4ce462a759d",
        "name": "spiral of size 4",
        "input": {"size": 4},
        "expected": [
            [1, 2, 3, 4],
            [12, 13, 14, 5],
            [11, 16, 15, 6],
            [10, 9, 8, 7],
        ],
    },
    {
        "uuid": "f4d2165b-1738-4e0c-bed0-c459045ae50d",
        "name": "spiral of size 5",
        "input": {"size": 5},
        "expected": [
            [1, 2, 3, 4, 5],
            [16, 17, 18, 19, 6],
            [15, 24, 25, 20, 7],
            [14, 23, 22, 21, 8],
            [13, 12, 11, 10, 9],
        ],
    },
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
    proc = subprocess.run(
        ["jq", "-c", "-f", str(solution_path)],
        input=json.dumps({"size": 1}),
        capture_output=True,
        text=True,
    )
    assert proc.returncode != 0, "Learner stub must fail/halt on input"
    print("✓ Learner stub verified unsolved in working tree.")


def check_toml() -> dict:
    """Validate tests.toml structure and test case counts."""
    with open(TESTS_TOML, "rb") as f:
        tests_data = tomllib.load(f)

    total_cases = len(tests_data)
    assert total_cases == 6, f"Expected 6 canonical cases in tests.toml, found {total_cases}"

    included_count = 0
    excluded_count = 0
    for uuid_key, entry in tests_data.items():
        if entry.get("include", True):
            included_count += 1
        else:
            excluded_count += 1

    assert included_count == 6, f"Expected 6 included cases, found {included_count}"
    assert excluded_count == 0, f"Expected 0 excluded cases, found {excluded_count}"

    for uuid, req in ANCHOR_CASES.items():
        assert uuid in tests_data, f"Anchor UUID {uuid} not found in tests.toml"
        assert tests_data[uuid].get("description") == req["name"], (
            f"Description mismatch for {uuid}: expected '{req['name']}', got '{tests_data[uuid].get('description')}'"
        )

    print(f"✓ tests.toml valid: {included_count} included, {excluded_count} excluded.")
    return {
        "total_cases": total_cases,
        "included_count": included_count,
        "excluded_count": excluded_count,
    }


def normalize_bats(content: str) -> str:
    """Normalize Bats file content by stripping the timestamp line."""
    lines = [line for line in content.splitlines() if not line.startswith("# generated on")]
    return "\n".join(lines).strip()


def check_generation_reproducibility() -> dict:
    """Regenerate in two fresh temporary copies and verify reproducibility and no case drops."""
    outputs = []
    with tempfile.TemporaryDirectory() as tmp1, tempfile.TemporaryDirectory() as tmp2:
        for tmp in (tmp1, tmp2):
            tmp_root = pathlib.Path(tmp)
            target_exercise = tmp_root / EXERCISE_REL
            shutil.copytree(EXERCISE_DIR, target_exercise)
            target_bats = target_exercise / "test-spiral-matrix.bats"
            if target_bats.exists():
                target_bats.unlink()
            shutil.copytree(REPO_ROOT / "bin", tmp_root / "bin")

            res = subprocess.run(
                ["python3", "bin/test-generator", "--no-pull", str(EXERCISE_REL)],
                cwd=str(tmp_root),
                capture_output=True,
                text=True,
            )
            assert res.returncode == 0, (
                f"test-generator failed in temp copy:\nstdout: {res.stdout}\nstderr: {res.stderr}"
            )
            assert target_bats.exists(), f"test-generator did not create {target_bats}"
            outputs.append(target_bats.read_text(encoding="utf-8"))

    norm1 = normalize_bats(outputs[0])
    norm2 = normalize_bats(outputs[1])
    assert norm1 == norm2, "Discrepancy detected between two independent test generations!"

    for case in ALL_CANONICAL_CASES:
        assert f"@test '{case['name']}'" in norm1, (
            f"Case '{case['name']}' was dropped in test generation!"
        )

    committed_bats = normalize_bats((EXERCISE_DIR / "test-spiral-matrix.bats").read_text(encoding="utf-8"))
    assert norm1 == committed_bats, "Generated tests differ from committed test-spiral-matrix.bats!"

    print("✓ Two independent generations match identically; all 6 cases present.")
    return {
        "reproducible": True,
        "total_cases_generated": len(ALL_CANONICAL_CASES),
        "anchor_cases_present": [c["name"] for c in ANCHOR_CASES.values()],
    }


def evaluate_reference_cases(example_path: pathlib.Path) -> list[dict]:
    """Run jq reference implementation directly on all canonical cases and record results."""
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
            "uuid": case["uuid"],
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

        tmp_bin = tmp_path / "bin"
        shutil.copytree(REPO_ROOT / "bin", tmp_bin)

        proc = subprocess.run(
            [str(REPO_ROOT / "bin/validate_one_exercise"), str(EXERCISE_REL)],
            cwd=str(tmp_path),
            capture_output=True,
            text=True,
        )
        output = proc.stdout + proc.stderr
        print(output.strip())

        assert proc.returncode == 0, f"Validation failed with code {proc.returncode}:\n{output}"

        tap_plan = re.search(r"1\.\.(\d+)", output)
        assert tap_plan, f"Could not find TAP test plan in output:\n{output}"
        num_planned = int(tap_plan.group(1))
        assert num_planned > 0, "Zero tests planned!"

        ok_matches = re.findall(r"^ok \d+ (.*)$", output, flags=re.MULTILINE)
        num_passed = len(ok_matches)
        assert num_passed == num_planned, (
            f"Mismatch between planned ({num_planned}) and passed ({num_passed}) tests"
        )
        assert num_passed == 6, f"Expected 6 executed tests, got {num_passed}"

        for req in ANCHOR_CASES.values():
            assert req["name"] in ok_matches, (
                f"Anchor test '{req['name']}' not found in executed test list: {ok_matches}"
            )

        print(f"✓ Validation in temporary copy passed with {num_passed} passing tests.")
        return {
            "returncode": proc.returncode,
            "tests_planned": num_planned,
            "tests_passed": num_passed,
            "test_names": ok_matches,
        }


def check_docs_and_scripts() -> None:
    """Ensure maintenance docs and reusable course checks exist with proper contents."""
    assert MAINTENANCE_DOC.exists(), f"Missing {MAINTENANCE_DOC}"
    doc_text = MAINTENANCE_DOC.read_text(encoding="utf-8")
    assert "bin/test-generator" in doc_text, "Maintenance doc missing reproduction command"
    for case in ANCHOR_CASES.values():
        assert case["name"] in doc_text, f"Maintenance doc missing anchor case: {case['name']}"

    assert COURSE_CHECK_SCRIPT.exists(), f"Missing {COURSE_CHECK_SCRIPT}"
    print("✓ Maintenance documentation and course check script verified.")


def main():
    print("=" * 60)
    print("Running R07-T052 Verification Checks (spiral-matrix)")
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

    # 4. Check tests.toml
    toml_check_results = check_toml()

    # 5. Check generation reproducibility
    gen_results = check_generation_reproducibility()

    # 6. Evaluate all canonical cases directly
    case_results = evaluate_reference_cases(EXERCISE_DIR / example_file)
    with open(WORK_DIR / "test_results.json", "w", encoding="utf-8") as f:
        json.dump(case_results, f, indent=2)

    # 7. Validate via bin/validate_one_exercise in temporary copy
    validation_results = run_validation_in_temp_copy(paths)

    # 8. Check documentation and reusable course checks
    check_docs_and_scripts()

    # 9. Check working tree stub is STILL unsolved
    check_stub_unsolved(EXERCISE_DIR / solution_file)

    # 10. Save overall summary
    summary = {
        "task_id": "R07-T052",
        "exercise": "spiral-matrix",
        "tool_versions": tool_versions,
        "counts_before": {"included": 6, "excluded": 0},
        "counts_after": {"included": 6, "excluded": 0},
        "toml_check": toml_check_results,
        "generation_check": gen_results,
        "validation_results": validation_results,
        "all_cases_passed": True,
        "learner_stub_unsolved": True,
    }
    with open(WORK_DIR / "check_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print("=" * 60)
    print("✓ All checks completed successfully. Results saved to work/R07-T052/")
    print("=" * 60)


if __name__ == "__main__":
    main()
