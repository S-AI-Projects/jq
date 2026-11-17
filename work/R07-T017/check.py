#!/usr/bin/env python3
"""Automated verification check for R07-T017 (jq-specific guidance for Forth)."""

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
    exercise_rel = "exercises/practice/forth"
    exercise_dir = os.path.join(repo_root, exercise_rel)

    config_path = os.path.join(exercise_dir, ".meta/config.json")
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    stub_path = os.path.join(exercise_dir, cfg["files"]["solution"][0])
    with open(stub_path, "r", encoding="utf-8") as f:
        stub_content = f.read()

    # 1. Assert learner stub is still unsolved
    if "record_macro" in stub_content or "isnumeric" in stub_content:
        print("ERROR: Working tree learner stub is solved!", file=sys.stderr)
        sys.exit(1)

    stub_hash_before = hash_file(stub_path)

    # 2. Assert micro-examples match published hint
    env = os.environ.copy()
    env["PATH"] = f"/opt/homebrew/bin:{env.get('PATH', '')}"

    # Micro-example 1: array construction
    res1 = subprocess.run(
        ["jq", "-c", "-n", '{"stack": [1, 2]} | .stack += [3]'],
        capture_output=True,
        text=True,
        check=True
    )
    out1 = res1.stdout.strip()
    expected_out1 = '{"stack":[1,2,3]}'
    if out1 != expected_out1:
        print(f"ERROR: Micro-example 1 mismatch: expected {expected_out1}, got {out1}", file=sys.stderr)
        sys.exit(1)

    # Micro-example 2: contrasting pitfall (type error without brackets)
    res2 = subprocess.run(
        ["jq", "-c", "-n", 'try ({"stack": [1, 2]} | .stack += 3) catch .'],
        capture_output=True,
        text=True,
        check=True
    )
    out2 = res2.stdout.strip()
    expected_out2 = '"array ([1,2]) and number (3) cannot be added"'
    if out2 != expected_out2:
        print(f"ERROR: Micro-example 2 mismatch: expected {expected_out2}, got {out2}", file=sys.stderr)
        sys.exit(1)

    # 3. Run isolated test suite in sandbox
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_exercise = os.path.join(tmpdir, exercise_rel)
        os.makedirs(os.path.dirname(tmp_exercise), exist_ok=True)
        shutil.copytree(exercise_dir, tmp_exercise)
        shutil.copytree(os.path.join(repo_root, "bin"), os.path.join(tmpdir, "bin"))

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
        if len(tap_ok) != 54:
            print(f"ERROR: Expected 54 passing tests, got {len(tap_ok)}", file=sys.stderr)
            sys.exit(1)

        named_cases = [
            "parsing and numbers:numbers just get pushed onto the stack",
            "parsing and numbers:pushes negative numbers onto the stack",
            "addition:can add two numbers"
        ]
        for nc in named_cases:
            if not any(nc in l for l in tap_ok):
                print(f"ERROR: Named case '{nc}' missing from executed tests", file=sys.stderr)
                sys.exit(1)

    # Verify working tree was not modified
    stub_hash_after = hash_file(stub_path)
    if stub_hash_before != stub_hash_after:
        print("ERROR: Working tree learner stub was altered during check!", file=sys.stderr)
        sys.exit(1)

    # 4. Save results and versions
    work_dir = os.path.join(repo_root, "work/R07-T017")
    os.makedirs(work_dir, exist_ok=True)

    summary = {
        "task_id": "R07-T017",
        "exercise": exercise_rel,
        "named_cases": named_cases,
        "executed_tests": len(tap_ok),
        "micro_example_1": {"input": '{"stack": [1, 2]} | .stack += [3]', "output": out1},
        "micro_example_2": {"input": 'try ({"stack": [1, 2]} | .stack += 3) catch .', "output": out2},
        "guidance_topic": "Array construction and concatenation in stack operations",
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

    print(f"SUCCESS: R07-T017 verified. Micro-examples match hint. All {len(tap_ok)} tests passed.")


if __name__ == "__main__":
    main()
