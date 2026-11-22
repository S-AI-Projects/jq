#!/usr/bin/env python3
"""
Verification check for R07-T056: bottle-song two implementation approaches.
Verifies reference passes all 7 canonical cases, compares Approach A and Approach B
on anchor cases, and verifies learner stub remains unsolved.
"""
import os
import sys
import json
import shutil
import tempfile
import subprocess

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
WORK_DIR = os.path.join(REPO_ROOT, "work", "R07-T056")
EXERCISE_DIR = os.path.join(REPO_ROOT, "exercises", "practice", "bottle-song")

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
    stub_path = os.path.join(EXERCISE_DIR, "bottle-song.jq")
    with open(stub_path, "r") as f:
        content = f.read()
    if "Remove this line and implement your solution" not in content:
        raise AssertionError("Learner stub bottle-song.jq has been modified or solved!")

def run_isolated_bats(solution_code):
    temp_dir = tempfile.mkdtemp(prefix="bs_test_")
    try:
        for fname in ["bats-extra.bash", "bats-jq.bash", "test-bottle-song.bats"]:
            src = os.path.join(EXERCISE_DIR, fname)
            if os.path.exists(src):
                shutil.copy(src, temp_dir)
        with open(os.path.join(temp_dir, "bottle-song.jq"), "w") as f:
            f.write(solution_code)

        env = os.environ.copy()
        env["BATS_RUN_SKIPPED"] = "true"
        proc = subprocess.run(
            ["bats", "--tap", "test-bottle-song.bats"],
            cwd=temp_dir,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        return proc.returncode, proc.stdout, proc.stderr
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

def run_single_input(solution_code, input_dict):
    proc = subprocess.run(
        ["jq", "-c", solution_code],
        input=json.dumps(input_dict),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True
    )
    return json.loads(proc.stdout)

def main():
    print("=" * 60)
    print("Running R07-T056 Verification Checks (bottle-song)")
    print("=" * 60)

    os.makedirs(WORK_DIR, exist_ok=True)
    tool_vers = get_tool_versions()
    print("Tool versions:", tool_vers)
    with open(os.path.join(WORK_DIR, "tool_versions.json"), "w") as f:
        json.dump(tool_vers, f, indent=2)

    # 1. Verify working tree stub
    verify_learner_stub()
    print("✓ Learner stub verified unsolved in working tree.")

    # 2. Run reference implementation against bats suite
    with open(os.path.join(EXERCISE_DIR, ".meta", "example.jq"), "r") as f:
        ref_code = f.read()

    ref_rc, ref_out, _ = run_isolated_bats(ref_code)
    passed_ref = [line for line in ref_out.splitlines() if line.startswith("ok ")]
    failed_ref = [line for line in ref_out.splitlines() if line.startswith("not ok ")]
    if ref_rc != 0 or len(failed_ref) > 0:
        raise AssertionError(f"Reference implementation failed tests: {failed_ref}")
    print(f"✓ Reference passed all {len(passed_ref)} test cases.")

    # 3. Verify Approach A and Approach B on anchor cases
    anchor_inputs = [
        {"name": "first generic verse", "input": {"startBottles": 10, "takeDown": 1}},
        {"name": "last generic verse", "input": {"startBottles": 3, "takeDown": 1}},
        {"name": "verse with 2 bottles", "input": {"startBottles": 2, "takeDown": 1}}
    ]

    with open(os.path.join(WORK_DIR, "approach_a.jq"), "r") as f:
        code_a = f.read()
    with open(os.path.join(WORK_DIR, "approach_b.jq"), "r") as f:
        code_b = f.read()

    # Run bats for both approaches too!
    rc_a, out_a, _ = run_isolated_bats(code_a)
    rc_b, out_b, _ = run_isolated_bats(code_b)
    assert rc_a == 0, "Approach A failed bats suite"
    assert rc_b == 0, "Approach B failed bats suite"
    print("✓ Both Approach A and Approach B pass all 7 canonical test cases!")

    comparison_results = {}
    for item in anchor_inputs:
        out_ref = run_single_input(ref_code, item["input"])
        out_a_val = run_single_input(code_a, item["input"])
        out_b_val = run_single_input(code_b, item["input"])
        assert out_ref == out_a_val == out_b_val, f"Mismatch in {item['name']}"
        comparison_results[item["name"]] = {
            "input": item["input"],
            "output_lines_count": len(out_ref),
            "output": out_ref
        }
        print(f"✓ Anchor case verified across approaches: '{item['name']}'.")

    # 4. Verify hints.md exists
    hints_path = os.path.join(EXERCISE_DIR, ".docs", "hints.md")
    assert os.path.exists(hints_path), "hints.md missing"
    print("✓ hints.md documentation verified.")

    # 5. Save results
    summary = {
        "task_id": "R07-T056",
        "exercise": "bottle-song",
        "tool_versions": tool_vers,
        "validation_results": {
            "returncode": ref_rc,
            "tests_planned": len(passed_ref),
            "tests_passed": len(passed_ref),
            "tests_failed": 0
        },
        "approach_comparison": {
            "approach_a": "Array-indexed number words + functional interpolation",
            "approach_b": "Modular single-verse constructor with reduce join",
            "anchor_cases_verified": [item["name"] for item in anchor_inputs]
        },
        "learner_stub_unsolved": True
    }
    with open(os.path.join(WORK_DIR, "check_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)

    with open(os.path.join(WORK_DIR, "test_results.json"), "w") as f:
        json.dump({
            "passed_tests": passed_ref,
            "comparisons": comparison_results
        }, f, indent=2)

    verify_learner_stub()
    print("=" * 60)
    print("✓ All R07-T056 checks passed successfully!")
    print("=" * 60)

if __name__ == "__main__":
    main()
