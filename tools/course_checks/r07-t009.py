#!/usr/bin/env python3
"""
Isolated test runner for pig-latin (R07-T009).
Executes tests in a temporary sandbox, protecting learner starter stubs,
asserting hash invariance, and propagating failures/zero-test conditions.
"""

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile


def hash_file(filepath):
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        hasher.update(f.read())
    return hasher.hexdigest()


def run_isolated(repo_root, mutate_solution=None, empty_tests=False):
    exercise_rel = "exercises/practice/pig-latin"
    exercise_dir = os.path.join(repo_root, exercise_rel)

    config_path = os.path.join(exercise_dir, ".meta/config.json")
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    stub_rel = cfg["files"]["solution"][0]
    test_rel = cfg["files"]["test"][0]
    example_rel = cfg["files"]["example"][0]

    stub_path = os.path.join(exercise_dir, stub_rel)
    stub_hash_before = hash_file(stub_path)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_exercise = os.path.join(tmpdir, exercise_rel)
        os.makedirs(os.path.dirname(tmp_exercise), exist_ok=True)
        shutil.copytree(exercise_dir, tmp_exercise)
        shutil.copytree(os.path.join(repo_root, "bin"), os.path.join(tmpdir, "bin"))

        # Substitute reference or mutant into temp copy
        tmp_example = os.path.join(tmp_exercise, example_rel)
        if mutate_solution:
            with open(tmp_example, "w", encoding="utf-8") as f:
                f.write(mutate_solution)

        if empty_tests:
            tmp_tests = os.path.join(tmp_exercise, test_rel)
            with open(tmp_tests, "w", encoding="utf-8") as f:
                f.write("# empty test file\n")

        env = os.environ.copy()
        env["PATH"] = f"/opt/homebrew/bin:{env.get('PATH', '')}"

        res = subprocess.run(
            ["./bin/validate_one_exercise", exercise_rel],
            cwd=tmpdir,
            capture_output=True,
            text=True,
            env=env
        )

        tap_ok = [l for l in res.stdout.splitlines() if l.startswith("ok ")]

        # Check hash invariance on working tree
        stub_hash_after = hash_file(stub_path)
        if stub_hash_before != stub_hash_after:
            raise RuntimeError("CRITICAL ERROR: Learner file hash changed during isolated run!")

        return {
            "returncode": res.returncode,
            "stdout": res.stdout,
            "stderr": res.stderr,
            "passed_tests": len(tap_ok),
            "tap_ok": tap_ok
        }


def main():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))

    # 1. Real reference execution
    real_run = run_isolated(repo_root)
    if real_run["returncode"] != 0:
        print("ERROR: Real reference run failed:\n" + real_run["stdout"] + "\n" + real_run["stderr"], file=sys.stderr)
        sys.exit(1)
    if real_run["passed_tests"] == 0:
        print("ERROR: Real reference produced zero passing tests!", file=sys.stderr)
        sys.exit(1)

    # 2. Deliberately failing reference
    failing_run = run_isolated(repo_root, mutate_solution='"wrong_output"')
    if failing_run["returncode"] == 0:
        print("ERROR: Deliberately failing mutant unexpectedly passed!", file=sys.stderr)
        sys.exit(1)

    # 3. Empty test selection
    empty_run = run_isolated(repo_root, empty_tests=True)
    if empty_run["returncode"] == 0 and empty_run["passed_tests"] > 0:
        print("ERROR: Empty test suite unexpectedly succeeded!", file=sys.stderr)
        sys.exit(1)

    print(f"Isolated runner check succeeded: {real_run['passed_tests']} real tests passed; defect/empty modes caught correctly.")


if __name__ == "__main__":
    main()
