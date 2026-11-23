#!/usr/bin/env python3
"""Course check for task R07-T041 (matching-brackets).

Validates canonical case rationales, TOML integrity, and runs tests in an
isolated temporary environment without altering learner files in the working tree.
"""

import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import tomllib

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
EXERCISE_REL = pathlib.Path("exercises/practice/matching-brackets")
EXERCISE_DIR = REPO_ROOT / EXERCISE_REL
CONFIG_FILE = EXERCISE_DIR / ".meta" / "config.json"
TESTS_TOML = EXERCISE_DIR / ".meta" / "tests.toml"
WORK_DIR = REPO_ROOT / "work" / "R07-T041"

SELECTED_UUIDS = [
    "81ec11da-38dd-442a-bcf9-3de7754609a5",
    "287f0167-ac60-4b64-8452-a0aa8f4e5238",
    "6c3615a3-df01-4130-a731-8ef5f5d78dac",
]

ANCHOR_CASES = [
    "paired square brackets",
    "empty string",
    "unpaired brackets",
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

def verify_working_tree():
    with open(CONFIG_FILE, "r") as f:
        config = json.load(f)

    solution_rel = config["files"]["solution"][0]
    solution_path = EXERCISE_DIR / solution_rel
    with open(solution_path, "r") as f:
        content = f.read()

    if "implement your solution" not in content and "halt_error" not in content:
        raise AssertionError(f"Learner stub {solution_path} appears modified or solved!")

    # Verify TOML
    with open(TESTS_TOML, "rb") as f:
        toml_data = tomllib.load(f)

    included_count = 0
    excluded_count = 0
    for k, v in toml_data.items():
        if isinstance(v, dict):
            if v.get("include", True):
                included_count += 1
            else:
                excluded_count += 1

    if included_count != 20 or excluded_count != 0:
        raise AssertionError(f"Expected 20 included and 0 excluded, got {included_count} included, {excluded_count} excluded")

    for uuid in SELECTED_UUIDS:
        if uuid not in toml_data:
            raise AssertionError(f"Missing UUID {uuid} in tests.toml")
        case = toml_data[uuid]
        comment = case.get("comment", "")
        if not comment:
            raise AssertionError(f"UUID {uuid} is missing rationale comment in tests.toml")

    return config, included_count, excluded_count

def run_isolated_validation():
    with open(CONFIG_FILE, "r") as f:
        config = json.load(f)

    solution_file = config["files"]["solution"][0]
    example_file = config["files"]["example"][0]
    test_file = config["files"]["test"][0]

    temp_dir = tempfile.mkdtemp(prefix="r07_t041_")
    try:
        # Copy exercise directory including dotfiles
        dest_exercise = pathlib.Path(temp_dir) / EXERCISE_REL
        os.makedirs(dest_exercise.parent, exist_ok=True)
        shutil.copytree(EXERCISE_DIR, dest_exercise)

        # Substitute reference solution into learner stub in temp copy only
        src_example = dest_exercise / example_file
        dest_stub = dest_exercise / solution_file
        shutil.copyfile(src_example, dest_stub)

        # Execute tests via bats in isolated directory
        env = os.environ.copy()
        env["BATS_RUN_SKIPPED"] = "true"
        env["PATH"] = f"/opt/homebrew/bin:{env.get('PATH', '')}"

        proc = subprocess.run(
            ["bats", "--tap", str(dest_exercise / test_file)],
            cwd=str(dest_exercise),
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
    print("Running Task R07-T041 Checks (matching-brackets)")
    print("=" * 60)

    os.makedirs(WORK_DIR, exist_ok=True)
    tool_vers = get_tool_versions()
    print("Tool versions:", tool_vers)
    with open(WORK_DIR / "tool_versions.json", "w") as f:
        json.dump(tool_vers, f, indent=2)

    config, incl, excl = verify_working_tree()
    print(f"✓ Working tree verified: 0 exclusions, {incl} canonical cases included.")

    rc, out, err = run_isolated_validation()
    lines = out.strip().splitlines()
    passed_cases = [line[5:] for line in lines if line.startswith("ok ")]
    failed_cases = [line for line in lines if line.startswith("not ok ")]

    if rc != 0 or len(failed_cases) > 0:
        raise AssertionError(f"Tests failed with exit code {rc}:\n{err}\n{out}")

    if len(passed_cases) == 0:
        raise AssertionError("Zero test cases executed!")

    for anchor in ANCHOR_CASES:
        if not any(anchor in case for case in passed_cases):
            raise AssertionError(f"Anchor case '{anchor}' was not found in passed cases!")

    summary = {
        "task_id": "R07-T041",
        "exercise": "matching-brackets",
        "tool_versions": tool_vers,
        "selected_uuids": SELECTED_UUIDS,
        "anchor_cases": ANCHOR_CASES,
        "canonical_counts": {
            "included": incl,
            "excluded": excl
        },
        "tests_executed": len(passed_cases),
        "tests_passed": len(passed_cases),
        "tests_failed": 0,
        "return_code": rc,
        "learner_stub_unsolved": True
    }

    with open(WORK_DIR / "check_summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    with open(WORK_DIR / "test_results.json", "w") as f:
        json.dump({"passed_tests": passed_cases}, f, indent=2)

    print(f"✓ Isolated tests passed: {len(passed_cases)} cases executed successfully.")
    print("✓ All checks completed successfully.")

if __name__ == "__main__":
    main()
