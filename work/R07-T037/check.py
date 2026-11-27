#!/usr/bin/env python3
import json
import os
import shutil
import subprocess
import sys
import tempfile

def main():
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    exercise_rel = "exercises/practice/zebra-puzzle"
    exercise_dir = os.path.join(root, exercise_rel)

    # 1. Check stub unsolved
    stub_file = os.path.join(exercise_dir, "zebra-puzzle.jq")
    with open(stub_file, "r") as f:
        content = f.read()
        if "rightOf" in content or "solveForColour" in content:
            print("ERROR: Working tree learner stub is solved!", file=sys.stderr)
            sys.exit(1)

    # 2. Check hints.md guidance and content
    hints_path = os.path.join(exercise_dir, ".docs/hints.md")
    if not os.path.isfile(hints_path):
        print("ERROR: Missing hints.md!", file=sys.stderr)
        sys.exit(1)
    with open(hints_path, "r") as f:
        hints_content = f.read()
    if "rightOf" not in hints_content:
        print("ERROR: hints.md must name construct rightOf!", file=sys.stderr)
        sys.exit(1)
    if "empty" not in hints_content:
        print("ERROR: hints.md must explain stream pruning with empty!", file=sys.stderr)
        sys.exit(1)

    # 3. Assert Micro-Example 1
    p1_bool = subprocess.run(
        ["jq", "-n", "def rightOf($house): . == $house + 1; 4 | rightOf(3)"],
        capture_output=True, text=True
    )
    if p1_bool.returncode != 0 or p1_bool.stdout.strip() != "true":
        print(f"ERROR: Micro-example 1 bool failed: {p1_bool.stdout} {p1_bool.stderr}", file=sys.stderr)
        sys.exit(1)

    p1_filter = subprocess.run(
        ["jq", "-n", 'def rightOf($house): . == $house + 1; 4 | if rightOf(3) then "valid" else empty end'],
        capture_output=True, text=True
    )
    if p1_filter.returncode != 0 or p1_filter.stdout.strip() != '"valid"':
        print(f"ERROR: Micro-example 1 filter failed: {p1_filter.stdout} {p1_filter.stderr}", file=sys.stderr)
        sys.exit(1)

    # 4. Assert Micro-Example 2
    p2_bool = subprocess.run(
        ["jq", "-n", "def rightOf($house): . == $house + 1; 2 | rightOf(3)"],
        capture_output=True, text=True
    )
    if p2_bool.returncode != 0 or p2_bool.stdout.strip() != "false":
        print(f"ERROR: Micro-example 2 bool failed: {p2_bool.stdout} {p2_bool.stderr}", file=sys.stderr)
        sys.exit(1)

    p2_filter = subprocess.run(
        ["jq", "-n", 'def rightOf($house): . == $house + 1; 2 | if rightOf(3) then "valid" else empty end'],
        capture_output=True, text=True
    )
    if p2_filter.returncode != 0 or p2_filter.stdout.strip() != "":
        print(f"ERROR: Micro-example 2 filter should yield empty stream, got: {p2_filter.stdout}", file=sys.stderr)
        sys.exit(1)

    # 5. Run test against reference in temp copy
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_exercise = os.path.join(tmpdir, exercise_rel)
        os.makedirs(os.path.dirname(tmp_exercise), exist_ok=True)
        shutil.copytree(exercise_dir, tmp_exercise)
        shutil.copytree(os.path.join(root, "bin"), os.path.join(tmpdir, "bin"))

        example_src = os.path.join(tmp_exercise, ".meta/example.jq")
        target_solution = os.path.join(tmp_exercise, "zebra-puzzle.jq")
        shutil.copyfile(example_src, target_solution)

        res = subprocess.run(["./bin/validate_one_exercise", exercise_rel], cwd=tmpdir, capture_output=True, text=True)
        if res.returncode != 0:
            print("Validation failed in temp copy:\n" + res.stdout + "\n" + res.stderr, file=sys.stderr)
            sys.exit(res.returncode)

        tap_lines = [l for l in res.stdout.splitlines() if l.startswith("ok ")]
        if len(tap_lines) < 2:
            print(f"ERROR: Expected at least 2 passing tests, got {len(tap_lines)}", file=sys.stderr)
            sys.exit(1)

    os.makedirs(os.path.join(root, "work/R07-T037"), exist_ok=True)
    summary = {
        "task_id": "R07-T037",
        "exercise": exercise_rel,
        "executed_tests": len(tap_lines),
        "micro_examples_verified": True,
        "learner_stub_unsolved": True,
        "all_cases_passed": True
    }
    with open(os.path.join(root, "work/R07-T037/test_results.json"), "w") as f:
        json.dump(summary, f, indent=2)

    v = {
        "python": sys.version.split()[0],
        "jq": subprocess.run(["jq", "--version"], capture_output=True, text=True).stdout.strip(),
        "bats": subprocess.run(["bats", "--version"], capture_output=True, text=True).stdout.strip()
    }
    with open(os.path.join(root, "work/R07-T037/tool_versions.json"), "w") as f:
        json.dump(v, f, indent=2)

    print(f"SUCCESS: {len(tap_lines)} tests passed, micro-examples and guidance verified.")

if __name__ == "__main__":
    main()
