#!/usr/bin/env python3
import json
import os
import shutil
import subprocess
import sys
import tempfile

def main():
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    exercise_rel = "exercises/practice/hello-world"
    exercise_dir = os.path.join(root, exercise_rel)

    # 1. Check stub unsolved
    stub_file = os.path.join(exercise_dir, "hello-world.jq")
    with open(stub_file, "r") as f:
        if "Hello, World!" in f.read():
            print("ERROR: Working tree learner stub is solved!", file=sys.stderr)
            sys.exit(1)

    # 2. Test reference in temp copy
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_exercise = os.path.join(tmpdir, exercise_rel)
        os.makedirs(os.path.dirname(tmp_exercise), exist_ok=True)
        shutil.copytree(exercise_dir, tmp_exercise)
        shutil.copytree(os.path.join(root, "bin"), os.path.join(tmpdir, "bin"))

        example_src = os.path.join(tmp_exercise, ".meta/example.jq")
        target_solution = os.path.join(tmp_exercise, "hello-world.jq")
        shutil.copyfile(example_src, target_solution)

        res = subprocess.run(["./bin/validate_one_exercise", exercise_rel], cwd=tmpdir, capture_output=True, text=True)
        if res.returncode != 0:
            print("Validation failed in temp copy:\n" + res.stdout + "\n" + res.stderr, file=sys.stderr)
            sys.exit(res.returncode)

        tap_lines = [l for l in res.stdout.splitlines() if l.startswith("ok ")]
        if len(tap_lines) < 1:
            print(f"ERROR: Expected at least 1 passing test, got {len(tap_lines)}", file=sys.stderr)
            sys.exit(1)

    # 3. Assert decision table contract
    example_path = os.path.join(exercise_dir, ".meta/example.jq")
    for test_input in ["null", "{}", '{"any": "value"}', '"text"']:
        p = subprocess.run(["jq", "-r", "-f", example_path], input=test_input, capture_output=True, text=True)
        if p.stdout.strip() != "Hello, World!":
            print(f"ERROR: Decision table mismatch on input {test_input}: got {p.stdout}", file=sys.stderr)
            sys.exit(1)

    summary = {
        "task_id": "R07-T040",
        "exercise": exercise_rel,
        "executed_tests": len(tap_lines),
        "decision_table_verified": True,
        "learner_stub_unsolved": True,
        "all_cases_passed": True
    }
    with open(os.path.join(root, "work/R07-T040/test_results.json"), "w") as f:
        json.dump(summary, f, indent=2)

    v = {
        "python": sys.version.split()[0],
        "jq": subprocess.run(["jq", "--version"], capture_output=True, text=True).stdout.strip(),
        "bats": subprocess.run(["bats", "--version"], capture_output=True, text=True).stdout.strip()
    }
    with open(os.path.join(root, "work/R07-T040/tool_versions.json"), "w") as f:
        json.dump(v, f, indent=2)

    print(f"SUCCESS: {len(tap_lines)} test passed, decision table verified.")

if __name__ == "__main__":
    main()
