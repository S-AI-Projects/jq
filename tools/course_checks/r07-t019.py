#!/usr/bin/env python3
"""Isolated test runner for acronym (R07-T019)."""

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile


def hash_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()


def run_isolated_suite(repo_root: str, custom_solution_content: str = None, custom_test_content: str = None):
    exercise_rel = "exercises/practice/acronym"
    exercise_dir = os.path.join(repo_root, exercise_rel)

    config_path = os.path.join(exercise_dir, ".meta/config.json")
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    example_rel = cfg["files"]["example"][0]
    test_rel = cfg["files"]["test"][0]

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_exercise = os.path.join(tmpdir, exercise_rel)
        os.makedirs(os.path.dirname(tmp_exercise), exist_ok=True)
        shutil.copytree(exercise_dir, tmp_exercise)
        shutil.copytree(os.path.join(repo_root, "bin"), os.path.join(tmpdir, "bin"))
        if os.path.exists(os.path.join(repo_root, "lib")):
            shutil.copytree(os.path.join(repo_root, "lib"), os.path.join(tmpdir, "lib"))

        if custom_solution_content is not None:
            example_dest = os.path.join(tmp_exercise, example_rel)
            with open(example_dest, "w", encoding="utf-8") as f:
                f.write(custom_solution_content)

        if custom_test_content is not None:
            test_dest = os.path.join(tmp_exercise, test_rel)
            with open(test_dest, "w", encoding="utf-8") as f:
                f.write(custom_test_content)

        env = os.environ.copy()
        env["PATH"] = f"/opt/homebrew/bin:{env.get('PATH', '')}"

        res = subprocess.run(
            ["./bin/validate_one_exercise", exercise_rel],
            cwd=tmpdir,
            capture_output=True,
            text=True,
            env=env
        )

        tap_lines = [l for l in res.stdout.splitlines() if l.startswith("ok ")]
        return res.returncode, len(tap_lines), res.stdout, res.stderr


def main():
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    exercise_dir = os.path.join(root, "exercises/practice/acronym")
    stub_file = os.path.join(exercise_dir, "acronym.jq")

    hash_before = hash_file(stub_file)

    # 1. Success run with real reference
    code_ref, count_ref, out_ref, err_ref = run_isolated_suite(root)
    if code_ref != 0 or count_ref != 9:
        print(f"ERROR: Real reference run failed with exit code {code_ref}, tests {count_ref}", file=sys.stderr)
        sys.exit(1)

    hash_after_ref = hash_file(stub_file)
    if hash_before != hash_after_ref:
        print("ERROR: Learner stub modified during reference run!", file=sys.stderr)
        sys.exit(1)

    # 2. Failure run with deliberately failing solution
    failing_content = 'def parse: "WRONG";\n'
    code_fail, count_fail, _, _ = run_isolated_suite(root, custom_solution_content=failing_content)
    if code_fail == 0:
        print("ERROR: Failing reference did not return non-zero exit code!", file=sys.stderr)
        sys.exit(1)

    hash_after_fail = hash_file(stub_file)
    if hash_before != hash_after_fail:
        print("ERROR: Learner stub modified during failing run!", file=sys.stderr)
        sys.exit(1)

    # 3. Failure run with empty test selection (zero-test run)
    empty_bats = "#!/usr/bin/env bats\nload bats-extra\nload bats-jq\n"
    code_empty, count_empty, _, _ = run_isolated_suite(root, custom_test_content=empty_bats)
    if count_empty != 0 or code_empty == 0:
        print(f"ERROR: Zero-test suite must fail or produce 0 tests (got code {code_empty}, count {count_empty})", file=sys.stderr)
        sys.exit(1)

    hash_after_empty = hash_file(stub_file)
    if hash_before != hash_after_empty:
        print("ERROR: Learner stub modified during empty test run!", file=sys.stderr)
        sys.exit(1)

    print(f"Isolated runner verified successfully. Real tests passed: {count_ref}, failing run rejected, zero-test run rejected, hashes invariant.")


if __name__ == "__main__":
    main()
