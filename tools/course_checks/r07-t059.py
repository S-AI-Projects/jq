#!/usr/bin/env python3
"""Isolated test runner for task R07-T059 (flower-field).

Executes exercises/practice/flower-field tests against the reference implementation
strictly inside an isolated temporary directory, guaranteeing that learner solution
files in the working tree are not modified.
"""

import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
EXERCISE_REL = pathlib.Path("exercises/practice/flower-field")
EXERCISE_DIR = REPO_ROOT / EXERCISE_REL
MAINTENANCE_DOC = REPO_ROOT / "docs/maintenance/flower-field.md"

ANCHOR_CASES = [
    "no columns",
    "no flowers",
    "vertical line"
]

def verify_learner_stub():
    stub = EXERCISE_DIR / "flower-field.jq"
    with open(stub, "r") as f:
        content = f.read()
    if "Remove this line and implement your solution" not in content and "halt_error" not in content:
        raise AssertionError("Learner stub flower-field.jq has been modified or solved!")

def run_isolated_tests():
    verify_learner_stub()

    temp_dir = tempfile.mkdtemp(prefix="ff_runner_")
    try:
        # Copy test assets
        for fname in ["bats-extra.bash", "bats-jq.bash", "test-flower-field.bats"]:
            shutil.copy(EXERCISE_DIR / fname, temp_dir)
        # Substitute reference as flower-field.jq only in temporary directory
        shutil.copy(EXERCISE_DIR / ".meta" / "example.jq", os.path.join(temp_dir, "flower-field.jq"))

        env = os.environ.copy()
        env["BATS_RUN_SKIPPED"] = "true"
        proc = subprocess.run(
            ["bats", "--tap", "test-flower-field.bats"],
            cwd=temp_dir,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        if proc.returncode != 0:
            raise AssertionError(f"Tests failed with code {proc.returncode}:\n{proc.stderr}\n{proc.stdout}")

        passed = [line for line in proc.stdout.splitlines() if line.startswith("ok ")]
        for case in ANCHOR_CASES:
            if not any(case in line for line in passed):
                raise AssertionError(f"Anchor case '{case}' was not executed or passed!")

        return passed
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
        # Guarantee working tree stub was not touched
        verify_learner_stub()

def main():
    print("=" * 60)
    print("Running Course Check: r07-t059 (flower-field isolated runner)")
    print("=" * 60)

    verify_learner_stub()
    print("✓ Learner stub verified unsolved before run.")

    assert MAINTENANCE_DOC.exists(), f"Maintenance document missing: {MAINTENANCE_DOC}"
    print(f"✓ Maintenance documentation verified: {MAINTENANCE_DOC.relative_to(REPO_ROOT)}")

    passed = run_isolated_tests()
    print(f"✓ Isolated runner executed {len(passed)} tests successfully (anchor cases verified).")

    verify_learner_stub()
    print("✓ Learner stub verified unsolved after run (working tree clean).")
    print("=" * 60)
    print("✓ All r07-t059 course checks passed successfully!")
    print("=" * 60)

if __name__ == "__main__":
    main()
