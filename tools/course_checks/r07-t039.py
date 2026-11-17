#!/usr/bin/env python3
"""Isolated test runner for binary-search (R07-T039)."""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile

def hash_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

def run_isolated_suite(repo_root, custom_solution_content=None):
    exercise_rel = "exercises/practice/binary-search"
    exercise_dir = os.path.join(repo_root, exercise_rel)

    config_path = os.path.join(exercise_dir, ".meta/config.json")
    with open(config_path, "r") as f:
        cfg = json.load(f)

    solution_rel = cfg["files"]["solution"][0]
    example_rel = cfg["files"]["example"][0]

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_exercise = os.path.join(tmpdir, exercise_rel)
        os.makedirs(os.path.dirname(tmp_exercise), exist_ok=True)
        shutil.copytree(exercise_dir, tmp_exercise)
        shutil.copytree(os.path.join(repo_root, "bin"), os.path.join(tmpdir, "bin"))

        example_src = os.path.join(tmp_exercise, example_rel)
        if custom_solution_content is not None:
            with open(example_src, "w") as f:
                f.write(custom_solution_content)

        res = subprocess.run(["./bin/validate_one_exercise", exercise_rel], cwd=tmpdir, capture_output=True, text=True)
        tap_lines = [l for l in res.stdout.splitlines() if l.startswith("ok ")]
        return res.returncode, len(tap_lines), res.stdout

def main():
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    exercise_dir = os.path.join(root, "exercises/practice/binary-search")
    stub_file = os.path.join(exercise_dir, "binary-search.jq")

    hash_before = hash_file(stub_file)

    # 1. Success run with reference
    code_ref, count_ref, _ = run_isolated_suite(root)
    if code_ref != 0 or count_ref < 10:
        print(f"ERROR: Real reference run failed with exit code {code_ref}, tests {count_ref}", file=sys.stderr)
        sys.exit(1)

    # 2. Failure run with deliberately failing solution
    failing_content = 'def find: "wrong";\n'
    code_fail, count_fail, _ = run_isolated_suite(root, custom_solution_content=failing_content)
    if code_fail == 0:
        print("ERROR: Failing reference did not return non-zero exit code!", file=sys.stderr)
        sys.exit(1)

    hash_after = hash_file(stub_file)
    if hash_before != hash_after:
        print("ERROR: Learner stub file hash changed after run!", file=sys.stderr)
        sys.exit(1)

    print(f"Isolated runner verified successfully. Real tests passed: {count_ref}, failing run rejected, hashes invariant.")

if __name__ == "__main__":
    main()
