#!/usr/bin/env python3
import json
import os
import shutil
import subprocess
import sys
import tempfile

def main():
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    exercise_rel = "exercises/practice/gigasecond"
    exercise_dir = os.path.join(root, exercise_rel)

    # 1. Check stub unsolved
    stub_file = os.path.join(exercise_dir, "gigasecond.jq")
    with open(stub_file, "r") as f:
        if "fromdateiso8601" in f.read() or "strptime" in f.read():
            print("ERROR: Working tree learner stub is solved!", file=sys.stderr)
            sys.exit(1)

    # 2. Test Approach 1 (Reference)
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_exercise = os.path.join(tmpdir, exercise_rel)
        os.makedirs(os.path.dirname(tmp_exercise), exist_ok=True)
        shutil.copytree(exercise_dir, tmp_exercise)
        shutil.copytree(os.path.join(root, "bin"), os.path.join(tmpdir, "bin"))

        example_src = os.path.join(tmp_exercise, ".meta/example.jq")
        target_solution = os.path.join(tmp_exercise, "gigasecond.jq")
        shutil.copyfile(example_src, target_solution)

        res1 = subprocess.run(["./bin/validate_one_exercise", exercise_rel], cwd=tmpdir, capture_output=True, text=True)
        if res1.returncode != 0:
            print("Reference validation failed:\n" + res1.stdout + "\n" + res1.stderr, file=sys.stderr)
            sys.exit(1)
        tap1 = [l for l in res1.stdout.splitlines() if l.startswith("ok ")]

    # 3. Test Approach 2 (Alternative)
    alt_code = """1000000000 as $Gigasecond
| .moment
| (if contains("T") then . else . + "T00:00:00" end)
| strptime("%Y-%m-%dT%H:%M:%S")
| mktime + $Gigasecond
| strftime("%Y-%m-%dT%H:%M:%S")
"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_exercise = os.path.join(tmpdir, exercise_rel)
        os.makedirs(os.path.dirname(tmp_exercise), exist_ok=True)
        shutil.copytree(exercise_dir, tmp_exercise)
        shutil.copytree(os.path.join(root, "bin"), os.path.join(tmpdir, "bin"))

        target_solution = os.path.join(tmp_exercise, "gigasecond.jq")
        with open(target_solution, "w") as f:
            f.write(alt_code)

        res2 = subprocess.run(["./bin/validate_one_exercise", exercise_rel], cwd=tmpdir, capture_output=True, text=True)
        if res2.returncode != 0:
            print("Alternative validation failed:\n" + res2.stdout + "\n" + res2.stderr, file=sys.stderr)
            sys.exit(1)
        tap2 = [l for l in res2.stdout.splitlines() if l.startswith("ok ")]

    if len(tap1) != len(tap2) or len(tap1) < 5:
        print(f"ERROR: Test count mismatch: orig={len(tap1)}, alt={len(tap2)}", file=sys.stderr)
        sys.exit(1)

    summary = {
        "task_id": "R07-T036",
        "exercise": exercise_rel,
        "approach1_tests_passed": len(tap1),
        "approach2_tests_passed": len(tap2),
        "both_approaches_valid": True,
        "learner_stub_unsolved": True
    }
    with open(os.path.join(root, "work/R07-T036/test_results.json"), "w") as f:
        json.dump(summary, f, indent=2)

    v = {
        "python": sys.version.split()[0],
        "jq": subprocess.run(["jq", "--version"], capture_output=True, text=True).stdout.strip(),
        "bats": subprocess.run(["bats", "--version"], capture_output=True, text=True).stdout.strip()
    }
    with open(os.path.join(root, "work/R07-T036/tool_versions.json"), "w") as f:
        json.dump(v, f, indent=2)

    print(f"SUCCESS: Both approaches passed {len(tap1)} tests.")

if __name__ == "__main__":
    main()
