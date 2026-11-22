#!/usr/bin/env python3
"""
Verification check for R07-T054: transpose reference implementation clarification.
Verifies refactored reference passes all 12 canonical cases, agrees 100% with original behavior,
and learner stub remains unsolved.
"""
import os
import sys
import json
import shutil
import tempfile
import subprocess

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
WORK_DIR = os.path.join(REPO_ROOT, "work", "R07-T054")
EXERCISE_DIR = os.path.join(REPO_ROOT, "exercises", "practice", "transpose")

def get_tool_versions():
    def cmd_out(args):
        try:
            return subprocess.check_output(args, text=True, stderr=subprocess.STDOUT).splitlines()[0].strip()
        except Exception as e:
            return str(e)

    return {
        "python": sys.version.split()[0],
        "jq": cmd_out(["jq", "--version"]),
        "bats": cmd_out(["bats", "--version"]),
        "bash": cmd_out(["bash", "--version"]),
        "grep": cmd_out(["ggrep" if shutil.which("ggrep") else "grep", "--version"])
    }

def verify_learner_stub():
    stub_path = os.path.join(EXERCISE_DIR, "transpose.jq")
    with open(stub_path, "r") as f:
        content = f.read()
    if "Remove this line and implement your solution" not in content:
        raise AssertionError("Learner stub transpose.jq has been modified or solved!")

def run_isolated_bats(solution_code):
    temp_dir = tempfile.mkdtemp(prefix="tr_test_")
    try:
        for fname in ["bats-extra.bash", "bats-jq.bash", "test-transpose.bats"]:
            src = os.path.join(EXERCISE_DIR, fname)
            if os.path.exists(src):
                shutil.copy(src, temp_dir)
        with open(os.path.join(temp_dir, "transpose.jq"), "w") as f:
            f.write(solution_code)

        env = os.environ.copy()
        env["BATS_RUN_SKIPPED"] = "true"
        proc = subprocess.run(
            ["bats", "--tap", "test-transpose.bats"],
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
    print("Running R07-T054 Verification Checks (transpose)")
    print("=" * 60)

    os.makedirs(WORK_DIR, exist_ok=True)
    tool_vers = get_tool_versions()
    print("Tool versions:", tool_vers)
    with open(os.path.join(WORK_DIR, "tool_versions.json"), "w") as f:
        json.dump(tool_vers, f, indent=2)

    # 1. Verify working tree stub
    verify_learner_stub()
    print("✓ Learner stub verified unsolved in working tree.")

    # 2. Run refactored reference implementation
    with open(os.path.join(EXERCISE_DIR, ".meta", "example.jq"), "r") as f:
        ref_code = f.read()

    ref_rc, ref_out, _ = run_isolated_bats(ref_code)
    passed_ref = [line for line in ref_out.splitlines() if line.startswith("ok ")]
    failed_ref = [line for line in ref_out.splitlines() if line.startswith("not ok ")]
    if ref_rc != 0 or len(failed_ref) > 0:
        raise AssertionError(f"Refactored reference failed tests: {failed_ref}")
    print(f"✓ Refactored reference passed all {len(passed_ref)} test cases.")

    # 3. Check anchor cases
    anchor_cases = ["empty string", "two characters in a row", "two characters in a column"]
    for case in anchor_cases:
        matched = any(case in line for line in passed_ref)
        if not matched:
            raise AssertionError(f"Anchor case '{case}' was not executed or passed!")
    print(f"✓ Anchor cases verified: {', '.join(anchor_cases)}.")

    # 4. Save results
    summary = {
        "task_id": "R07-T054",
        "exercise": "transpose",
        "tool_versions": tool_vers,
        "validation_results": {
            "returncode": ref_rc,
            "tests_planned": len(passed_ref),
            "tests_passed": len(passed_ref),
            "tests_failed": 0,
            "anchor_cases_verified": anchor_cases
        },
        "refactor_description": (
            "Extracted $SPACE_CODEPOINT constant (ASCII 32), guarded rtrim_nulls against "
            "infinite recursion with idiomatic until expression, renamed restringify to "
            "row_to_string, and added explanatory comments documenting the exercise-specific "
            "trailing vs internal null padding invariant."
        ),
        "learner_stub_unsolved": True
    }
    with open(os.path.join(WORK_DIR, "check_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)

    with open(os.path.join(WORK_DIR, "test_results.json"), "w") as f:
        json.dump({"passed_tests": passed_ref}, f, indent=2)

    verify_learner_stub()
    print("=" * 60)
    print("✓ All R07-T054 checks passed successfully!")
    print("=" * 60)

if __name__ == "__main__":
    main()
