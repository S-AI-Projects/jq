#!/usr/bin/env python3
"""Path and configuration checker for task R07-T058 (beer-song).

Audits exercises/practice/beer-song/.meta/config.json against filesystem reality,
verifies that all referenced solution, test, example, and invalidator files exist,
and validates reference execution against anchor canonical cases.
"""

import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
EXERCISE_REL = pathlib.Path("exercises/practice/beer-song")
EXERCISE_DIR = REPO_ROOT / EXERCISE_REL
META_DIR = EXERCISE_DIR / ".meta"
CONFIG_FILE = META_DIR / "config.json"
MAINTENANCE_DOC = REPO_ROOT / "docs/maintenance/beer-song.md"

ANCHOR_CASES = [
    "first generic verse",
    "last generic verse",
    "verse with 2 bottles"
]

def verify_configuration():
    if not CONFIG_FILE.exists():
        raise FileNotFoundError(f"Missing config file: {CONFIG_FILE}")

    with open(CONFIG_FILE, "r") as f:
        config = json.load(f)

    files_decl = config.get("files", {})
    missing_files = []

    # Check solution
    for sol in files_decl.get("solution", []):
        p = EXERCISE_DIR / sol
        if not p.exists():
            missing_files.append(("solution", sol, str(p)))

    # Check test
    for tst in files_decl.get("test", []):
        p = EXERCISE_DIR / tst
        if not p.exists():
            missing_files.append(("test", tst, str(p)))

    # Check example
    for ex in files_decl.get("example", []):
        p = EXERCISE_DIR / ex
        if not p.exists():
            missing_files.append(("example", ex, str(p)))

    # Check invalidator
    for inv in files_decl.get("invalidator", []):
        p = EXERCISE_DIR / inv
        if not p.exists():
            missing_files.append(("invalidator", inv, str(p)))

    if missing_files:
        raise AssertionError(f"Mismatch between config.json and disk: {missing_files}")

    return files_decl

def verify_learner_stub():
    stub = EXERCISE_DIR / "beer-song.jq"
    with open(stub, "r") as f:
        content = f.read()
    if "Remove this line and implement your solution" not in content and "halt_error" not in content:
        raise AssertionError("Learner stub beer-song.jq has been modified or solved!")

def run_isolated_validation():
    temp_dir = tempfile.mkdtemp(prefix="beer_check_")
    try:
        for fname in ["bats-extra.bash", "bats-jq.bash", "test-beer-song.bats"]:
            shutil.copy(EXERCISE_DIR / fname, temp_dir)
        shutil.copy(EXERCISE_DIR / ".meta" / "example.jq", os.path.join(temp_dir, "beer-song.jq"))

        env = os.environ.copy()
        env["BATS_RUN_SKIPPED"] = "true"
        proc = subprocess.run(
            ["bats", "--tap", "test-beer-song.bats"],
            cwd=temp_dir,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if proc.returncode != 0:
            raise AssertionError(f"Validation failed with code {proc.returncode}:\n{proc.stderr}\n{proc.stdout}")

        passed = [line for line in proc.stdout.splitlines() if line.startswith("ok ")]
        for case in ANCHOR_CASES:
            if not any(case in line for line in passed):
                raise AssertionError(f"Anchor case '{case}' was not executed or passed!")

        return passed
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

def main():
    print("=" * 60)
    print("Running Course Check: r07-t058 (beer-song)")
    print("=" * 60)

    # 1. Check learner stub
    verify_learner_stub()
    print("✓ Learner stub verified unsolved in working tree.")

    # 2. Check configuration alignment
    files_decl = verify_configuration()
    print(f"✓ config.json verified: all declared files exist ({len(files_decl)} categories checked).")

    # 3. Check maintenance doc
    assert MAINTENANCE_DOC.exists(), f"Maintenance document missing: {MAINTENANCE_DOC}"
    print(f"✓ Maintenance documentation verified: {MAINTENANCE_DOC.relative_to(REPO_ROOT)}")

    # 4. Run isolated validation
    passed_tests = run_isolated_validation()
    print(f"✓ All {len(passed_tests)} tests passed against reference implementation (anchor cases verified).")

    verify_learner_stub()
    print("=" * 60)
    print("✓ All r07-t058 course checks passed successfully!")
    print("=" * 60)

if __name__ == "__main__":
    main()
