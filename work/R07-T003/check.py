#!/usr/bin/env python3
"""
Automated verification check for R07-T003:
Mutation analysis for kindergarten-garden.
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
    exercise_rel = "exercises/practice/kindergarten-garden"
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
    if "index" in stub_content or "diagram" in stub_content:
        print("ERROR: Working tree learner stub is solved!", file=sys.stderr)
        sys.exit(1)

    stub_hash_before = hash_file(stub_path)

    # 2. Test original reference implementation
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
            print("ERROR: Original reference failed:\n" + res.stdout + "\n" + res.stderr, file=sys.stderr)
            sys.exit(1)

        tap_ok = [l for l in res.stdout.splitlines() if l.startswith("ok ")]
        if len(tap_ok) != 17:
            print(f"ERROR: Expected 17 executed passing tests, got {len(tap_ok)}", file=sys.stderr)
            sys.exit(1)

        named_cases = [
            "partial garden:garden with single student",
            "partial garden:different garden with single student",
            "partial garden:garden with two students"
        ]
        for nc in named_cases:
            if not any(nc in l for l in tap_ok):
                print(f"ERROR: Named case '{nc}' not found in executed tests", file=sys.stderr)
                sys.exit(1)

    # 3. Test mutated reference implementation
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_exercise = os.path.join(tmpdir, exercise_rel)
        os.makedirs(os.path.dirname(tmp_exercise), exist_ok=True)
        shutil.copytree(exercise_dir, tmp_exercise)
        shutil.copytree(os.path.join(repo_root, "bin"), os.path.join(tmpdir, "bin"))

        # Mutate example.jq: change [offset*2:offset*2+2] to [offset:offset+2]
        mutant_file = os.path.join(tmp_exercise, example_rel)
        with open(mutant_file, "r", encoding="utf-8") as f:
            content = f.read()
        mutated_content = content.replace(".[$offset * 2:$offset * 2 + 2]", ".[$offset:$offset + 2]")
        with open(mutant_file, "w", encoding="utf-8") as f:
            f.write(mutated_content)

        env = os.environ.copy()
        env["PATH"] = f"/opt/homebrew/bin:{env.get('PATH', '')}"

        res_mutant = subprocess.run(
            ["./bin/validate_one_exercise", exercise_rel],
            cwd=tmpdir,
            capture_output=True,
            text=True,
            env=env
        )

        if res_mutant.returncode == 0:
            print("ERROR: Mutant was NOT rejected by the test suite!", file=sys.stderr)
            sys.exit(1)

        if "partial garden:garden with two students" not in res_mutant.stdout and "partial garden:garden with two students" not in res_mutant.stderr:
            print("ERROR: Rejecting test 'partial garden:garden with two students' was not triggered!", file=sys.stderr)
            sys.exit(1)

    # 4. Verify working tree was not modified
    stub_hash_after = hash_file(stub_path)
    if stub_hash_before != stub_hash_after:
        print("ERROR: Working tree learner stub was altered during check!", file=sys.stderr)
        sys.exit(1)

    # 5. Save results and tool versions
    work_dir = os.path.join(repo_root, "work/R07-T003")
    os.makedirs(work_dir, exist_ok=True)

    summary = {
        "task_id": "R07-T003",
        "exercise": exercise_rel,
        "original_tests_passed": len(tap_ok),
        "named_cases_passed": named_cases,
        "mutant_rejected": True,
        "rejecting_test": "partial garden:garden with two students",
        "rejecting_uuid": "c376fcc8-349c-446c-94b0-903947315757",
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

    print(f"SUCCESS: R07-T003 verified. Original passed 17 tests; mutant rejected by 'partial garden:garden with two students'.")


if __name__ == "__main__":
    main()
