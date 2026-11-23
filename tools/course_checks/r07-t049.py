#!/usr/bin/env python3
"""Isolated test runner for task R07-T049 (knapsack).

Executes exercises/practice/knapsack tests against the reference implementation
strictly inside an isolated temporary directory, guaranteeing that learner solution
files in the working tree are not modified.
"""

import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
EXERCISE_REL = pathlib.Path("exercises/practice/knapsack")
EXERCISE_DIR = REPO_ROOT / EXERCISE_REL
STUB_FILE = EXERCISE_DIR / "knapsack.jq"
EXAMPLE_FILE = EXERCISE_DIR / ".meta" / "example.jq"

ANCHOR_CASES = [
    "no items",
    "one item, too heavy",
    "five items (cannot be greedy by weight)",
]

def get_file_hash(path: pathlib.Path) -> str:
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()

def verify_learner_stub():
    with open(STUB_FILE, "r") as f:
        content = f.read()
    if "implement your solution" not in content and "halt_error" not in content:
        raise AssertionError("Learner stub knapsack.jq has been modified or solved!")

def run_in_sandbox(solution_content: str, test_filename: str = "test-knapsack.bats"):
    temp_dir = tempfile.mkdtemp(prefix="knapsack_runner_")
    try:
        for fname in ["bats-extra.bash", "bats-jq.bash", "test-knapsack.bats"]:
            shutil.copy(EXERCISE_DIR / fname, temp_dir)
        with open(os.path.join(temp_dir, "knapsack.jq"), "w") as f:
            f.write(solution_content)

        env = os.environ.copy()
        env["BATS_RUN_SKIPPED"] = "true"
        env["PATH"] = f"/opt/homebrew/bin:{env.get('PATH', '')}"

        proc = subprocess.run(
            ["bats", "--tap", test_filename],
            cwd=temp_dir,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        return proc.returncode, proc.stdout, proc.stderr
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

def test_negative_cases():
    # 1. Deliberately failing test returns non-zero exit code
    rc_fail, _, _ = run_in_sandbox("def maximumValue: -999;")
    if rc_fail == 0:
        raise AssertionError("Simulated failure run unexpectedly returned 0 exit code!")
    print("✓ Deliberately failing solution correctly produced non-zero exit code.")

    # 2. Zero-test run returns non-zero or failure
    temp_dir = tempfile.mkdtemp(prefix="knapsack_zero_")
    try:
        empty_bats = os.path.join(temp_dir, "empty.bats")
        with open(empty_bats, "w") as f:
            f.write("#!/usr/bin/env bats\n# zero tests\n")

        env = os.environ.copy()
        env["PATH"] = f"/opt/homebrew/bin:{env.get('PATH', '')}"
        proc = subprocess.run(
            ["bats", "--tap", "empty.bats"],
            cwd=temp_dir,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        # In Bats or test runner, zero tests should fail or be caught
        lines = proc.stdout.strip().splitlines()
        passed = [l for l in lines if l.startswith("ok ")]
        if len(passed) != 0:
            raise AssertionError("Zero-test run unexpectedly produced passed tests!")
        print("✓ Zero-test execution correctly identified.")
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

def main():
    print("=" * 60)
    print("Running Course Check r07-t049 (knapsack)")
    print("=" * 60)

    initial_hash = get_file_hash(STUB_FILE)
    verify_learner_stub()
    print("✓ Learner stub verified unsolved; initial SHA-256:", initial_hash)

    with open(EXAMPLE_FILE, "r") as f:
        ref_code = f.read()

    rc, out, err = run_in_sandbox(ref_code)
    lines = out.strip().splitlines()
    passed = [l[5:] for l in lines if l.startswith("ok ")]
    failed = [l for l in lines if l.startswith("not ok ")]

    if rc != 0 or len(failed) > 0 or len(passed) == 0:
        raise AssertionError(f"Reference failed tests: {failed}\n{err}\n{out}")

    for anchor in ANCHOR_CASES:
        if not any(anchor in p for p in passed):
            raise AssertionError(f"Anchor case '{anchor}' missing from passed tests!")

    print(f"✓ Reference passed all {len(passed)} canonical tests in isolated runner.")

    # Negative tests
    test_negative_cases()

    # Re-verify hash
    post_hash = get_file_hash(STUB_FILE)
    if initial_hash != post_hash:
        raise AssertionError("Learner stub hash changed after test runs!")
    verify_learner_stub()
    print("✓ Learner stub hash identical before and after all runs:", post_hash)
    print("✓ All checks passed successfully.")
    return passed

if __name__ == "__main__":
    main()
