#!/usr/bin/env python3
"""Automated verification check for task R07-T044 (rotational-cipher).

Validates the refactored makeMap reference solution in an isolated runner,
confirms anchor cases pass, and ensures learner files remain untouched.
"""

import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
EXERCISE_REL = pathlib.Path("exercises/practice/rotational-cipher")
EXERCISE_DIR = REPO_ROOT / EXERCISE_REL
STUB_FILE = EXERCISE_DIR / "rotational-cipher.jq"
EXAMPLE_FILE = EXERCISE_DIR / ".meta" / "example.jq"
WORK_DIR = REPO_ROOT / "work" / "R07-T044"

ANCHOR_CASES = [
    "rotate a by 0, same output as input",
    "rotate a by 1",
    "rotate a by 26, same output as input",
]

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
        raise AssertionError("Learner stub rotational-cipher.jq has been modified or solved!")

def run_isolated():
    temp_dir = tempfile.mkdtemp(prefix="rot_val_")
    try:
        for fname in ["bats-extra.bash", "bats-jq.bash", "test-rotational-cipher.bats"]:
            shutil.copy(EXERCISE_DIR / fname, temp_dir)
        shutil.copy(EXAMPLE_FILE, os.path.join(temp_dir, "rotational-cipher.jq"))

        env = os.environ.copy()
        env["BATS_RUN_SKIPPED"] = "true"
        env["PATH"] = f"/opt/homebrew/bin:{env.get('PATH', '')}"

        proc = subprocess.run(
            ["bats", "--tap", "test-rotational-cipher.bats"],
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
    print("Running Task R07-T044 Checks (rotational-cipher)")
    print("=" * 60)

    os.makedirs(WORK_DIR, exist_ok=True)
    tool_vers = get_tool_versions()
    print("Tool versions:", tool_vers)
    with open(WORK_DIR / "tool_versions.json", "w") as f:
        json.dump(tool_vers, f, indent=2)

    verify_learner_stub()
    print("✓ Learner stub verified unsolved in working tree.")

    # Verify example comment invariant
    with open(EXAMPLE_FILE, "r") as f:
        ex_code = f.read()
    if "$shift % 26" not in ex_code or "Invariant" not in ex_code:
        raise AssertionError("Invariant comment or modulo 26 normalization missing from example.jq!")

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
        "task_id": "R07-T044",
        "exercise": "rotational-cipher",
        "tool_versions": tool_vers,
        "anchor_cases": ANCHOR_CASES,
        "tests_executed": len(passed),
        "tests_passed": len(passed),
        "tests_failed": 0,
        "refactor_verified": True,
        "learner_stub_unsolved": True,
        "return_code": 0
    }

    with open(WORK_DIR / "check_summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    with open(WORK_DIR / "test_results.json", "w") as f:
        json.dump({"passed_tests": passed}, f, indent=2)

    verify_learner_stub()
    print("✓ All Task R07-T044 checks passed successfully.")

if __name__ == "__main__":
    main()
