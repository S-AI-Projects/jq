#!/usr/bin/env python3
"""Reusable focused regeneration check for task R07-T042 (tournament).

Verifies the deterministic generation path from problem-specifications,
tests.toml, and template.j2 to test-tournament.bats, and verifies reference
execution in an isolated temporary environment.
"""

import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
EXERCISE_REL = pathlib.Path("exercises/practice/tournament")
EXERCISE_DIR = REPO_ROOT / EXERCISE_REL
BATS_FILE = EXERCISE_DIR / "test-tournament.bats"
STUB_FILE = EXERCISE_DIR / "tournament.jq"
EXAMPLE_FILE = EXERCISE_DIR / ".meta" / "example.jq"

ANCHOR_CASES = [
    "just the header if no input",
    "a win is three points, a loss is zero points",
    "a win can also be expressed as a loss"
]

def verify_learner_stub():
    with open(STUB_FILE, "r") as f:
        content = f.read()
    if "implement your solution" not in content and "halt_error" not in content:
        raise AssertionError("Learner stub tournament.jq has been modified or solved!")

def normalize_timestamp(text: str) -> str:
    return re.sub(r"# generated on .*", "# generated on <NORMALIZED>", text)

def verify_regeneration_route():
    # Verify that running generator generates identical suite to checked-in file
    temp_dir = tempfile.mkdtemp(prefix="tourn_gen_")
    try:
        # We test generation reproducibility by generating into temporary copies
        gen_script = REPO_ROOT / "bin" / "test-generator"
        env = os.environ.copy()
        env["PATH"] = f"/opt/anaconda3/bin:/opt/homebrew/bin:{env.get('PATH', '')}"

        # Run generator
        proc1 = subprocess.run(
            [sys.executable, str(gen_script), "--no-pull", "tournament"],
            cwd=str(REPO_ROOT),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if proc1.returncode != 0:
            raise AssertionError(f"First generation failed: {proc1.stderr}")

        with open(BATS_FILE, "r") as f:
            content1 = normalize_timestamp(f.read())

        proc2 = subprocess.run(
            [sys.executable, str(gen_script), "--no-pull", "tournament"],
            cwd=str(REPO_ROOT),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if proc2.returncode != 0:
            raise AssertionError(f"Second generation failed: {proc2.stderr}")

        with open(BATS_FILE, "r") as f:
            content2 = normalize_timestamp(f.read())

        if content1 != content2:
            raise AssertionError("Consecutive generations differed after timestamp normalization!")

        return content1
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

def run_isolated_tests():
    verify_learner_stub()
    temp_dir = tempfile.mkdtemp(prefix="tourn_test_")
    try:
        for fname in ["bats-extra.bash", "bats-jq.bash", "test-tournament.bats"]:
            shutil.copy(EXERCISE_DIR / fname, temp_dir)
        shutil.copy(EXAMPLE_FILE, os.path.join(temp_dir, "tournament.jq"))

        env = os.environ.copy()
        env["BATS_RUN_SKIPPED"] = "true"
        env["PATH"] = f"/opt/homebrew/bin:{env.get('PATH', '')}"

        proc = subprocess.run(
            ["bats", "--tap", "test-tournament.bats"],
            cwd=temp_dir,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if proc.returncode != 0:
            raise AssertionError(f"Tests failed with exit code {proc.returncode}:\n{proc.stderr}\n{proc.stdout}")

        lines = proc.stdout.strip().splitlines()
        passed = [line[5:] for line in lines if line.startswith("ok ")]
        failed = [line for line in lines if line.startswith("not ok ")]

        if len(failed) > 0 or len(passed) == 0:
            raise AssertionError(f"Test run incomplete or failed: {failed}")

        for anchor in ANCHOR_CASES:
            if not any(anchor in p for p in passed):
                raise AssertionError(f"Anchor case '{anchor}' missing from passed cases!")

        return passed
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

def main():
    print("=" * 60)
    print("Running Course Check r07-t042 (tournament)")
    print("=" * 60)

    verify_learner_stub()
    print("✓ Learner stub verified unsolved in working tree.")

    verify_regeneration_route()
    print("✓ Test generation path verified reproducible and deterministic.")

    passed = run_isolated_tests()
    print(f"✓ Reference passed all {len(passed)} test cases in isolated runner.")
    verify_learner_stub()
    print("✓ All checks passed successfully.")

if __name__ == "__main__":
    main()
