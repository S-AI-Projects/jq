#!/usr/bin/env python3
"""Reusable focused regeneration check for minesweeper (R07-T012)."""

import os
import re
import shutil
import subprocess
import sys
import tempfile


def strip_timestamp(content: str) -> list[str]:
    """Strip generator timestamp lines for strict AST/semantic equality comparison."""
    return [line for line in content.splitlines() if not line.startswith("# generated on ")]


def run_generator_in_copy(repo_root: str, dest_dir: str) -> str:
    """Copy repo to temporary directory and run generator on minesweeper."""
    exercise_rel = "exercises/practice/minesweeper"
    shutil.copytree(os.path.join(repo_root, "bin"), os.path.join(dest_dir, "bin"))
    shutil.copytree(os.path.join(repo_root, "lib"), os.path.join(dest_dir, "lib"), dirs_exist_ok=True)
    os.makedirs(os.path.join(dest_dir, "exercises/practice"), exist_ok=True)
    shutil.copytree(os.path.join(repo_root, exercise_rel), os.path.join(dest_dir, exercise_rel))

    env = os.environ.copy()
    env["PATH"] = f"/opt/homebrew/bin:{env.get('PATH', '')}"

    res = subprocess.run(
        [sys.executable, "bin/test-generator", "--no-pull", "minesweeper"],
        cwd=dest_dir,
        capture_output=True,
        text=True,
        env=env
    )
    if res.returncode != 0:
        raise RuntimeError(f"test-generator failed (exit code {res.returncode}):\n{res.stdout}\n{res.stderr}")

    test_file = os.path.join(dest_dir, exercise_rel, "test-minesweeper.bats")
    with open(test_file, "r", encoding="utf-8") as f:
        return f.read()


def main():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    exercise_rel = "exercises/practice/minesweeper"
    bats_path = os.path.join(repo_root, exercise_rel, "test-minesweeper.bats")

    if not os.path.exists(bats_path):
        print(f"ERROR: {bats_path} does not exist", file=sys.stderr)
        sys.exit(1)

    with open(bats_path, "r", encoding="utf-8") as f:
        existing_bats = f.read()

    # Verify presence of the 3 anchored cases
    anchored_cases = ["no rows", "no columns", "no mines"]
    for case in anchored_cases:
        if f"@test '{case}'" not in existing_bats:
            print(f"ERROR: Anchored case '{case}' missing from test suite!", file=sys.stderr)
            sys.exit(1)

    # Perform two independent generations in fresh temporary directories
    with tempfile.TemporaryDirectory() as tmp1, tempfile.TemporaryDirectory() as tmp2:
        gen1 = run_generator_in_copy(repo_root, tmp1)
        gen2 = run_generator_in_copy(repo_root, tmp2)

        lines1 = strip_timestamp(gen1)
        lines2 = strip_timestamp(gen2)
        lines_existing = strip_timestamp(existing_bats)

        if lines1 != lines2:
            print("ERROR: Non-deterministic test generation between two fresh copies!", file=sys.stderr)
            sys.exit(1)

        if lines1 != lines_existing:
            print("ERROR: Generated test contents differ from repository test suite beyond timestamp!", file=sys.stderr)
            sys.exit(1)

    print("SUCCESS: Minesweeper test generation is reproducible across independent runs.")


if __name__ == "__main__":
    main()
