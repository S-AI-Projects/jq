#!/usr/bin/env python3
"""Automated verification check for R07-T013 (Collatz Conjecture mutation-driven regression)."""

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


def run_isolated_suite(repo_root, custom_example_content=None):
    exercise_rel = "exercises/practice/collatz-conjecture"
    exercise_dir = os.path.join(repo_root, exercise_rel)

    config_path = os.path.join(exercise_dir, ".meta/config.json")
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    example_rel = cfg["files"]["example"][0]

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_exercise = os.path.join(tmpdir, exercise_rel)
        os.makedirs(os.path.dirname(tmp_exercise), exist_ok=True)
        shutil.copytree(exercise_dir, tmp_exercise)
        shutil.copytree(os.path.join(repo_root, "bin"), os.path.join(tmpdir, "bin"))

        if custom_example_content is not None:
            example_dest = os.path.join(tmp_exercise, example_rel)
            with open(example_dest, "w", encoding="utf-8") as f:
                f.write(custom_example_content)

        env = os.environ.copy()
        env["PATH"] = f"/opt/homebrew/bin:{env.get('PATH', '')}"

        res = subprocess.run(
            ["./bin/validate_one_exercise", exercise_rel],
            cwd=tmpdir,
            capture_output=True,
            text=True,
            env=env
        )
        tap_ok = [l for l in res.stdout.splitlines() if l.startswith("ok ")]
        return res.returncode, tap_ok, res.stdout, res.stderr


def main():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    exercise_rel = "exercises/practice/collatz-conjecture"
    exercise_dir = os.path.join(repo_root, exercise_rel)

    config_path = os.path.join(exercise_dir, ".meta/config.json")
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    stub_path = os.path.join(exercise_dir, cfg["files"]["solution"][0])
    with open(stub_path, "r", encoding="utf-8") as f:
        stub_content = f.read()

    # 1. Assert learner stub is still unsolved
    if "Implement this function" not in stub_content:
        print("ERROR: Working tree learner stub is solved!", file=sys.stderr)
        sys.exit(1)

    stub_hash_before = hash_file(stub_path)

    # 2. Run real reference in sandbox
    ret_orig, tap_orig, out_orig, err_orig = run_isolated_suite(repo_root)
    if ret_orig != 0 or len(tap_orig) != 6:
        print(f"ERROR: Original reference run failed (ret={ret_orig}, tests={len(tap_orig)}):\n{out_orig}\n{err_orig}", file=sys.stderr)
        sys.exit(1)

    named_cases = ["zero steps for one", "divide if even", "even and odd steps"]
    for nc in named_cases:
        if not any(nc in l for l in tap_orig):
            print(f"ERROR: Named case '{nc}' missing from executed tests", file=sys.stderr)
            sys.exit(1)

    # 3. Run mutant reference in sandbox
    example_path = os.path.join(exercise_dir, cfg["files"]["example"][0])
    with open(example_path, "r", encoding="utf-8") as f:
        orig_example = f.read()

    # Create deliberate mutant: off-by-one on terminal condition
    mutant_content = orig_example.replace(
        "if (.[0] == 1) then .[1]",
        "if (.[0] == 1) then .[1] + 1"
    )
    if mutant_content == orig_example:
        print("ERROR: Failed to create mutant from reference implementation", file=sys.stderr)
        sys.exit(1)

    ret_mut, tap_mut, out_mut, err_mut = run_isolated_suite(repo_root, custom_example_content=mutant_content)
    if ret_mut == 0:
        print("ERROR: Mutated reference unexpectedly passed the test suite!", file=sys.stderr)
        sys.exit(1)

    # Verify that 'zero steps for one' failed
    if "not ok 1 zero steps for one" not in out_mut:
        print("ERROR: Expected mutant to fail 'zero steps for one':\n" + out_mut, file=sys.stderr)
        sys.exit(1)

    # 4. Verify working tree invariance
    stub_hash_after = hash_file(stub_path)
    if stub_hash_before != stub_hash_after:
        print("ERROR: Learner stub modified during check!", file=sys.stderr)
        sys.exit(1)

    # 5. Save results and versions
    work_dir = os.path.join(repo_root, "work/R07-T013")
    os.makedirs(work_dir, exist_ok=True)

    summary = {
        "task_id": "R07-T013",
        "exercise": exercise_rel,
        "named_cases": named_cases,
        "executed_tests": len(tap_orig),
        "original_passed": True,
        "mutant_rejected": True,
        "rejecting_test": "zero steps for one",
        "learner_stub_unsolved": True,
        "all_assertions_passed": True
    }
    with open(os.path.join(work_dir, "test_results.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    env = os.environ.copy()
    env["PATH"] = f"/opt/homebrew/bin:{env.get('PATH', '')}"
    versions = {
        "python": sys.version.split()[0],
        "jq": subprocess.run(["jq", "--version"], capture_output=True, text=True).stdout.strip(),
        "bats": subprocess.run(["bats", "--version"], capture_output=True, text=True, env=env).stdout.strip()
    }
    with open(os.path.join(work_dir, "tool_versions.json"), "w", encoding="utf-8") as f:
        json.dump(versions, f, indent=2)

    print(f"SUCCESS: R07-T013 verified. Original passed {len(tap_orig)} tests, mutant successfully rejected by 'zero steps for one'.")


if __name__ == "__main__":
    main()
