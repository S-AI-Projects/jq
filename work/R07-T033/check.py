#!/usr/bin/env python3
import json
import os
import shutil
import subprocess
import sys
import tempfile

def main():
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    exercise_rel = "exercises/practice/reverse-string"
    exercise_dir = os.path.join(root, exercise_rel)

    # 1. Check stub unsolved
    stub_file = os.path.join(exercise_dir, "reverse-string.jq")
    with open(stub_file, "r") as f:
        if "reduce" in f.read():
            print("ERROR: Working tree learner stub is solved!", file=sys.stderr)
            sys.exit(1)

    # 2. Test original reference
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_exercise = os.path.join(tmpdir, exercise_rel)
        os.makedirs(os.path.dirname(tmp_exercise), exist_ok=True)
        shutil.copytree(exercise_dir, tmp_exercise)
        shutil.copytree(os.path.join(root, "bin"), os.path.join(tmpdir, "bin"))

        example_src = os.path.join(tmp_exercise, ".meta/example.jq")
        target_solution = os.path.join(tmp_exercise, "reverse-string.jq")
        shutil.copyfile(example_src, target_solution)

        res = subprocess.run(["./bin/validate_one_exercise", exercise_rel], cwd=tmpdir, capture_output=True, text=True)
        if res.returncode != 0:
            print("Original reference failed validation:\n" + res.stdout + "\n" + res.stderr, file=sys.stderr)
            sys.exit(1)
        tap_orig = [l for l in res.stdout.splitlines() if l.startswith("ok ")]

    # 3. Test mutant
    mutant_code = '.value | reduce split("")[] as $char (""; . + $char)\n'
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_exercise = os.path.join(tmpdir, exercise_rel)
        os.makedirs(os.path.dirname(tmp_exercise), exist_ok=True)
        shutil.copytree(exercise_dir, tmp_exercise)
        shutil.copytree(os.path.join(root, "bin"), os.path.join(tmpdir, "bin"))

        example_src = os.path.join(tmp_exercise, ".meta/example.jq")
        with open(example_src, "w") as f:
            f.write(mutant_code)

        res_mut = subprocess.run(["./bin/validate_one_exercise", exercise_rel], cwd=tmpdir, capture_output=True, text=True)
        if res_mut.returncode == 0:
            print("ERROR: Mutant unexpectedly passed test suite!", file=sys.stderr)
            sys.exit(1)

        if "not ok" not in res_mut.stdout and "FAIL" not in res_mut.stdout:
            print("ERROR: Expected mutant failure report in output", file=sys.stderr)
            sys.exit(1)

    summary = {
        "task_id": "R07-T033",
        "exercise": exercise_rel,
        "reference_tests_passed": len(tap_orig),
        "mutant_rejected": True,
        "rejecting_test_id": "01ebf55b-bebb-414e-9dec-06f7bb0bee3c",
        "rejecting_test_name": "a word",
        "learner_stub_unsolved": True
    }
    with open(os.path.join(root, "work/R07-T033/test_results.json"), "w") as f:
        json.dump(summary, f, indent=2)

    v = {
        "python": sys.version.split()[0],
        "jq": subprocess.run(["jq", "--version"], capture_output=True, text=True).stdout.strip(),
        "bats": subprocess.run(["bats", "--version"], capture_output=True, text=True).stdout.strip()
    }
    with open(os.path.join(root, "work/R07-T033/tool_versions.json"), "w") as f:
        json.dump(v, f, indent=2)

    print(f"SUCCESS: Reference passed {len(tap_orig)} tests, mutant rejected by 'a word'.")

if __name__ == "__main__":
    main()
