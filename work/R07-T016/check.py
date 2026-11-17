#!/usr/bin/env python3
"""Automated verification check for R07-T016 (Compare nth-prime implementation approaches)."""

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
    exercise_rel = "exercises/practice/nth-prime"
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
    exercise_rel = "exercises/practice/nth-prime"
    exercise_dir = os.path.join(repo_root, exercise_rel)

    config_path = os.path.join(exercise_dir, ".meta/config.json")
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    stub_path = os.path.join(exercise_dir, cfg["files"]["solution"][0])
    with open(stub_path, "r", encoding="utf-8") as f:
        stub_content = f.read()

    # 1. Assert learner stub is still unsolved
    if "is_prime" in stub_content or "next_prime" in stub_content:
        print("ERROR: Working tree learner stub is solved!", file=sys.stderr)
        sys.exit(1)

    stub_hash_before = hash_file(stub_path)

    # 2. Run real reference in sandbox
    ret_ref, tap_ref, out_ref, err_ref = run_isolated_suite(repo_root)
    if ret_ref != 0:
        print(f"ERROR: Reference implementation failed:\n{out_ref}\n{err_ref}", file=sys.stderr)
        sys.exit(1)

    named_cases = ["first prime", "second prime", "sixth prime"]
    for nc in named_cases:
        if not any(nc in l for l in tap_ref):
            print(f"ERROR: Named case '{nc}' missing from reference run", file=sys.stderr)
            sys.exit(1)

    # 3. Run alternative approach in sandbox
    alt_file = os.path.join(repo_root, "work/R07-T016/alternative.jq")
    with open(alt_file, "r", encoding="utf-8") as f:
        alt_content = f.read()

    ret_alt, tap_alt, out_alt, err_alt = run_isolated_suite(repo_root, custom_example_content=alt_content)
    if ret_alt != 0:
        print(f"ERROR: Alternative implementation failed:\n{out_alt}\n{err_alt}", file=sys.stderr)
        sys.exit(1)

    for nc in named_cases:
        if not any(nc in l for l in tap_alt):
            print(f"ERROR: Named case '{nc}' missing from alternative run", file=sys.stderr)
            sys.exit(1)

    # 4. Verify working tree invariance
    stub_hash_after = hash_file(stub_path)
    if stub_hash_before != stub_hash_after:
        print("ERROR: Learner stub modified during check!", file=sys.stderr)
        sys.exit(1)

    # 5. Save results and versions
    work_dir = os.path.join(repo_root, "work/R07-T016")
    os.makedirs(work_dir, exist_ok=True)

    summary = {
        "task_id": "R07-T016",
        "exercise": exercise_rel,
        "named_cases": named_cases,
        "reference_tests_passed": len(tap_ref),
        "alternative_tests_passed": len(tap_alt),
        "approaches_compared": [
            "Dynamic Prime Accumulation (Reference)",
            "Constant-Space Direct Trial Division (Alternative)"
        ],
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

    print(f"SUCCESS: R07-T016 verified. Both reference and alternative approach passed all {len(tap_ref)} tests.")


if __name__ == "__main__":
    main()
