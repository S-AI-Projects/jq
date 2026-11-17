#!/usr/bin/env python3
import json
import os
import shutil
import subprocess
import sys
import tempfile
import tomllib

def main():
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    exercise_rel = "exercises/practice/flatten-array"
    exercise_dir = os.path.join(root, exercise_rel)

    # 1. Check stub unsolved
    stub_file = os.path.join(exercise_dir, "flatten-array.jq")
    with open(stub_file, "r") as f:
        if "map(select" in f.read():
            print("ERROR: Working tree learner stub is solved!", file=sys.stderr)
            sys.exit(1)

    # 2. Check toml
    toml_path = os.path.join(exercise_dir, ".meta/tests.toml")
    with open(toml_path, "rb") as f:
        data = tomllib.load(f)

    included, excluded = 0, 0
    target_uuids = [
        "c6cf26de-8ccd-4410-84bd-b9efd88fd2bc",
        "382c5242-587e-4577-b8ce-a5fb51e385a1",
        "ef1d4790-1b1e-4939-a179-51ace0829dbd"
    ]
    rationales = {}
    for k, v in data.items():
        if isinstance(v, dict):
            if v.get("include", True):
                included += 1
            else:
                excluded += 1
            if k in target_uuids:
                if "comment" not in v:
                    print(f"ERROR: Missing comment rationale for UUID {k}", file=sys.stderr)
                    sys.exit(1)
                rationales[k] = v["comment"]

    if included != 11 or excluded != 4:
        print(f"ERROR: Expected 11 included, 4 excluded, got {included} inc, {excluded} exc", file=sys.stderr)
        sys.exit(1)

    # 3. Test in temp copy
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_exercise = os.path.join(tmpdir, exercise_rel)
        os.makedirs(os.path.dirname(tmp_exercise), exist_ok=True)
        shutil.copytree(exercise_dir, tmp_exercise)
        shutil.copytree(os.path.join(root, "bin"), os.path.join(tmpdir, "bin"))

        example_src = os.path.join(tmp_exercise, ".meta/example.jq")
        target_solution = os.path.join(tmp_exercise, "flatten-array.jq")
        shutil.copyfile(example_src, target_solution)

        res = subprocess.run(["./bin/validate_one_exercise", exercise_rel], cwd=tmpdir, capture_output=True, text=True)
        if res.returncode != 0:
            print("Validation failed in temp copy:\n" + res.stdout + "\n" + res.stderr, file=sys.stderr)
            sys.exit(res.returncode)

        tap_lines = [l for l in res.stdout.splitlines() if l.startswith("ok ")]
        if len(tap_lines) < 11:
            print(f"ERROR: Expected at least 11 passing tests, got {len(tap_lines)}", file=sys.stderr)
            sys.exit(1)

    summary = {
        "task_id": "R07-T031",
        "exercise": exercise_rel,
        "included_cases": included,
        "excluded_cases": excluded,
        "executed_tests": len(tap_lines),
        "target_rationales": rationales,
        "learner_stub_unsolved": True,
        "all_cases_passed": True
    }
    with open(os.path.join(root, "work/R07-T031/test_results.json"), "w") as f:
        json.dump(summary, f, indent=2)

    v = {
        "python": sys.version.split()[0],
        "jq": subprocess.run(["jq", "--version"], capture_output=True, text=True).stdout.strip(),
        "bats": subprocess.run(["bats", "--version"], capture_output=True, text=True).stdout.strip()
    }
    with open(os.path.join(root, "work/R07-T031/tool_versions.json"), "w") as f:
        json.dump(v, f, indent=2)

    print(f"SUCCESS: {len(tap_lines)} tests passed.")

if __name__ == "__main__":
    main()
