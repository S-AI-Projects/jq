#!/usr/bin/env python3
"""Path and configuration validator for task R07-T048 (roman-numerals).

Verifies that all files declared in .meta/config.json exist on disk,
confirms that 3 deliberately invalid metadata fixtures fail for intended reasons,
and executes isolated tests against the reference solution.
"""

import copy
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
EXERCISE_REL = pathlib.Path("exercises/practice/roman-numerals")
EXERCISE_DIR = REPO_ROOT / EXERCISE_REL
CONFIG_PATH = EXERCISE_DIR / ".meta" / "config.json"
STUB_FILE = EXERCISE_DIR / "roman-numerals.jq"
EXAMPLE_FILE = EXERCISE_DIR / ".meta" / "example.jq"

ANCHOR_CASES = [
    "1 is I",
    "2 is II",
    "3 is III"
]

def verify_learner_stub():
    with open(STUB_FILE, "r") as f:
        content = f.read()
    if "implement your solution" not in content and "halt_error" not in content:
        raise AssertionError("Learner stub roman-numerals.jq has been modified or solved!")

def validate_config(config_dict: dict, base_dir: pathlib.Path):
    """Validates that files declared in config_dict resolve inside base_dir."""
    files = config_dict.get("files", {})
    for role in ["solution", "test", "example"]:
        entries = files.get(role, [])
        if not entries:
            raise ValueError(f"Config error: missing required role '{role}' in files")
        for rel_path in entries:
            resolved = base_dir / rel_path
            if not resolved.exists():
                raise FileNotFoundError(f"Missing {role} file: {resolved}")

def test_metadata_fixtures():
    with open(CONFIG_PATH, "r") as f:
        real_config = json.load(f)

    # 1. Real config must pass
    validate_config(real_config, EXERCISE_DIR)
    print("✓ Real metadata in .meta/config.json passed validation.")

    # 2. Fixture 1: invalid solution
    bad_sol = copy.deepcopy(real_config)
    bad_sol["files"]["solution"] = ["nonexistent-solution.jq"]
    try:
        validate_config(bad_sol, EXERCISE_DIR)
        raise AssertionError("Fixture 1 (invalid solution) unexpectedly passed!")
    except FileNotFoundError:
        print("✓ Fixture 1 (invalid solution path) correctly rejected.")

    # 3. Fixture 2: invalid test
    bad_test = copy.deepcopy(real_config)
    bad_test["files"]["test"] = ["missing-test-roman-numerals.bats"]
    try:
        validate_config(bad_test, EXERCISE_DIR)
        raise AssertionError("Fixture 2 (invalid test) unexpectedly passed!")
    except FileNotFoundError:
        print("✓ Fixture 2 (invalid test path) correctly rejected.")

    # 4. Fixture 3: invalid example
    bad_ex = copy.deepcopy(real_config)
    bad_ex["files"]["example"] = [".meta/nonexistent-example.jq"]
    try:
        validate_config(bad_ex, EXERCISE_DIR)
        raise AssertionError("Fixture 3 (invalid example) unexpectedly passed!")
    except FileNotFoundError:
        print("✓ Fixture 3 (invalid example path) correctly rejected.")

def run_isolated():
    temp_dir = tempfile.mkdtemp(prefix="rn_val_")
    try:
        for fname in ["bats-extra.bash", "bats-jq.bash", "test-roman-numerals.bats"]:
            shutil.copy(EXERCISE_DIR / fname, temp_dir)
        shutil.copy(EXAMPLE_FILE, os.path.join(temp_dir, "roman-numerals.jq"))

        env = os.environ.copy()
        env["BATS_RUN_SKIPPED"] = "true"
        env["PATH"] = f"/opt/homebrew/bin:{env.get('PATH', '')}"

        proc = subprocess.run(
            ["bats", "--tap", "test-roman-numerals.bats"],
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
    print("Running Course Check r07-t048 (roman-numerals)")
    print("=" * 60)

    verify_learner_stub()
    print("✓ Learner stub verified unsolved in working tree.")

    test_metadata_fixtures()

    rc, out, err = run_isolated()
    lines = out.strip().splitlines()
    passed = [l[5:] for l in lines if l.startswith("ok ")]
    failed = [l for l in lines if l.startswith("not ok ")]

    if rc != 0 or len(failed) > 0 or len(passed) == 0:
        raise AssertionError(f"Tests failed with code {rc}:\n{err}\n{out}")

    for anchor in ANCHOR_CASES:
        if not any(anchor in p for p in passed):
            raise AssertionError(f"Anchor case '{anchor}' missing from passed tests!")

    print(f"✓ Reference passed all {len(passed)} canonical tests in isolated runner.")
    verify_learner_stub()
    print("✓ All checks passed successfully.")
    return passed

if __name__ == "__main__":
    main()
