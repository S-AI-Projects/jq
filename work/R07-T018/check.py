#!/usr/bin/env python3
"""Automated verification check for R07-T018 (Sieve maintenance metadata and path verification)."""

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile

import importlib.util

spec = importlib.util.spec_from_file_location(
    "r07_t018",
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../../tools/course_checks/r07-t018.py"))
)
r07_t018 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r07_t018)
validate_config = r07_t018.validate_config


def hash_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()


def main():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    exercise_rel = "exercises/practice/sieve"
    exercise_dir = os.path.join(repo_root, exercise_rel)

    config_path = os.path.join(exercise_dir, ".meta/config.json")
    with open(config_path, "r", encoding="utf-8") as f:
        real_cfg = json.load(f)

    stub_path = os.path.join(exercise_dir, real_cfg["files"]["solution"][0])
    with open(stub_path, "r", encoding="utf-8") as f:
        stub_content = f.read()

    # 1. Assert learner stub is still unsolved
    if "range" in stub_content or "sieve" in stub_content:
        # Check if actual solution logic is present
        if "del(" in stub_content or "map(" in stub_content:
            print("ERROR: Working tree learner stub is solved!", file=sys.stderr)
            sys.exit(1)

    stub_hash_before = hash_file(stub_path)

    # 2. Validate real metadata
    valid_real, msg_real = validate_config(exercise_dir)
    if not valid_real:
        print(f"ERROR: Real sieve config failed validation: {msg_real}", file=sys.stderr)
        sys.exit(1)

    # 3. Test deliberately invalid fixtures
    # Fixture A: missing reference
    bad_cfg_missing_ref = json.loads(json.dumps(real_cfg))
    bad_cfg_missing_ref["files"]["example"] = [".meta/nonexistent.jq"]
    valid_a, msg_a = validate_config(exercise_dir, bad_cfg_missing_ref)
    if valid_a or "does not exist" not in msg_a:
        print(f"ERROR: Missing reference fixture unexpectedly passed: {msg_a}", file=sys.stderr)
        sys.exit(1)

    # Fixture B: missing test
    bad_cfg_missing_test = json.loads(json.dumps(real_cfg))
    bad_cfg_missing_test["files"]["test"] = ["nonexistent-test.bats"]
    valid_b, msg_b = validate_config(exercise_dir, bad_cfg_missing_test)
    if valid_b or "does not exist" not in msg_b:
        print(f"ERROR: Missing test fixture unexpectedly passed: {msg_b}", file=sys.stderr)
        sys.exit(1)

    # Fixture C: outside exercise path / parent traversal
    bad_cfg_outside = json.loads(json.dumps(real_cfg))
    bad_cfg_outside["files"]["solution"] = ["../../outside.jq"]
    valid_c, msg_c = validate_config(exercise_dir, bad_cfg_outside)
    if valid_c or "Parent traversal forbidden" not in msg_c:
        print(f"ERROR: Outside-exercise path traversal fixture unexpectedly passed: {msg_c}", file=sys.stderr)
        sys.exit(1)

    # 4. Run isolated test suite in sandbox
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
            print("ERROR: Test validation failed:\n" + res.stdout + "\n" + res.stderr, file=sys.stderr)
            sys.exit(1)

        tap_ok = [l for l in res.stdout.splitlines() if l.startswith("ok ")]
        if len(tap_ok) != 5:
            print(f"ERROR: Expected 5 passing tests, got {len(tap_ok)}", file=sys.stderr)
            sys.exit(1)

        named_cases = ["no primes under two", "find first prime"]
        for nc in named_cases:
            if not any(nc in l for l in tap_ok):
                print(f"ERROR: Named case '{nc}' missing from executed tests", file=sys.stderr)
                sys.exit(1)

    # Verify working tree was not modified
    stub_hash_after = hash_file(stub_path)
    if stub_hash_before != stub_hash_after:
        print("ERROR: Working tree learner stub was altered during check!", file=sys.stderr)
        sys.exit(1)

    # 5. Save results and versions
    work_dir = os.path.join(repo_root, "work/R07-T018")
    os.makedirs(work_dir, exist_ok=True)

    summary = {
        "task_id": "R07-T018",
        "exercise": exercise_rel,
        "named_cases": named_cases,
        "executed_tests": len(tap_ok),
        "real_config_passed": True,
        "invalid_fixtures_tested": [
            {"fixture": "missing_reference", "correctly_rejected": True, "error": msg_a},
            {"fixture": "missing_test", "correctly_rejected": True, "error": msg_b},
            {"fixture": "outside_exercise_traversal", "correctly_rejected": True, "error": msg_c}
        ],
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

    print(f"SUCCESS: R07-T018 verified. Real config passed, 3 invalid fixtures rejected, {len(tap_ok)} tests passed.")


if __name__ == "__main__":
    main()
