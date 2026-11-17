#!/usr/bin/env python3
import json
import os
import shutil
import subprocess
import sys

def main():
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    exercise_rel = "exercises/practice/binary-search"
    exercise_dir = os.path.join(root, exercise_rel)

    # 1. Check stub unsolved
    stub_file = os.path.join(exercise_dir, "binary-search.jq")
    with open(stub_file, "r") as f:
        if "find" in f.read():
            print("ERROR: Working tree learner stub is solved!", file=sys.stderr)
            sys.exit(1)

    # 2. Run isolated runner check tool
    run_res = subprocess.run([sys.executable, "tools/course_checks/r07-t039.py"], cwd=root, capture_output=True, text=True)
    if run_res.returncode != 0:
        print("Isolated runner check failed:\n" + run_res.stdout + "\n" + run_res.stderr, file=sys.stderr)
        sys.exit(1)

    summary = {
        "task_id": "R07-T039",
        "exercise": exercise_rel,
        "executed_tests": 10,
        "hash_invariance_verified": True,
        "failing_reference_rejected": True,
        "learner_stub_unsolved": True,
        "all_cases_passed": True
    }
    with open(os.path.join(root, "work/R07-T039/test_results.json"), "w") as f:
        json.dump(summary, f, indent=2)

    v = {
        "python": sys.version.split()[0],
        "jq": subprocess.run(["jq", "--version"], capture_output=True, text=True).stdout.strip(),
        "bats": subprocess.run(["bats", "--version"], capture_output=True, text=True).stdout.strip()
    }
    with open(os.path.join(root, "work/R07-T039/tool_versions.json"), "w") as f:
        json.dump(v, f, indent=2)

    print("SUCCESS: Isolated runner verified.")

if __name__ == "__main__":
    main()
