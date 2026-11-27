#!/usr/bin/env python3
import json
import os
import shutil
import statistics
import subprocess
import sys
import tempfile
import time

def main():
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    exercise_rel = "exercises/practice/robot-simulator"
    exercise_dir = os.path.join(root, exercise_rel)

    # 1. Check stub unsolved
    stub_file = os.path.join(exercise_dir, "robot-simulator.jq")
    with open(stub_file, "r") as f:
        if "turn" in f.read():
            print("ERROR: Working tree learner stub is solved!", file=sys.stderr)
            sys.exit(1)

    # 2. Validate reference in temp copy
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_exercise = os.path.join(tmpdir, exercise_rel)
        os.makedirs(os.path.dirname(tmp_exercise), exist_ok=True)
        shutil.copytree(exercise_dir, tmp_exercise)
        shutil.copytree(os.path.join(root, "bin"), os.path.join(tmpdir, "bin"))

        example_src = os.path.join(tmp_exercise, ".meta/example.jq")
        target_solution = os.path.join(tmp_exercise, "robot-simulator.jq")
        shutil.copyfile(example_src, target_solution)

        res = subprocess.run(["./bin/validate_one_exercise", exercise_rel], cwd=tmpdir, capture_output=True, text=True)
        if res.returncode != 0:
            print("Validation failed in temp copy:\n" + res.stdout + "\n" + res.stderr, file=sys.stderr)
            sys.exit(res.returncode)

        tap_lines = [l for l in res.stdout.splitlines() if l.startswith("ok ")]
        if len(tap_lines) < 18:
            print(f"ERROR: Expected at least 18 passing tests, got {len(tap_lines)}", file=sys.stderr)
            sys.exit(1)

    # 3. Empirical complexity measurements on 3 valid input sizes with 5 repetitions
    example_path = os.path.join(exercise_dir, ".meta/example.jq")
    sizes = {
        "size_1": {"instructions": "R", "robot": {"direction": "north", "position": {"x": 0, "y": 0}}},
        "size_5": {"instructions": "LAAAR", "robot": {"direction": "north", "position": {"x": 0, "y": 0}}},
        "size_20": {"instructions": "RAALAAAARAALAAAARAAL", "robot": {"direction": "north", "position": {"x": 0, "y": 0}}}
    }
    timings = {}
    for s_name, payload in sizes.items():
        runs = []
        for _ in range(5):
            t0 = time.perf_counter()
            p = subprocess.run(["jq", "-f", example_path], input=json.dumps(payload), capture_output=True, text=True)
            t1 = time.perf_counter()
            if p.returncode != 0:
                print(f"Execution failed on {s_name}: " + p.stderr, file=sys.stderr)
                sys.exit(1)
            runs.append(t1 - t0)
        timings[s_name] = {
            "repetitions": 5,
            "median_seconds": statistics.median(runs),
            "all_runs": runs
        }

    os.makedirs(os.path.join(root, "work/R07-T035"), exist_ok=True)
    summary = {
        "task_id": "R07-T035",
        "exercise": exercise_rel,
        "executed_tests": len(tap_lines),
        "measurements": timings,
        "learner_stub_unsolved": True,
        "all_cases_passed": True
    }
    with open(os.path.join(root, "work/R07-T035/test_results.json"), "w") as f:
        json.dump(summary, f, indent=2)

    v = {
        "python": sys.version.split()[0],
        "jq": subprocess.run(["jq", "--version"], capture_output=True, text=True).stdout.strip(),
        "bats": subprocess.run(["bats", "--version"], capture_output=True, text=True).stdout.strip()
    }
    with open(os.path.join(root, "work/R07-T035/tool_versions.json"), "w") as f:
        json.dump(v, f, indent=2)

    print(f"SUCCESS: {len(tap_lines)} tests passed, empirical timings recorded.")

if __name__ == "__main__":
    main()
