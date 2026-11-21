#!/usr/bin/env python3
"""
Automated verification check for R07-T010:
Contract cases and decision table for resistor-color-trio.
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


def main():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    exercise_rel = "exercises/practice/resistor-color-trio"
    exercise_dir = os.path.join(repo_root, exercise_rel)

    config_path = os.path.join(exercise_dir, ".meta/config.json")
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    stub_rel = cfg["files"]["solution"][0]
    test_rel = cfg["files"]["test"][0]
    example_rel = cfg["files"]["example"][0]

    stub_path = os.path.join(exercise_dir, stub_rel)
    with open(stub_path, "r", encoding="utf-8") as f:
        stub_content = f.read()

    # 1. Assert learner stub is still unsolved
    if "labelled" in stub_content or "ohms" in stub_content:
        print("ERROR: Working tree learner stub is solved!", file=sys.stderr)
        sys.exit(1)

    stub_hash_before = hash_file(stub_path)

    # 2. Assert decision table cases against reference in scratch environment
    example_path = os.path.join(exercise_dir, example_rel)
    decision_table = [
        {
            "name": "Orange and orange and black",
            "input": {"colors": ["orange", "orange", "black"]},
            "expected": {"value": 33, "unit": "ohms"}
        },
        {
            "name": "Blue and grey and brown",
            "input": {"colors": ["blue", "grey", "brown"]},
            "expected": {"value": 680, "unit": "ohms"}
        }
    ]

    for entry in decision_table:
        res = subprocess.run(
            ["jq", "-c", "-f", example_path],
            input=json.dumps(entry["input"]),
            capture_output=True,
            text=True,
            check=True
        )
        actual = json.loads(res.stdout.strip())
        if actual != entry["expected"]:
            print(f"ERROR: Decision table mismatch for '{entry['name']}': expected {entry['expected']}, got {actual}", file=sys.stderr)
            sys.exit(1)

    # 3. Assert hints.md contains Decision Table
    hints_path = os.path.join(exercise_dir, ".docs/hints.md")
    with open(hints_path, "r", encoding="utf-8") as f:
        hints_content = f.read()

    if "Decision Table" not in hints_content or "orange" not in hints_content or "blue" not in hints_content:
        print("ERROR: hints.md is missing Decision Table / selected cases!", file=sys.stderr)
        sys.exit(1)

    # 4. Isolated test execution in temporary copy
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_exercise = os.path.join(tmpdir, exercise_rel)
        os.makedirs(os.path.dirname(tmp_exercise), exist_ok=True)
        shutil.copytree(exercise_dir, tmp_exercise)
        shutil.copytree(os.path.join(repo_root, "bin"), os.path.join(tmpdir, "bin"))

        env = os.environ.copy()
        env["PATH"] = f"/opt/homebrew/bin:{env.get('PATH', '')}"

        res = subprocess.run(
            ["./bin/validate_one_exercise", exercise_rel],
            cwd=tmpdir,
            capture_output=True,
            text=True,
            env=env
        )

        if res.returncode != 0:
            print("ERROR: Test execution failed in isolated environment:\n" + res.stdout + "\n" + res.stderr, file=sys.stderr)
            sys.exit(1)

        tap_ok = [l for l in res.stdout.splitlines() if l.startswith("ok ")]
        if len(tap_ok) != 10:
            print(f"ERROR: Expected 10 executed passing tests, got {len(tap_ok)}", file=sys.stderr)
            sys.exit(1)

        named_cases = ["Orange and orange and black", "Blue and grey and brown"]
        for nc in named_cases:
            if not any(nc in l for l in tap_ok):
                print(f"ERROR: Named case '{nc}' not found in executed tests", file=sys.stderr)
                sys.exit(1)

    # 5. Verify working tree stub was not modified
    stub_hash_after = hash_file(stub_path)
    if stub_hash_before != stub_hash_after:
        print("ERROR: Working tree learner stub was altered during check!", file=sys.stderr)
        sys.exit(1)

    # 6. Save results and tool versions
    work_dir = os.path.join(repo_root, "work/R07-T010")
    os.makedirs(work_dir, exist_ok=True)

    summary = {
        "task_id": "R07-T010",
        "exercise": exercise_rel,
        "decision_table_verified": True,
        "decision_table_entries": decision_table,
        "executed_tests": len(tap_ok),
        "named_cases_passed": named_cases,
        "learner_stub_unsolved": True,
        "all_assertions_passed": True
    }
    with open(os.path.join(work_dir, "test_results.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    jq_ver = subprocess.run(["jq", "--version"], capture_output=True, text=True).stdout.strip()
    bats_ver = subprocess.run(["bats", "--version"], capture_output=True, text=True, env=env).stdout.strip()
    versions = {
        "python": sys.version.split()[0],
        "jq": jq_ver,
        "bats": bats_ver
    }
    with open(os.path.join(work_dir, "tool_versions.json"), "w", encoding="utf-8") as f:
        json.dump(versions, f, indent=2)

    print(f"SUCCESS: R07-T010 verified. Decision table matched and 10 tests passed.")


if __name__ == "__main__":
    main()
