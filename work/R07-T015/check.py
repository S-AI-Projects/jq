#!/usr/bin/env python3
"""Automated verification check for R07-T015 (Satellite reference complexity and scaling study)."""

import hashlib
import json
import os
import shutil
import statistics
import subprocess
import sys
import tempfile
import time


def hash_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()


def main():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    exercise_rel = "exercises/practice/satellite"
    exercise_dir = os.path.join(repo_root, exercise_rel)

    config_path = os.path.join(exercise_dir, ".meta/config.json")
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    stub_path = os.path.join(exercise_dir, cfg["files"]["solution"][0])
    with open(stub_path, "r", encoding="utf-8") as f:
        stub_content = f.read()

    # 1. Assert learner stub is still unsolved
    if "indices" in stub_content or "build_tree" in stub_content:
        print("ERROR: Working tree learner stub is solved!", file=sys.stderr)
        sys.exit(1)

    stub_hash_before = hash_file(stub_path)

    # 2. Run isolated test suite in sandbox
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
        if len(tap_ok) != 9:
            print(f"ERROR: Expected 9 passing tests, got {len(tap_ok)}", file=sys.stderr)
            sys.exit(1)

        named_cases = ["Empty tree", "Tree with one item", "Tree with many items"]
        for nc in named_cases:
            if not any(nc in l for l in tap_ok):
                print(f"ERROR: Named case '{nc}' missing from executed tests", file=sys.stderr)
                sys.exit(1)

    # 3. Benchmark timings across 3 domain sizes (5 repetitions each)
    example_path = os.path.join(exercise_dir, cfg["files"]["example"][0])
    benchmark_inputs = [
        ("N=0", {"preorder": [], "inorder": []}, {}),
        ("N=1", {"preorder": ["a"], "inorder": ["a"]}, {"v": "a", "l": {}, "r": {}}),
        ("N=5", {"preorder": ["a", "i", "x", "f", "r"], "inorder": ["i", "a", "f", "x", "r"]},
         {"v": "a", "l": {"v": "i", "l": {}, "r": {}}, "r": {"v": "x", "l": {"v": "f", "l": {}, "r": {}}, "r": {"v": "r", "l": {}, "r": {}}}})
    ]

    timings = {}
    for label, inp, expected in benchmark_inputs:
        runs = []
        inp_str = json.dumps(inp)
        for _ in range(5):
            t0 = time.perf_counter()
            proc = subprocess.run(
                ["jq", "-c", "-f", example_path],
                input=inp_str,
                capture_output=True,
                text=True,
                check=True
            )
            t1 = time.perf_counter()
            # Assert correctness before timing record
            actual = json.loads(proc.stdout)
            if actual != expected:
                print(f"ERROR: Correctness failed for {label}: expected {expected}, got {actual}", file=sys.stderr)
                sys.exit(1)
            runs.append((t1 - t0) * 1000.0)
        timings[label] = {
            "repetitions": len(runs),
            "median_ms": round(statistics.median(runs), 3),
            "all_ms": [round(x, 3) for x in runs]
        }

    # Verify working tree was not modified
    stub_hash_after = hash_file(stub_path)
    if stub_hash_before != stub_hash_after:
        print("ERROR: Working tree learner stub was altered during check!", file=sys.stderr)
        sys.exit(1)

    # 4. Save results and versions
    work_dir = os.path.join(repo_root, "work/R07-T015")
    os.makedirs(work_dir, exist_ok=True)

    summary = {
        "task_id": "R07-T015",
        "exercise": exercise_rel,
        "named_cases": named_cases,
        "executed_tests": len(tap_ok),
        "scaling_measurements": timings,
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

    print(f"SUCCESS: R07-T015 verified. {len(tap_ok)} tests passed. Scaling measurements recorded.")


if __name__ == "__main__":
    main()
