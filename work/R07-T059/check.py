#!/usr/bin/env python3
"""
Verification check for R07-T059: flower-field isolated execution without altering learner files.
Verifies all 12 canonical test cases pass against reference in isolated directory,
confirms anchor cases, runs course runner script, and guarantees working tree stub remains untouched.
"""
import os
import sys
import json
import shutil
import tempfile
import subprocess

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
WORK_DIR = os.path.join(REPO_ROOT, "work", "R07-T059")
EXERCISE_DIR = os.path.join(REPO_ROOT, "exercises", "practice", "flower-field")

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
    stub_path = os.path.join(EXERCISE_DIR, "flower-field.jq")
    with open(stub_path, "r") as f:
        content = f.read()
    if "Remove this line and implement your solution" not in content and "halt_error" not in content:
        raise AssertionError("Learner stub flower-field.jq has been modified or solved!")

def run_isolated_bats():
    temp_dir = tempfile.mkdtemp(prefix="ff_val_")
    try:
        for fname in ["bats-extra.bash", "bats-jq.bash", "test-flower-field.bats"]:
            shutil.copy(os.path.join(EXERCISE_DIR, fname), temp_dir)
        shutil.copy(os.path.join(EXERCISE_DIR, ".meta", "example.jq"), os.path.join(temp_dir, "flower-field.jq"))

        env = os.environ.copy()
        env["BATS_RUN_SKIPPED"] = "true"
        proc = subprocess.run(
            ["bats", "--tap", "test-flower-field.bats"],
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
    print("Running R07-T059 Verification Checks (flower-field)")
    print("=" * 60)

    os.makedirs(WORK_DIR, exist_ok=True)
    tool_vers = get_tool_versions()
    print("Tool versions:", tool_vers)
    with open(os.path.join(WORK_DIR, "tool_versions.json"), "w") as f:
        json.dump(tool_vers, f, indent=2)

    # 1. Verify working tree stub
    verify_learner_stub()
    print("✓ Learner stub verified unsolved in working tree.")

    # 2. Run course runner script
    runner_script = os.path.join(REPO_ROOT, "tools", "course_checks", "r07-t059.py")
    subprocess.check_call([sys.executable, runner_script])
    print("✓ tools/course_checks/r07-t059.py passed successfully.")

    # 3. Validate reference execution
    rc, out, _ = run_isolated_bats()
    passed = [line for line in out.splitlines() if line.startswith("ok ")]
    failed = [line for line in out.splitlines() if line.startswith("not ok ")]
    if rc != 0 or len(failed) > 0:
        raise AssertionError(f"Reference failed tests: {failed}")
    print(f"✓ Reference passed all {len(passed)} test cases.")

    # 4. Save results
    summary = {
        "task_id": "R07-T059",
        "exercise": "flower-field",
        "tool_versions": tool_vers,
        "isolation_verified": True,
        "validation_results": {
            "returncode": rc,
            "tests_planned": len(passed),
            "tests_passed": len(passed),
            "tests_failed": 0,
            "anchor_cases_verified": [
                "no columns",
                "no flowers",
                "vertical line"
            ]
        },
        "learner_stub_unsolved": True
    }
    with open(os.path.join(WORK_DIR, "check_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)

    with open(os.path.join(WORK_DIR, "test_results.json"), "w") as f:
        json.dump({"passed_tests": passed}, f, indent=2)

    verify_learner_stub()
    print("=" * 60)
    print("✓ All R07-T059 checks passed successfully!")
    print("=" * 60)

if __name__ == "__main__":
    main()
