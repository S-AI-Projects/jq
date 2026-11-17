#!/usr/bin/env python3
"""Automated verification check for R07-T020 (Secret Handshake subtle contract cases)."""

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile


def hash_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()


def main():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    exercise_rel = "exercises/practice/secret-handshake"
    exercise_dir = os.path.join(repo_root, exercise_rel)

    config_path = os.path.join(exercise_dir, ".meta/config.json")
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    stub_path = os.path.join(exercise_dir, cfg["files"]["solution"][0])
    with open(stub_path, "r", encoding="utf-8") as f:
        stub_content = f.read()

    # 1. Assert learner stub is still unsolved
    if "bit_set" in stub_content or "shift_right" in stub_content:
        print("ERROR: Working tree learner stub is solved!", file=sys.stderr)
        sys.exit(1)

    stub_hash_before = hash_file(stub_path)

    # 2. Validate decision table cases against reference in scratch execution
    example_path = os.path.join(exercise_dir, cfg["files"]["example"][0])
    decision_table = [
        {"name": "wink for 1", "input": {"number": 1}, "expected": ["wink"]},
        {"name": "double blink for 10", "input": {"number": 2}, "expected": ["double blink"]},
        {"name": "close your eyes for 100", "input": {"number": 4}, "expected": ["close your eyes"]},
    ]

    for item in decision_table:
        res = subprocess.run(
            ["jq", "-c", "-f", example_path],
            input=json.dumps(item["input"]),
            capture_output=True,
            text=True,
            check=True
        )
        actual = json.loads(res.stdout)
        if actual != item["expected"]:
            print(f"ERROR: Decision table mismatch for {item['name']}: expected {item['expected']}, got {actual}", file=sys.stderr)
            sys.exit(1)

    # 3. Run isolated test suite in temporary sandbox
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
        if len(tap_ok) != 11:
            print(f"ERROR: Expected 11 passing tests, got {len(tap_ok)}", file=sys.stderr)
            sys.exit(1)

        for item in decision_table:
            if not any(item["name"] in l for l in tap_ok):
                print(f"ERROR: Named case '{item['name']}' missing from executed tests", file=sys.stderr)
                sys.exit(1)

    # Verify working tree was not modified
    stub_hash_after = hash_file(stub_path)
    if stub_hash_before != stub_hash_after:
        print("ERROR: Working tree learner stub was altered during check!", file=sys.stderr)
        sys.exit(1)

    # 4. Save results and versions
    work_dir = os.path.join(repo_root, "work/R07-T020")
    os.makedirs(work_dir, exist_ok=True)

    summary = {
        "task_id": "R07-T020",
        "exercise": exercise_rel,
        "decision_table": decision_table,
        "executed_tests": len(tap_ok),
        "all_decision_cases_passed": True,
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

    print(f"SUCCESS: R07-T020 verified. Decision table matches all {len(decision_table)} cases. All {len(tap_ok)} tests passed.")


if __name__ == "__main__":
    main()
