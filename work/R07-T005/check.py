#!/usr/bin/env python3
"""
Automated verification check for R07-T005:
Measure scaling and complexity of largest-series-product reference.
"""

import hashlib
import json
import os
import shutil
import statistics
import subprocess
import sys
import tempfile
import time


def hash_file(filepath):
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        hasher.update(f.read())
    return hasher.hexdigest()


def measure_case(example_path, input_data, expected_result, reps=7):
    input_json = json.dumps(input_data)
    # 1. Correctness check
    res = subprocess.run(
        ["jq", "-r", "-f", example_path],
        input=input_json,
        capture_output=True,
        text=True,
        check=True
    )
    actual_result = int(res.stdout.strip())
    if actual_result != expected_result:
        raise ValueError(f"Expected {expected_result}, got {actual_result}")

    # 2. Timing repetitions
    timings_ms = []
    for _ in range(reps):
        t0 = time.perf_counter()
        subprocess.run(
            ["jq", "-r", "-f", example_path],
            input=input_json,
            capture_output=True,
            text=True,
            check=True
        )
        t1 = time.perf_counter()
        timings_ms.append((t1 - t0) * 1000.0)

    median_ms = statistics.median(timings_ms)
    return median_ms


def main():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    exercise_rel = "exercises/practice/largest-series-product"
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
    if "assert" in stub_content or "product" in stub_content:
        print("ERROR: Working tree learner stub is solved!", file=sys.stderr)
        sys.exit(1)

    stub_hash_before = hash_file(stub_path)

    # 2. Assert example.jq contains complexity comment
    example_path = os.path.join(exercise_dir, example_rel)
    with open(example_path, "r", encoding="utf-8") as f:
        example_content = f.read()

    if "Complexity & Invariants for assert" not in example_content:
        print("ERROR: example.jq is missing complexity comment!", file=sys.stderr)
        sys.exit(1)

    # 3. Benchmark scaling across 3 canonical sizes
    test_cases = [
        {
            "name": "finds the largest product if span equals length",
            "digits": "29",
            "span": 2,
            "expected": 18
        },
        {
            "name": "can find the largest product of 2",
            "digits": "576802143",
            "span": 2,
            "expected": 48
        },
        {
            "name": "can find the largest product of 2 with numbers in order",
            "digits": "0123456789",
            "span": 2,
            "expected": 72
        }
    ]

    measured_results = []
    for tc in test_cases:
        inp = {"digits": tc["digits"], "span": tc["span"]}
        med = measure_case(example_path, inp, tc["expected"], reps=7)
        n = len(tc["digits"])
        k = tc["span"]
        measured_results.append({
            "case": tc["name"],
            "input_length_N": n,
            "span_k": k,
            "assertions_count": 3,
            "sliding_windows": n - k + 1,
            "multiplications": (n - k + 1) * k,
            "median_runtime_ms": round(med, 2),
            "verified_correct": True
        })

    # 4. Isolated test execution in temporary copy
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
        if len(tap_ok) != 15:
            print(f"ERROR: Expected 15 executed passing tests, got {len(tap_ok)}", file=sys.stderr)
            sys.exit(1)

        named_cases = [tc["name"] for tc in test_cases]
        for nc in named_cases:
            if not any(nc in l for l in tap_ok):
                print(f"ERROR: Named case '{nc}' not found in executed tests", file=sys.stderr)
                sys.exit(1)

    # 5. Verify working tree stub was not modified
    stub_hash_after = hash_file(stub_path)
    if stub_hash_before != stub_hash_after:
        print("ERROR: Working tree learner stub was altered during check!", file=sys.stderr)
        sys.exit(1)

    # 6. Save results and tool versions
    work_dir = os.path.join(repo_root, "work/R07-T005")
    os.makedirs(work_dir, exist_ok=True)

    summary = {
        "task_id": "R07-T005",
        "exercise": exercise_rel,
        "measured_scaling": measured_results,
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

    print(f"SUCCESS: R07-T005 verified. 15 tests passed. Empirical scaling & complexity measured across 3 valid sizes.")


if __name__ == "__main__":
    main()
