#!/usr/bin/env python3
"""Automated verification check for task R07-T046 (scrabble-score).

Compares the reference implementation (ASCII array indexing) against an
independent alternative (Object dictionary lookup), verifying identical behavior
across all test cases in isolated environments without modifying learner files.
"""

import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
EXERCISE_REL = pathlib.Path("exercises/practice/scrabble-score")
EXERCISE_DIR = REPO_ROOT / EXERCISE_REL
STUB_FILE = EXERCISE_DIR / "scrabble-score.jq"
EXAMPLE_FILE = EXERCISE_DIR / ".meta" / "example.jq"
WORK_DIR = REPO_ROOT / "work" / "R07-T046"

ANCHOR_CASES = [
    "lowercase letter",
    "uppercase letter",
    "valuable letter",
]

ALTERNATIVE_SOLUTION = """
.word as $w
| {
    "A": 1, "E": 1, "I": 1, "O": 1, "U": 1, "L": 1, "N": 1, "R": 1, "S": 1, "T": 1,
    "D": 2, "G": 2,
    "B": 3, "C": 3, "M": 3, "P": 3,
    "F": 4, "H": 4, "V": 4, "W": 4, "Y": 4,
    "K": 5,
    "J": 8, "X": 8,
    "Q": 10, "Z": 10
  } as $points
| ($w // "")
| ascii_upcase
| split("")
| map($points[.] // 0)
| add // 0
"""

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
        raise AssertionError("Learner stub scrabble-score.jq has been modified or solved!")

def run_isolated(solution_content: str):
    temp_dir = tempfile.mkdtemp(prefix="ss_val_")
    try:
        for fname in ["bats-extra.bash", "bats-jq.bash", "test-scrabble-score.bats"]:
            shutil.copy(EXERCISE_DIR / fname, temp_dir)
        with open(os.path.join(temp_dir, "scrabble-score.jq"), "w") as f:
            f.write(solution_content)

        env = os.environ.copy()
        env["BATS_RUN_SKIPPED"] = "true"
        env["PATH"] = f"/opt/homebrew/bin:{env.get('PATH', '')}"

        proc = subprocess.run(
            ["bats", "--tap", "test-scrabble-score.bats"],
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
    print("Running Task R07-T046 Checks (scrabble-score)")
    print("=" * 60)

    os.makedirs(WORK_DIR, exist_ok=True)
    tool_vers = get_tool_versions()
    print("Tool versions:", tool_vers)
    with open(WORK_DIR / "tool_versions.json", "w") as f:
        json.dump(tool_vers, f, indent=2)

    verify_learner_stub()
    print("✓ Learner stub verified unsolved in working tree.")

    # 1. Run reference (Approach A)
    with open(EXAMPLE_FILE, "r") as f:
        ref_code = f.read()
    rc_ref, out_ref, err_ref = run_isolated(ref_code)
    lines_ref = out_ref.strip().splitlines()
    passed_ref = [l[5:] for l in lines_ref if l.startswith("ok ")]
    failed_ref = [l for l in lines_ref if l.startswith("not ok ")]

    if rc_ref != 0 or len(failed_ref) > 0 or len(passed_ref) == 0:
        raise AssertionError(f"Reference failed tests: {failed_ref}\n{err_ref}")
    print(f"✓ Reference (Approach A) passed all {len(passed_ref)} test cases.")

    # 2. Run alternative (Approach B)
    rc_alt, out_alt, err_alt = run_isolated(ALTERNATIVE_SOLUTION)
    lines_alt = out_alt.strip().splitlines()
    passed_alt = [l[5:] for l in lines_alt if l.startswith("ok ")]
    failed_alt = [l for l in lines_alt if l.startswith("not ok ")]

    if rc_alt != 0 or len(failed_alt) > 0 or len(passed_alt) == 0:
        raise AssertionError(f"Alternative (Approach B) failed tests: {failed_alt}\n{err_alt}")
    print(f"✓ Alternative (Approach B) passed all {len(passed_alt)} test cases.")

    if passed_ref != passed_alt:
        raise AssertionError("Parity mismatch between Approach A and Approach B!")
    print("✓ Full test parity verified between Approach A and Approach B.")

    for anchor in ANCHOR_CASES:
        if not any(anchor in p for p in passed_ref):
            raise AssertionError(f"Anchor case '{anchor}' missing from passed tests!")

    summary = {
        "task_id": "R07-T046",
        "exercise": "scrabble-score",
        "tool_versions": tool_vers,
        "anchor_cases": ANCHOR_CASES,
        "approach_a": "ASCII direct array indexing (example.jq)",
        "approach_b": "Object dictionary lookup (alternative)",
        "tests_executed": len(passed_ref),
        "tests_passed": len(passed_ref),
        "parity_verified": True,
        "learner_stub_unsolved": True,
        "return_code": 0
    }

    with open(WORK_DIR / "check_summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    with open(WORK_DIR / "test_results.json", "w") as f:
        json.dump({"passed_tests": passed_ref}, f, indent=2)

    verify_learner_stub()
    print("✓ All Task R07-T046 checks passed successfully.")

if __name__ == "__main__":
    main()
