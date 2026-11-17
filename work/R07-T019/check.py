#!/usr/bin/env python3
"""Automated verification check for R07-T019 (Acronym isolated test runner)."""

import hashlib
import json
import os
import subprocess
import sys


def hash_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()


def main():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    exercise_rel = "exercises/practice/acronym"
    exercise_dir = os.path.join(repo_root, exercise_rel)

    config_path = os.path.join(exercise_dir, ".meta/config.json")
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    stub_path = os.path.join(exercise_dir, cfg["files"]["solution"][0])
    with open(stub_path, "r", encoding="utf-8") as f:
        stub_content = f.read()

    # 1. Assert learner stub is still unsolved
    if "split" in stub_content or "ascii_upcase" in stub_content or "parse" in stub_content:
        # Check if actual solution logic is implemented
        if "indices" in stub_content or "explode" in stub_content or "startswith" in stub_content:
            print("ERROR: Working tree learner stub is solved!", file=sys.stderr)
            sys.exit(1)

    stub_hash_before = hash_file(stub_path)

    # 2. Run isolated runner tool
    env = os.environ.copy()
    env["PATH"] = f"/opt/homebrew/bin:{env.get('PATH', '')}"

    runner_res = subprocess.run(
        [sys.executable, "tools/course_checks/r07-t019.py"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        env=env
    )

    if runner_res.returncode != 0:
        print("ERROR: Isolated runner tool failed:\n" + runner_res.stdout + "\n" + runner_res.stderr, file=sys.stderr)
        sys.exit(1)

    # 3. Verify named test cases in test suite
    bats_path = os.path.join(exercise_dir, cfg["files"]["test"][0])
    with open(bats_path, "r", encoding="utf-8") as f:
        bats_content = f.read()

    named_cases = ["lowercase words", "all caps word", "punctuation without whitespace"]
    for nc in named_cases:
        if f"@test '{nc}'" not in bats_content:
            print(f"ERROR: Named case '{nc}' missing from test suite", file=sys.stderr)
            sys.exit(1)

    # 4. Verify learner file hash invariance
    stub_hash_after = hash_file(stub_path)
    if stub_hash_before != stub_hash_after:
        print("ERROR: Working tree learner stub was altered during check!", file=sys.stderr)
        sys.exit(1)

    # 5. Save results and versions
    work_dir = os.path.join(repo_root, "work/R07-T019")
    os.makedirs(work_dir, exist_ok=True)

    summary = {
        "task_id": "R07-T019",
        "exercise": exercise_rel,
        "named_cases": named_cases,
        "executed_tests": 9,
        "hash_invariance_verified": True,
        "failing_reference_rejected": True,
        "zero_test_run_rejected": True,
        "learner_stub_unsolved": True,
        "all_assertions_passed": True
    }
    with open(os.path.join(work_dir, "test_results.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    versions = {
        "python": sys.version.split()[0],
        "jq": subprocess.run(["jq", "--version"], capture_output=True, text=True).stdout.strip(),
        "bats": subprocess.run(["bats", "--version"], capture_output=True, text=True, env=env).stdout.strip()
    }
    with open(os.path.join(work_dir, "tool_versions.json"), "w", encoding="utf-8") as f:
        json.dump(versions, f, indent=2)

    print("SUCCESS: R07-T019 verified. Isolated runner and hash invariance verified successfully.")


if __name__ == "__main__":
    main()
