#!/usr/bin/env python3
"""
Automated verification check for R07-T006:
Compare two approaches for nucleotide-count in jq.
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


def run_tests_for_solution(repo_root, exercise_rel, solution_path):
    exercise_dir = os.path.join(repo_root, exercise_rel)
    with open(os.path.join(exercise_dir, ".meta/config.json")) as f:
        cfg = json.load(f)
    example_rel = cfg["files"]["example"][0]

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_exercise = os.path.join(tmpdir, exercise_rel)
        os.makedirs(os.path.dirname(tmp_exercise), exist_ok=True)
        shutil.copytree(exercise_dir, tmp_exercise)
        shutil.copytree(os.path.join(repo_root, "bin"), os.path.join(tmpdir, "bin"))

        # Overwrite example file with the target solution to test
        shutil.copyfile(solution_path, os.path.join(tmp_exercise, example_rel))

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
            print(f"ERROR: Solution {solution_path} failed tests:\n" + res.stdout + "\n" + res.stderr, file=sys.stderr)
            sys.exit(1)

        tap_ok = [l for l in res.stdout.splitlines() if l.startswith("ok ")]
        return tap_ok


def main():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    exercise_rel = "exercises/practice/nucleotide-count"
    exercise_dir = os.path.join(repo_root, exercise_rel)

    config_path = os.path.join(exercise_dir, ".meta/config.json")
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    stub_rel = cfg["files"]["solution"][0]
    example_rel = cfg["files"]["example"][0]

    stub_path = os.path.join(exercise_dir, stub_rel)
    with open(stub_path, "r", encoding="utf-8") as f:
        stub_content = f.read()

    # 1. Assert learner stub is still unsolved
    if "reduce" in stub_content or "split" in stub_content:
        print("ERROR: Working tree learner stub is solved!", file=sys.stderr)
        sys.exit(1)

    stub_hash_before = hash_file(stub_path)

    # 2. Test Approach 1: Original reference implementation
    ref_path = os.path.join(exercise_dir, example_rel)
    ref_ok = run_tests_for_solution(repo_root, exercise_rel, ref_path)
    if len(ref_ok) != 5:
        print(f"ERROR: Expected 5 tests passed for reference, got {len(ref_ok)}", file=sys.stderr)
        sys.exit(1)

    # 3. Test Approach 2: Experimental alternative implementation
    alt_path = os.path.join(repo_root, "work/R07-T006/alternative.jq")
    alt_ok = run_tests_for_solution(repo_root, exercise_rel, alt_path)
    if len(alt_ok) != 5:
        print(f"ERROR: Expected 5 tests passed for alternative, got {len(alt_ok)}", file=sys.stderr)
        sys.exit(1)

    named_cases = [
        "empty strand",
        "can count one nucleotide in single-character input",
        "strand with repeated nucleotide"
    ]
    for nc in named_cases:
        if not any(nc in l for l in ref_ok):
            print(f"ERROR: Named case '{nc}' missing in reference test results", file=sys.stderr)
            sys.exit(1)
        if not any(nc in l for l in alt_ok):
            print(f"ERROR: Named case '{nc}' missing in alternative test results", file=sys.stderr)
            sys.exit(1)

    # 4. Verify working tree stub was not modified
    stub_hash_after = hash_file(stub_path)
    if stub_hash_before != stub_hash_after:
        print("ERROR: Working tree learner stub was altered during check!", file=sys.stderr)
        sys.exit(1)

    # 5. Save results and tool versions
    work_dir = os.path.join(repo_root, "work/R07-T006")
    os.makedirs(work_dir, exist_ok=True)

    summary = {
        "task_id": "R07-T006",
        "exercise": exercise_rel,
        "approach_1": "Single-pass streaming reduce over exploded characters",
        "approach_2": "Upfront regex validation followed by multi-pass character filtering",
        "reference_tests_passed": len(ref_ok),
        "alternative_tests_passed": len(alt_ok),
        "named_cases_passed": named_cases,
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

    print(f"SUCCESS: R07-T006 verified. Both approaches passed 5/5 tests including all named cases.")


if __name__ == "__main__":
    main()
