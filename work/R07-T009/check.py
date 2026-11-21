#!/usr/bin/env python3
"""
Automated verification check for R07-T009:
Run pig-latin without altering its learner files.
"""

import hashlib
import json
import os
import shutil
import subprocess
import sys


def hash_file(filepath):
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        hasher.update(f.read())
    return hasher.hexdigest()


def main():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    exercise_rel = "exercises/practice/pig-latin"
    exercise_dir = os.path.join(repo_root, exercise_rel)

    config_path = os.path.join(exercise_dir, ".meta/config.json")
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    stub_rel = cfg["files"]["solution"][0]
    stub_path = os.path.join(exercise_dir, stub_rel)

    with open(stub_path, "r", encoding="utf-8") as f:
        stub_content = f.read()

    # 1. Assert learner stub is still unsolved
    if "translate" in stub_content or "qu" in stub_content:
        print("ERROR: Working tree learner stub is solved!", file=sys.stderr)
        sys.exit(1)

    stub_hash_before = hash_file(stub_path)

    # 2. Run tools/course_checks/r07-t009.py
    run_tool = subprocess.run(
        [sys.executable, "tools/course_checks/r07-t009.py"],
        cwd=repo_root,
        capture_output=True,
        text=True
    )
    if run_tool.returncode != 0:
        print("ERROR: tools/course_checks/r07-t009.py failed:\n" + run_tool.stdout + "\n" + run_tool.stderr, file=sys.stderr)
        sys.exit(1)

    # 3. Assert named cases passed in real runner output
    # Import isolated runner directly for detailed telemetry
    sys.path.insert(0, os.path.join(repo_root, "tools/course_checks"))
    import importlib
    r07_t009 = importlib.import_module("r07-t009")

    real_res = r07_t009.run_isolated(repo_root)
    if real_res["passed_tests"] != 23:
        print(f"ERROR: Expected 23 executed tests, got {real_res['passed_tests']}", file=sys.stderr)
        sys.exit(1)

    named_cases = [
        "ay is added to words that start with vowels:word beginning with a",
        "ay is added to words that start with vowels:word beginning with e",
        "ay is added to words that start with vowels:word beginning with i"
    ]
    for nc in named_cases:
        if not any(nc in l for l in real_res["tap_ok"]):
            print(f"ERROR: Named case '{nc}' not found in executed tests", file=sys.stderr)
            sys.exit(1)

    # 4. Assert deliberate failure is caught and rejected
    fail_res = r07_t009.run_isolated(repo_root, mutate_solution='"wrong_output"')
    if fail_res["returncode"] == 0:
        print("ERROR: Deliberate failure mutant was not rejected!", file=sys.stderr)
        sys.exit(1)

    # 5. Assert empty tests is caught
    empty_res = r07_t009.run_isolated(repo_root, empty_tests=True)
    if empty_res["passed_tests"] > 0:
        print("ERROR: Empty test run produced non-zero passed tests!", file=sys.stderr)
        sys.exit(1)

    # 6. Verify working tree stub hash is invariant
    stub_hash_after = hash_file(stub_path)
    if stub_hash_before != stub_hash_after:
        print("ERROR: Working tree learner stub was altered during check!", file=sys.stderr)
        sys.exit(1)

    # 7. Save results and tool versions
    work_dir = os.path.join(repo_root, "work/R07-T009")
    os.makedirs(work_dir, exist_ok=True)

    summary = {
        "task_id": "R07-T009",
        "exercise": exercise_rel,
        "hash_invariance_verified": True,
        "sha256_stub_before": stub_hash_before,
        "sha256_stub_after": stub_hash_after,
        "real_reference_passed_tests": real_res["passed_tests"],
        "named_cases_passed": named_cases,
        "failing_mutant_rejected": True,
        "zero_test_detected": True,
        "learner_stub_unsolved": True,
        "all_assertions_passed": True
    }
    with open(os.path.join(work_dir, "test_results.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    jq_ver = subprocess.run(["jq", "--version"], capture_output=True, text=True).stdout.strip()
    env = os.environ.copy()
    env["PATH"] = f"/opt/homebrew/bin:{env.get('PATH', '')}"
    bats_ver = subprocess.run(["bats", "--version"], capture_output=True, text=True, env=env).stdout.strip()
    versions = {
        "python": sys.version.split()[0],
        "jq": jq_ver,
        "bats": bats_ver
    }
    with open(os.path.join(work_dir, "tool_versions.json"), "w", encoding="utf-8") as f:
        json.dump(versions, f, indent=2)

    print(f"SUCCESS: R07-T009 verified. 23 tests passed, mutant rejected, hash invariant verified.")


if __name__ == "__main__":
    main()
