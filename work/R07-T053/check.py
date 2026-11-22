#!/usr/bin/env python3
"""
Verification check for R07-T053: protein-translation mutant distinction.
Verifies reference passes all 31 canonical cases, mutant fails UUID 9d73899f-e68e-4291-b1e2-7bf87c00f024,
and learner stub remains unsolved.
"""
import os
import sys
import json
import shutil
import tempfile
import subprocess
import re

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
WORK_DIR = os.path.join(REPO_ROOT, "work", "R07-T053")
EXERCISE_DIR = os.path.join(REPO_ROOT, "exercises", "practice", "protein-translation")

MUTANT_JQ = """{
    "AUG": "Methionine", "UUU": "Phenylalanine", "UUC": "Phenylalanine",
    "UUA": "Leucine", "UUG": "Leucine", "UCU": "Serine", "UCC": "Serine",
    "UCA": "Serine", "UCG": "Serine", "UAU": "Tyrosine", "UAC": "Tyrosine",
    "UGU": "Cysteine", "UGC": "Cysteine", "UGG": "Tryptophan",
    "UAA": "STOP", "UAG": "STOP", "UGA": "STOP"
} as $c2p |
[
    label $translate |
    foreach (.strand | scan(".{3}")) as $codon (null; $c2p[$codon];
        if . == "STOP" then break $translate
        elif . then .
        else "Invalid codon" | halt_error
        end
    )
]
"""

def get_tool_versions():
    def cmd_out(args):
        try:
            return subprocess.check_output(args, text=True, stderr=subprocess.STDOUT).splitlines()[0].strip()
        except Exception as e:
            return str(e)

    python_ver = sys.version.split()[0]
    jq_ver = cmd_out(["jq", "--version"])
    bats_ver = cmd_out(["bats", "--version"])
    bash_ver = cmd_out(["bash", "--version"])
    grep_cmd = "ggrep" if shutil.which("ggrep") else "grep"
    grep_ver = cmd_out([grep_cmd, "--version"])

    return {
        "python": python_ver,
        "jq": jq_ver,
        "bats": bats_ver,
        "bash": bash_ver,
        "grep": grep_ver
    }

def verify_learner_stub():
    stub_path = os.path.join(EXERCISE_DIR, "protein-translation.jq")
    with open(stub_path, "r") as f:
        content = f.read()
    if "Remove this line and implement your solution" not in content:
        raise AssertionError("Learner stub protein-translation.jq has been modified or solved!")

def run_isolated_test(solution_code):
    temp_dir = tempfile.mkdtemp(prefix="pt_test_")
    try:
        # Copy exercise files
        for fname in ["bats-extra.bash", "bats-jq.bash", "test-protein-translation.bats"]:
            src = os.path.join(EXERCISE_DIR, fname)
            if os.path.exists(src):
                shutil.copy(src, temp_dir)
        # Write solution file
        with open(os.path.join(temp_dir, "protein-translation.jq"), "w") as f:
            f.write(solution_code)

        env = os.environ.copy()
        env["BATS_RUN_SKIPPED"] = "true"
        proc = subprocess.run(
            ["bats", "--tap", "test-protein-translation.bats"],
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
    print("Running R07-T053 Verification Checks (protein-translation)")
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

    ref_rc, ref_out, _ = run_isolated_test(ref_code)
    passed_ref = [line for line in ref_out.splitlines() if line.startswith("ok ")]
    failed_ref = [line for line in ref_out.splitlines() if line.startswith("not ok ")]
    if ref_rc != 0 or len(failed_ref) > 0:
        raise AssertionError(f"Reference implementation failed tests: {failed_ref}")
    print(f"✓ Reference passed all {len(passed_ref)} test cases.")

    # 3. Run mutant implementation
    mut_rc, mut_out, _ = run_isolated_test(MUTANT_JQ)
    failed_mut = [line for line in mut_out.splitlines() if line.startswith("not ok ")]
    passed_mut = [line for line in mut_out.splitlines() if line.startswith("ok ")]

    target_case = "Incomplete RNA sequence can't translate"
    rejecting_line = next((line for line in failed_mut if target_case in line), None)
    if not rejecting_line:
        raise AssertionError(f"Mutant did not fail target case '{target_case}'!")
    print(f"✓ Mutant correctly distinguished: failed '{rejecting_line}'.")

    # 4. Verify docs exist
    hints_path = os.path.join(EXERCISE_DIR, ".docs", "hints.md")
    maint_path = os.path.join(REPO_ROOT, "docs", "maintenance", "protein-translation.md")
    assert os.path.exists(hints_path), "hints.md missing"
    assert os.path.exists(maint_path), "docs/maintenance/protein-translation.md missing"
    print("✓ Documentation files hints.md and maintenance markdown verified.")

    # 5. Save results
    summary = {
        "task_id": "R07-T053",
        "exercise": "protein-translation",
        "tool_versions": tool_vers,
        "reference_validation": {
            "returncode": ref_rc,
            "tests_passed": len(passed_ref),
            "tests_failed": len(failed_ref)
        },
        "mutant_validation": {
            "returncode": mut_rc,
            "tests_passed": len(passed_mut),
            "tests_failed": len(failed_mut),
            "rejecting_test_id": "9d73899f-e68e-4291-b1e2-7bf87c00f024",
            "rejecting_test_name": target_case
        },
        "learner_stub_unsolved": True
    }
    with open(os.path.join(WORK_DIR, "check_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)

    with open(os.path.join(WORK_DIR, "test_results.json"), "w") as f:
        json.dump({
            "reference_passed_tests": passed_ref,
            "mutant_failed_tests": failed_mut
        }, f, indent=2)

    verify_learner_stub()
    print("=" * 60)
    print("✓ All R07-T053 checks passed successfully!")
    print("=" * 60)

if __name__ == "__main__":
    main()
