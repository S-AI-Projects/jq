#!/usr/bin/env python3
"""
Automated verification check for R07-T001:
Review canonical case decisions for all-your-base.
"""

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import tomllib


def hash_file(filepath):
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        hasher.update(f.read())
    return hasher.hexdigest()


def main():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    exercise_rel = "exercises/practice/all-your-base"
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
    if "to_decimal" in stub_content or "to_base" in stub_content:
        print("ERROR: Working tree learner stub is solved!", file=sys.stderr)
        sys.exit(1)

    stub_hash_before = hash_file(stub_path)

    # 2. Assert tests.toml parsing and rationale verification
    toml_path = os.path.join(exercise_dir, ".meta/tests.toml")
    with open(toml_path, "rb") as f:
        toml_data = tomllib.load(f)

    total_cases = len(toml_data)
    included = [k for k, v in toml_data.items() if v.get("include", True)]
    excluded = [k for k, v in toml_data.items() if not v.get("include", True)]

    if len(included) != 21 or len(excluded) != 0:
        print(f"ERROR: Expected 21 included and 0 excluded cases, got {len(included)} and {len(excluded)}", file=sys.stderr)
        sys.exit(1)

    target_uuids = [
        "5ce422f9-7a4b-4f44-ad29-49c67cb32d2c",
        "0cc3fea8-bb79-46ac-a2ab-5a2c93051033",
        "f12db0f9-0d3d-42c2-b3ba-e38cb375a2b8"
    ]
    for uid in target_uuids:
        if uid not in toml_data:
            print(f"ERROR: UUID {uid} missing in tests.toml", file=sys.stderr)
            sys.exit(1)
        comment = toml_data[uid].get("comment", "")
        if not comment:
            print(f"ERROR: UUID {uid} missing rationale comment in tests.toml", file=sys.stderr)
            sys.exit(1)

    # 3. Isolated test execution in temporary copy
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
        if len(tap_ok) != 21:
            print(f"ERROR: Expected 21 executed passing tests, got {len(tap_ok)}", file=sys.stderr)
            sys.exit(1)

        named_cases = [
            "single bit one to decimal",
            "binary to single decimal",
            "single decimal to binary"
        ]
        for nc in named_cases:
            if not any(nc in l for l in tap_ok):
                print(f"ERROR: Named case '{nc}' not found in executed tests", file=sys.stderr)
                sys.exit(1)

    # 4. Verify working tree was not modified
    stub_hash_after = hash_file(stub_path)
    if stub_hash_before != stub_hash_after:
        print("ERROR: Working tree learner stub was altered during check!", file=sys.stderr)
        sys.exit(1)

    # 5. Save results and tool versions
    work_dir = os.path.join(repo_root, "work/R07-T001")
    os.makedirs(work_dir, exist_ok=True)

    summary = {
        "task_id": "R07-T001",
        "exercise": exercise_rel,
        "total_canonical_cases": total_cases,
        "included_cases_before": 21,
        "included_cases_after": len(included),
        "excluded_cases_before": 0,
        "excluded_cases_after": len(excluded),
        "target_uuids_verified": target_uuids,
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

    print(f"SUCCESS: R07-T001 verified. {len(tap_ok)} tests executed successfully. Rationale documented and confirmed.")


if __name__ == "__main__":
    main()
