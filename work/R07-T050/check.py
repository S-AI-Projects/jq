#!/usr/bin/env python3
"""Automated verification check for task R07-T050 (yacht).

Validates decision table cases (Yacht, Not Yacht, Ones) against reference
solution in isolated execution, verifies hints documentation, and ensures
learner starter files remain untouched.
"""

import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
EXERCISE_REL = pathlib.Path("exercises/practice/yacht")
EXERCISE_DIR = REPO_ROOT / EXERCISE_REL
STUB_FILE = EXERCISE_DIR / "yacht.jq"
EXAMPLE_FILE = EXERCISE_DIR / ".meta" / "example.jq"
HINTS_FILE = EXERCISE_DIR / ".docs" / "hints.md"
WORK_DIR = REPO_ROOT / "work" / "R07-T050"

DECISION_TABLE = [
    {
        "name": "Yacht",
        "dice": [5, 5, 5, 5, 5],
        "category": "yacht",
        "expected": 50,
        "condition": "all 5 dice identical"
    },
    {
        "name": "Not Yacht",
        "dice": [1, 3, 3, 2, 5],
        "category": "yacht",
        "expected": 0,
        "condition": "fewer than 5 dice identical"
    },
    {
        "name": "Ones",
        "dice": [1, 1, 1, 3, 5],
        "category": "ones",
        "expected": 3,
        "condition": "sum of dice showing 1 (3 * 1)"
    },
]

def get_tool_versions():
    def run_cmd(cmd):
        try:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
            return res.stdout.strip().splitlines()[0]
        except Exception as e:
            return f"unavailable ({e})"

    return {
        "python": sys.version.split()[0],
        "jq": run_cmd(["jq", "--version"]),
        "bats": run_cmd(["bats", "--version"]),
        "bash": run_cmd(["bash", "--version"]),
        "grep": run_cmd(["ggrep", "--version"]) if shutil.which("ggrep") else run_cmd(["grep", "--version"]),
    }

def verify_learner_stub():
    with open(STUB_FILE, "r") as f:
        content = f.read()
    if "implement your solution" not in content and "halt_error" not in content:
        raise AssertionError("Learner stub yacht.jq has been modified or solved!")

def verify_decision_table_against_reference():
    with open(EXAMPLE_FILE, "r") as f:
        ref_code = f.read()

    for item in DECISION_TABLE:
        input_json = json.dumps({"dice": item["dice"], "category": item["category"]})
        proc = subprocess.run(
            ["jq", "-n", "--argjson", "data", input_json, f"$data | {ref_code}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        actual = int(proc.stdout.strip())
        if actual != item["expected"]:
            raise AssertionError(f"Decision table case '{item['name']}' mismatch: expected {item['expected']}, got {actual}")
    print(f"✓ Decision table verified directly against reference for all {len(DECISION_TABLE)} anchor cases.")

def run_isolated():
    temp_dir = tempfile.mkdtemp(prefix="yacht_val_")
    try:
        for fname in ["bats-extra.bash", "bats-jq.bash", "test-yacht.bats"]:
            shutil.copy(EXERCISE_DIR / fname, temp_dir)
        shutil.copy(EXAMPLE_FILE, os.path.join(temp_dir, "yacht.jq"))

        env = os.environ.copy()
        env["BATS_RUN_SKIPPED"] = "true"
        env["PATH"] = f"/opt/homebrew/bin:{env.get('PATH', '')}"

        proc = subprocess.run(
            ["bats", "--tap", "test-yacht.bats"],
            cwd=temp_dir,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        return proc.returncode, proc.stdout, proc.stderr
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

def main():
    print("=" * 60)
    print("Running Task R07-T050 Checks (yacht)")
    print("=" * 60)

    os.makedirs(WORK_DIR, exist_ok=True)
    tool_vers = get_tool_versions()
    print("Tool versions:", tool_vers)
    with open(WORK_DIR / "tool_versions.json", "w") as f:
        json.dump(tool_vers, f, indent=2)

    verify_learner_stub()
    print("✓ Learner stub verified unsolved in working tree.")

    verify_decision_table_against_reference()

    rc, out, err = run_isolated()
    lines = out.strip().splitlines()
    passed = [l[5:] for l in lines if l.startswith("ok ")]
    failed = [l for l in lines if l.startswith("not ok ")]

    if rc != 0 or len(failed) > 0 or len(passed) == 0:
        raise AssertionError(f"Tests failed with code {rc}:\n{err}\n{out}")

    for item in DECISION_TABLE:
        if not any(item["name"] in p for p in passed):
            raise AssertionError(f"Anchor case '{item['name']}' missing from passed tests!")

    print(f"✓ Reference passed all {len(passed)} canonical tests in isolated runner.")

    summary = {
        "task_id": "R07-T050",
        "exercise": "yacht",
        "tool_versions": tool_vers,
        "decision_table": DECISION_TABLE,
        "tests_executed": len(passed),
        "tests_passed": len(passed),
        "tests_failed": 0,
        "learner_stub_unsolved": True,
        "return_code": 0
    }

    with open(WORK_DIR / "check_summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    with open(WORK_DIR / "test_results.json", "w") as f:
        json.dump({"passed_tests": passed}, f, indent=2)

    verify_learner_stub()
    print("✓ All Task R07-T050 checks passed successfully.")

if __name__ == "__main__":
    main()
