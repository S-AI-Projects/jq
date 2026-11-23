#!/usr/bin/env python3
"""Automated verification check for task R07-T045 (difference-of-squares).

Verifies complexity comment annotations, operation count scaling across
benchmark sizes N in {1, 5, 100}, runs isolated tests against reference,
and ensures learner files remain unsolved.
"""

import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
EXERCISE_REL = pathlib.Path("exercises/practice/difference-of-squares")
EXERCISE_DIR = REPO_ROOT / EXERCISE_REL
STUB_FILE = EXERCISE_DIR / "difference-of-squares.jq"
EXAMPLE_FILE = EXERCISE_DIR / ".meta" / "example.jq"
WORK_DIR = REPO_ROOT / "work" / "R07-T045"

BENCHMARK_CASES = {
    1: {"name": "difference of squares 1", "expected": 0, "operations": 3},
    5: {"name": "difference of squares 5", "expected": 170, "operations": 15},
    100: {"name": "difference of squares 100", "expected": 25164150, "operations": 300},
}

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
        raise AssertionError("Learner stub difference-of-squares.jq has been modified or solved!")

def verify_complexity_comment():
    with open(EXAMPLE_FILE, "r") as f:
        code = f.read()
    for req in ["O(N)", "linear", "3*N", "N = 1: 3 operations", "N = 5: 15 operations", "N = 100: 300 operations"]:
        if req not in code:
            raise AssertionError(f"Required complexity specification '{req}' missing from example.jq comment!")

def run_isolated():
    temp_dir = tempfile.mkdtemp(prefix="dos_val_")
    try:
        for fname in ["bats-extra.bash", "bats-jq.bash", "test-difference-of-squares.bats"]:
            shutil.copy(EXERCISE_DIR / fname, temp_dir)
        shutil.copy(EXAMPLE_FILE, os.path.join(temp_dir, "difference-of-squares.jq"))

        env = os.environ.copy()
        env["BATS_RUN_SKIPPED"] = "true"
        env["PATH"] = f"/opt/homebrew/bin:{env.get('PATH', '')}"

        proc = subprocess.run(
            ["bats", "--tap", "test-difference-of-squares.bats"],
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
    print("Running Task R07-T045 Checks (difference-of-squares)")
    print("=" * 60)

    os.makedirs(WORK_DIR, exist_ok=True)
    tool_vers = get_tool_versions()
    print("Tool versions:", tool_vers)
    with open(WORK_DIR / "tool_versions.json", "w") as f:
        json.dump(tool_vers, f, indent=2)

    verify_learner_stub()
    print("✓ Learner stub verified unsolved in working tree.")

    verify_complexity_comment()
    print("✓ Complexity/invariant comments verified adjacent to reference.")

    rc, out, err = run_isolated()
    lines = out.strip().splitlines()
    passed = [l[5:] for l in lines if l.startswith("ok ")]
    failed = [l for l in lines if l.startswith("not ok ")]

    if rc != 0 or len(failed) > 0 or len(passed) == 0:
        raise AssertionError(f"Tests failed with code {rc}:\n{err}\n{out}")

    for n, data in BENCHMARK_CASES.items():
        if not any(data["name"] in p for p in passed):
            raise AssertionError(f"Benchmark case '{data['name']}' not found in passed tests!")

    print(f"✓ Reference passed all {len(passed)} canonical tests in isolated runner.")

    summary = {
        "task_id": "R07-T045",
        "exercise": "difference-of-squares",
        "tool_versions": tool_vers,
        "benchmark_cases": BENCHMARK_CASES,
        "complexity_class": "O(N) linear time, O(N) space",
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
    print("✓ All Task R07-T045 checks passed successfully.")

if __name__ == "__main__":
    main()
