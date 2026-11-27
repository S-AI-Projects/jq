#!/usr/bin/env python3
import json
import os
import shutil
import subprocess
import sys
import tempfile

def main():
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    exercise_rel = "exercises/practice/luhn"
    exercise_dir = os.path.join(root, exercise_rel)

    # 1. Check stub unsolved
    stub_file = os.path.join(exercise_dir, "luhn.jq")
    with open(stub_file, "r") as f:
        if "select" in f.read() or "explode" in f.read():
            print("ERROR: Working tree learner stub is solved!", file=sys.stderr)
            sys.exit(1)

    # 2. Run metadata validator tool
    val_res = subprocess.run([sys.executable, "tools/course_checks/r07-t038.py"], cwd=root, capture_output=True, text=True)
    if val_res.returncode != 0:
        print("Metadata validation check failed:\n" + val_res.stdout + "\n" + val_res.stderr, file=sys.stderr)
        sys.exit(1)

    # 3. Run test against reference in temp copy
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_exercise = os.path.join(tmpdir, exercise_rel)
        os.makedirs(os.path.dirname(tmp_exercise), exist_ok=True)
        shutil.copytree(exercise_dir, tmp_exercise)
        shutil.copytree(os.path.join(root, "bin"), os.path.join(tmpdir, "bin"))

        example_src = os.path.join(tmp_exercise, ".meta/example.jq")
        target_solution = os.path.join(tmp_exercise, "luhn.jq")
        shutil.copyfile(example_src, target_solution)

        res = subprocess.run(["./bin/validate_one_exercise", exercise_rel], cwd=tmpdir, capture_output=True, text=True)
        if res.returncode != 0:
            print("Validation failed in temp copy:\n" + res.stdout + "\n" + res.stderr, file=sys.stderr)
            sys.exit(res.returncode)

        tap_lines = [l for l in res.stdout.splitlines() if l.startswith("ok ")]
        if len(tap_lines) < 10:
            print(f"ERROR: Expected at least 10 passing tests, got {len(tap_lines)}", file=sys.stderr)
            sys.exit(1)

    os.makedirs(os.path.join(root, "work/R07-T038"), exist_ok=True)
    summary = {
        "task_id": "R07-T038",
        "exercise": exercise_rel,
        "executed_tests": len(tap_lines),
        "metadata_fixtures_verified": True,
        "learner_stub_unsolved": True,
        "all_cases_passed": True
    }
    with open(os.path.join(root, "work/R07-T038/test_results.json"), "w") as f:
        json.dump(summary, f, indent=2)

    v = {
        "python": sys.version.split()[0],
        "jq": subprocess.run(["jq", "--version"], capture_output=True, text=True).stdout.strip(),
        "bats": subprocess.run(["bats", "--version"], capture_output=True, text=True).stdout.strip()
    }
    with open(os.path.join(root, "work/R07-T038/tool_versions.json"), "w") as f:
        json.dump(v, f, indent=2)

    print(f"SUCCESS: {len(tap_lines)} tests passed, metadata fixtures verified.")

if __name__ == "__main__":
    main()
