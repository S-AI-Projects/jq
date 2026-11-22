#!/usr/bin/env python3
"""
Verification check for R07-T057: space-age jq-specific guidance and micro-examples.
Verifies reference passes all 9 canonical cases, tests micro-examples,
confirms anchor cases, and verifies learner stub remains unsolved.
"""
import os
import sys
import json
import shutil
import tempfile
import subprocess

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
WORK_DIR = os.path.join(REPO_ROOT, "work", "R07-T057")
EXERCISE_DIR = os.path.join(REPO_ROOT, "exercises", "practice", "space-age")

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
    stub_path = os.path.join(EXERCISE_DIR, "space-age.jq")
    with open(stub_path, "r") as f:
        content = f.read()
    if "Remove this line and implement your solution" not in content and "halt_error" not in content:
        raise AssertionError("Learner stub space-age.jq has been modified or solved!")

def run_isolated_bats(solution_code):
    temp_dir = tempfile.mkdtemp(prefix="sa_test_")
    try:
        for fname in ["bats-extra.bash", "bats-jq.bash", "test-space-age.bats"]:
            src = os.path.join(EXERCISE_DIR, fname)
            if os.path.exists(src):
                shutil.copy(src, temp_dir)
        with open(os.path.join(temp_dir, "space-age.jq"), "w") as f:
            f.write(solution_code)

        env = os.environ.copy()
        env["BATS_RUN_SKIPPED"] = "true"
        proc = subprocess.run(
            ["bats", "--tap", "test-space-age.bats"],
            cwd=temp_dir,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        return proc.returncode, proc.stdout, proc.stderr
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

def verify_micro_examples():
    # Test 1: round 31.687537 to 2 decimals
    out1 = subprocess.check_output(
        ["jq", "-n", "31.687537 | ((. * 100) | round) / 100"],
        text=True
    ).strip()
    assert float(out1) == 31.69, f"Micro-example 1 failed: {out1} != 31.69"

    # Test 2: Mercury calculation
    out2 = subprocess.check_output(
        ["jq", "-n", "(2134835688 / 31557600 / 0.2408467) | ((. * 100) | round) / 100"],
        text=True
    ).strip()
    assert float(out2) == 280.88, f"Micro-example 2 failed: {out2} != 280.88"

    return {"example_1": float(out1), "example_2": float(out2)}

def main():
    print("=" * 60)
    print("Running R07-T057 Verification Checks (space-age)")
    print("=" * 60)

    os.makedirs(WORK_DIR, exist_ok=True)
    tool_vers = get_tool_versions()
    print("Tool versions:", tool_vers)
    with open(os.path.join(WORK_DIR, "tool_versions.json"), "w") as f:
        json.dump(tool_vers, f, indent=2)

    # 1. Verify working tree stub
    verify_learner_stub()
    print("✓ Learner stub verified unsolved in working tree.")

    # 2. Run reference implementation
    with open(os.path.join(EXERCISE_DIR, ".meta", "example.jq"), "r") as f:
        ref_code = f.read()

    ref_rc, ref_out, _ = run_isolated_bats(ref_code)
    passed_ref = [line for line in ref_out.splitlines() if line.startswith("ok ")]
    failed_ref = [line for line in ref_out.splitlines() if line.startswith("not ok ")]
    if ref_rc != 0 or len(failed_ref) > 0:
        raise AssertionError(f"Reference implementation failed tests: {failed_ref}")
    print(f"✓ Reference passed all {len(passed_ref)} test cases.")

    # 3. Check anchor cases
    anchor_cases = ["age on Earth", "age on Mercury", "age on Venus"]
    for case in anchor_cases:
        matched = any(case in line for line in passed_ref)
        if not matched:
            raise AssertionError(f"Anchor case '{case}' was not executed or passed!")
    print(f"✓ Anchor cases verified: {', '.join(anchor_cases)}.")

    # 4. Verify micro-examples and documentation
    micro_res = verify_micro_examples()
    print(f"✓ Micro-examples verified: {micro_res}")

    hints_path = os.path.join(EXERCISE_DIR, ".docs", "hints.md")
    assert os.path.exists(hints_path), "hints.md missing"
    with open(hints_path, "r") as f:
        hints_content = f.read()
    assert "https://jqlang.github.io/jq/manual/#math" in hints_content, "Official manual link missing from hints.md"
    assert "two_decimal" in hints_content, "Rounding filter definition missing from hints.md"
    print("✓ Documentation hints.md verified with official jq documentation link.")

    # 5. Save results
    summary = {
        "task_id": "R07-T057",
        "exercise": "space-age",
        "tool_versions": tool_vers,
        "validation_results": {
            "returncode": ref_rc,
            "tests_planned": len(passed_ref),
            "tests_passed": len(passed_ref),
            "tests_failed": 0,
            "anchor_cases_verified": anchor_cases
        },
        "micro_examples_verified": micro_res,
        "hints_link_verified": "https://jqlang.github.io/jq/manual/#math",
        "learner_stub_unsolved": True
    }
    with open(os.path.join(WORK_DIR, "check_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)

    with open(os.path.join(WORK_DIR, "test_results.json"), "w") as f:
        json.dump({
            "passed_tests": passed_ref,
            "micro_examples": micro_res
        }, f, indent=2)

    verify_learner_stub()
    print("=" * 60)
    print("✓ All R07-T057 checks passed successfully!")
    print("=" * 60)

if __name__ == "__main__":
    main()
