#!/usr/bin/env python3
"""
Verification check for R07-T055: rna-transcription reference scaling and complexity study.
Verifies reference passes all 6 canonical cases, confirms anchor cases,
records scaling measurements, and confirms learner stub remains unsolved.
"""
import os
import sys
import json
import time
import shutil
import tempfile
import subprocess

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
WORK_DIR = os.path.join(REPO_ROOT, "work", "R07-T055")
EXERCISE_DIR = os.path.join(REPO_ROOT, "exercises", "practice", "rna-transcription")

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
    stub_path = os.path.join(EXERCISE_DIR, "rna-transcription.jq")
    with open(stub_path, "r") as f:
        content = f.read()
    if "halt_error" not in content or "Implement this function" not in content:
        raise AssertionError("Learner stub rna-transcription.jq has been modified or solved!")

def run_isolated_bats(solution_code):
    temp_dir = tempfile.mkdtemp(prefix="rna_test_")
    try:
        for fname in ["bats-extra.bash", "bats-jq.bash", "test-rna-transcription.bats"]:
            src = os.path.join(EXERCISE_DIR, fname)
            if os.path.exists(src):
                shutil.copy(src, temp_dir)
        with open(os.path.join(temp_dir, "rna-transcription.jq"), "w") as f:
            f.write(solution_code)

        env = os.environ.copy()
        env["BATS_RUN_SKIPPED"] = "true"
        proc = subprocess.run(
            ["bats", "--tap", "test-rna-transcription.bats"],
            cwd=temp_dir,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        return proc.returncode, proc.stdout, proc.stderr
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

def measure_scaling(ref_code):
    sizes = [10, 100, 1000, 10000, 100000]
    timings = {}
    jq_script = ref_code + "\n.dna | toRna"
    for n in sizes:
        dna = ("GCTA" * (n // 4 + 1))[:n]
        input_json = json.dumps({"dna": dna})
        trials = 5 if n <= 1000 else 3
        times = []
        for _ in range(trials):
            t0 = time.perf_counter()
            proc = subprocess.run(
                ["jq", "-r", jq_script],
                input=input_json,
                text=True,
                stdout=subprocess.PIPE,
                check=True
            )
            t1 = time.perf_counter()
            times.append(t1 - t0)
        avg_ms = round((sum(times) / len(times)) * 1000, 3)
        timings[str(n)] = {
            "size": n,
            "avg_ms": avg_ms,
            "output_length": len(proc.stdout.strip())
        }
    return timings

def main():
    print("=" * 60)
    print("Running R07-T055 Verification Checks (rna-transcription)")
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
    anchor_cases = [
        "Empty RNA sequence",
        "RNA complement of cytosine is guanine",
        "RNA complement of guanine is cytosine"
    ]
    for case in anchor_cases:
        matched = any(case in line for line in passed_ref)
        if not matched:
            raise AssertionError(f"Anchor case '{case}' was not executed or passed!")
    print(f"✓ Anchor cases verified: {', '.join(anchor_cases)}.")

    # 4. Measure scaling
    scaling_results = measure_scaling(ref_code)
    print("✓ Scaling measurements collected across input sizes N in [10, 100, 1000, 10000, 100000]:")
    for sz, data in scaling_results.items():
        print(f"    N={sz}: {data['avg_ms']} ms")

    # 5. Save results
    summary = {
        "task_id": "R07-T055",
        "exercise": "rna-transcription",
        "tool_versions": tool_vers,
        "validation_results": {
            "returncode": ref_rc,
            "tests_planned": len(passed_ref),
            "tests_passed": len(passed_ref),
            "tests_failed": 0,
            "anchor_cases_verified": anchor_cases
        },
        "scaling_measurements": scaling_results,
        "complexity": {
            "time_complexity": "O(N)",
            "space_complexity": "O(N)",
            "model": "Linear string split, table lookup, and string reassembly"
        },
        "learner_stub_unsolved": True
    }
    with open(os.path.join(WORK_DIR, "check_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)

    with open(os.path.join(WORK_DIR, "test_results.json"), "w") as f:
        json.dump({"passed_tests": passed_ref, "scaling": scaling_results}, f, indent=2)

    verify_learner_stub()
    print("=" * 60)
    print("✓ All R07-T055 checks passed successfully!")
    print("=" * 60)

if __name__ == "__main__":
    main()
