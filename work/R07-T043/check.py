#!/usr/bin/env python3
"""Automated verification check for task R07-T043 (run-length-encoding).

Validates that reference solution passes all canonical test cases, that a deliberate
mutant fails the specified test case, and that learner files remain unchanged.
"""

import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
EXERCISE_REL = pathlib.Path("exercises/practice/run-length-encoding")
EXERCISE_DIR = REPO_ROOT / EXERCISE_REL
STUB_FILE = EXERCISE_DIR / "run-length-encoding.jq"
EXAMPLE_FILE = EXERCISE_DIR / ".meta" / "example.jq"
WORK_DIR = REPO_ROOT / "work" / "R07-T043"

ANCHOR_CASES = [
    "run-length encode a string:empty string",
    "run-length encode a string:single characters only are encoded without count",
    "run-length encode a string:string with no single characters",
]

REJECTING_CASE = "run-length encode a string:single characters only are encoded without count"

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
        raise AssertionError("Learner stub run-length-encoding.jq has been modified or solved!")

def run_isolated(solution_content: str):
    temp_dir = tempfile.mkdtemp(prefix="rle_val_")
    try:
        for fname in ["bats-extra.bash", "bats-jq.bash", "test-run-length-encoding.bats"]:
            shutil.copy(EXERCISE_DIR / fname, temp_dir)
        with open(os.path.join(temp_dir, "run-length-encoding.jq"), "w") as f:
            f.write(solution_content)

        env = os.environ.copy()
        env["BATS_RUN_SKIPPED"] = "true"
        env["PATH"] = f"/opt/homebrew/bin:{env.get('PATH', '')}"

        proc = subprocess.run(
            ["bats", "--tap", "test-run-length-encoding.bats"],
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
    print("Running Task R07-T043 Checks (run-length-encoding)")
    print("=" * 60)

    os.makedirs(WORK_DIR, exist_ok=True)
    tool_vers = get_tool_versions()
    print("Tool versions:", tool_vers)
    with open(WORK_DIR / "tool_versions.json", "w") as f:
        json.dump(tool_vers, f, indent=2)

    verify_learner_stub()
    print("✓ Learner stub verified unsolved in working tree.")

    with open(EXAMPLE_FILE, "r") as f:
        ref_code = f.read()

    # 1. Run reference implementation
    rc_ref, out_ref, err_ref = run_isolated(ref_code)
    lines_ref = out_ref.strip().splitlines()
    passed_ref = [l[5:] for l in lines_ref if l.startswith("ok ")]
    failed_ref = [l for l in lines_ref if l.startswith("not ok ")]

    if rc_ref != 0 or len(failed_ref) > 0 or len(passed_ref) == 0:
        raise AssertionError(f"Reference failed tests: {failed_ref}\n{err_ref}")

    for anchor in ANCHOR_CASES:
        if not any(anchor in p for p in passed_ref):
            raise AssertionError(f"Anchor case '{anchor}' missing from passed tests!")
    print(f"✓ Reference passed all {len(passed_ref)} canonical test cases.")

    # 2. Run mutant
    mutant_code = ref_code.replace(
        '. + if $count == "1" then "" else $count end + $s[0]',
        '. + $count + $s[0]'
    )
    if mutant_code == ref_code:
        raise AssertionError("Failed to generate mutant from reference code!")

    rc_mut, out_mut, _ = run_isolated(mutant_code)
    lines_mut = out_mut.strip().splitlines()
    failed_mut = [l for l in lines_mut if l.startswith("not ok ")]

    if rc_mut == 0 or not any(REJECTING_CASE in f for f in failed_mut):
        raise AssertionError(f"Mutant did not fail rejecting case '{REJECTING_CASE}'! Output:\n{out_mut}")
    print(f"✓ Deliberate mutant successfully caught by '{REJECTING_CASE}'.")

    summary = {
        "task_id": "R07-T043",
        "exercise": "run-length-encoding",
        "tool_versions": tool_vers,
        "anchor_cases": ANCHOR_CASES,
        "rejecting_case": REJECTING_CASE,
        "reference_tests_passed": len(passed_ref),
        "mutant_rejected": True,
        "learner_stub_unsolved": True,
        "return_code": 0
    }

    with open(WORK_DIR / "check_summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    with open(WORK_DIR / "test_results.json", "w") as f:
        json.dump({"passed_tests": passed_ref, "mutant_failed_tests": failed_mut}, f, indent=2)

    verify_learner_stub()
    print("✓ All Task R07-T043 checks passed successfully.")

if __name__ == "__main__":
    main()
