#!/usr/bin/env python3
"""Automated verification check for R07-T011 (Hamming canonical-case rationale)."""

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib


def hash_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()


def main():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    exercise_rel = "exercises/practice/hamming"
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
    if "explode" in stub_content or "transpose" in stub_content:
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

    if len(included) != 9 or len(excluded) != 6:
        print(f"ERROR: Expected 9 included and 6 excluded cases, got {len(included)} and {len(excluded)}", file=sys.stderr)
        sys.exit(1)

    target_uuids = [
        "919f8ef0-b767-4d1b-8516-6379d07fcb28",
        "8a2d4ed0-ead5-4fdd-924d-27c4cf56e60e",
        "5dce058b-28d4-4ca7-aa64-adfe4e17784c"
    ]
    for uid in target_uuids:
        if uid not in toml_data:
            print(f"ERROR: UUID {uid} missing in tests.toml", file=sys.stderr)
            sys.exit(1)
        comment = toml_data[uid].get("comment", "")
        if not comment or ("superseded" not in comment.lower() and "reimplement" not in comment.lower()):
            print(f"ERROR: UUID {uid} missing detailed rationale comment in tests.toml", file=sys.stderr)
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
        if len(tap_ok) != 9:
            print(f"ERROR: Expected 9 executed passing tests, got {len(tap_ok)}", file=sys.stderr)
            sys.exit(1)

        # Check named cases
        named_cases = ["empty strands", "single letter identical strands", "single letter different strands"]
        for nc in named_cases:
            if not any(nc in l for l in tap_ok):
                print(f"ERROR: Named case '{nc}' not found in executed tests", file=sys.stderr)
                sys.exit(1)

    # Verify working tree was not modified
    stub_hash_after = hash_file(stub_path)
    if stub_hash_before != stub_hash_after:
        print("ERROR: Working tree learner stub was altered during check!", file=sys.stderr)
        sys.exit(1)

    # 4. Save results and tool versions
    work_dir = os.path.join(repo_root, "work/R07-T011")
    os.makedirs(work_dir, exist_ok=True)

    summary = {
        "task_id": "R07-T011",
        "exercise": exercise_rel,
        "total_canonical_cases": total_cases,
        "included_cases": len(included),
        "excluded_cases": len(excluded),
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

    print(f"SUCCESS: R07-T011 verified. {len(tap_ok)} tests executed successfully. Rationale documented and confirmed.")


if __name__ == "__main__":
    main()
