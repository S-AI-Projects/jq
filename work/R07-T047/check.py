#!/usr/bin/env python3
"""Automated verification check for task R07-T047 (etl).

Validates isolated reference tests, asserts both micro-example outputs
against published documentation, confirms learner files remain unsolved.
"""

import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
EXERCISE_REL = pathlib.Path("exercises/practice/etl")
EXERCISE_DIR = REPO_ROOT / EXERCISE_REL
STUB_FILE = EXERCISE_DIR / "etl.jq"
EXAMPLE_FILE = EXERCISE_DIR / ".meta" / "example.jq"
HINTS_FILE = EXERCISE_DIR / ".docs" / "hints.md"
WORK_DIR = REPO_ROOT / "work" / "R07-T047"

ANCHOR_CASES = [
    "single letter",
    "single score with multiple letters",
    "multiple scores with multiple letters",
]

MICRO_EXAMPLE_1 = {
    "expr": '{"1": ["A", "B"]} | [to_entries[] | {key: (.value[] | ascii_downcase), value: (.key | tonumber)}]',
    "expected": [{"key": "a", "value": 1}, {"key": "b", "value": 1}]
}

MICRO_EXAMPLE_2 = {
    "expr": '[{"key": "a", "value": 1}, {"key": "b", "value": 1}] | from_entries',
    "expected": {"a": 1, "b": 1}
}

def get_tool_versions():
    def run_cmd(cmd):
        try:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
            return res.stdout.strip().splitlines()[0]
        except Exception as e:
            return f"unavailable ({e})"

    return {
        "python": sys.version.split()[0],
        "jq": run_cmd(["jq", "--version"]),
        "bats": run_cmd(["bats", "--version"]),
        "bash": run_cmd(["bash", "--version"]),
        "grep": run_cmd(["ggrep", "--version"]) if shutil.which("ggrep") else run_cmd(["grep", "--version"]),
    }

def verify_learner_stub():
    with open(STUB_FILE, "r") as f:
        content = f.read()
    if "implement your solution" not in content and "halt_error" not in content:
        raise AssertionError("Learner stub etl.jq has been modified or solved!")

def verify_micro_examples():
    for i, ex in enumerate([MICRO_EXAMPLE_1, MICRO_EXAMPLE_2], start=1):
        proc = subprocess.run(
            ["jq", "-c", "-n", ex["expr"]],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        actual = json.loads(proc.stdout.strip())
        if actual != ex["expected"]:
            raise AssertionError(f"Micro-example {i} failed: expected {ex['expected']}, got {actual}")
    print("✓ Both micro-examples executed in jq and matched expected outputs.")

def verify_hints_content():
    with open(HINTS_FILE, "r") as f:
        hints = f.read()
    for needle in ["stream cardinality", "to_entries", "from_entries", "https://jqlang.github.io/jq/manual"]:
        if needle.lower() not in hints.lower():
            raise AssertionError(f"Missing required documentation item: '{needle}' in hints.md")
    print("✓ Language guidance, micro-examples, and reference links verified in hints.md.")

def run_isolated():
    temp_dir = tempfile.mkdtemp(prefix="etl_val_")
    try:
        for fname in ["bats-extra.bash", "bats-jq.bash", "test-etl.bats"]:
            shutil.copy(EXERCISE_DIR / fname, temp_dir)
        shutil.copy(EXAMPLE_FILE, os.path.join(temp_dir, "etl.jq"))

        env = os.environ.copy()
        env["BATS_RUN_SKIPPED"] = "true"
        env["PATH"] = f"/opt/homebrew/bin:{env.get('PATH', '')}"

        proc = subprocess.run(
            ["bats", "--tap", "test-etl.bats"],
            cwd=temp_dir,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        return proc.returncode, proc.stdout, proc.stderr
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

def main():
    print("=" * 60)
    print("Running Task R07-T047 Checks (etl)")
    print("=" * 60)

    os.makedirs(WORK_DIR, exist_ok=True)
    tool_vers = get_tool_versions()
    print("Tool versions:", tool_vers)
    with open(WORK_DIR / "tool_versions.json", "w") as f:
        json.dump(tool_vers, f, indent=2)

    verify_learner_stub()
    print("✓ Learner stub verified unsolved in working tree.")

    verify_micro_examples()
    verify_hints_content()

    rc, out, err = run_isolated()
    lines = out.strip().splitlines()
    passed = [l[5:] for l in lines if l.startswith("ok ")]
    failed = [l for l in lines if l.startswith("not ok ")]

    if rc != 0 or len(failed) > 0 or len(passed) == 0:
        raise AssertionError(f"Tests failed with code {rc}:\n{err}\n{out}")

    for anchor in ANCHOR_CASES:
        if not any(anchor in p for p in passed):
            raise AssertionError(f"Anchor case '{anchor}' missing from passed tests!")

    print(f"✓ Reference passed all {len(passed)} canonical tests in isolated runner.")

    summary = {
        "task_id": "R07-T047",
        "exercise": "etl",
        "tool_versions": tool_vers,
        "anchor_cases": ANCHOR_CASES,
        "micro_examples_asserted": 2,
        "tests_executed": len(passed),
        "tests_passed": len(passed),
        "tests_failed": 0,
        "learner_stub_unsolved": True,
        "return_code": 0
    }

    with open(WORK_DIR / "check_summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    with open(WORK_DIR / "test_results.json", "w") as f:
        json.dump({"passed_tests": passed}, f, indent=2)

    verify_learner_stub()
    print("✓ All Task R07-T047 checks passed successfully.")

if __name__ == "__main__":
    main()
