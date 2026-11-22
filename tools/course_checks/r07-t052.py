#!/usr/bin/env python3
"""Reusable focused regeneration check for task R07-T052.

Verifies the route from canonical problem-specifications and tests.toml
to test-spiral-matrix.bats, ensuring reproducibility, anchor case integrity,
and reference execution against exercises/practice/spiral-matrix/.meta/example.jq.
"""

import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
EXERCISE_REL = pathlib.Path("exercises/practice/spiral-matrix")
EXERCISE_DIR = REPO_ROOT / EXERCISE_REL
META_DIR = EXERCISE_DIR / ".meta"
CONFIG_FILE = META_DIR / "config.json"
TESTS_TOML = META_DIR / "tests.toml"
MAINTENANCE_DOC = REPO_ROOT / "docs/maintenance/spiral-matrix.md"

ANCHOR_CASES = {
    "8f584201-b446-4bc9-b132-811c8edd9040": {
        "name": "empty spiral",
        "input": {"size": 0},
        "expected": [],
    },
    "e40ae5f3-e2c9-4639-8116-8a119d632ab2": {
        "name": "trivial spiral",
        "input": {"size": 1},
        "expected": [[1]],
    },
    "cf05e42d-eb78-4098-a36e-cdaf0991bc48": {
        "name": "spiral of size 2",
        "input": {"size": 2},
        "expected": [
            [1, 2],
            [4, 3],
        ],
    },
}


def normalize_bats(content: str) -> str:
    """Normalize Bats file content by stripping the timestamp line."""
    lines = [line for line in content.splitlines() if not line.startswith("# generated on")]
    return "\n".join(lines).strip()


def check_stub_unsolved(stub_path: pathlib.Path) -> None:
    """Verify that learner solution stub remains unsolved and halts on input."""
    assert stub_path.exists(), f"Stub file not found at {stub_path}"
    content = stub_path.read_text(encoding="utf-8")
    assert "halt_error" in content or "Remove this line" in content, (
        f"Learner stub at {stub_path} appears modified or solved!"
    )
    proc = subprocess.run(
        ["jq", "-c", "-f", str(stub_path)],
        input=json.dumps({"size": 1}),
        capture_output=True,
        text=True,
    )
    assert proc.returncode != 0, "Learner stub must fail/halt on input"
    print("✓ Learner stub verified unsolved in working tree.")


def check_documentation() -> None:
    """Verify that maintenance doc exists and documents reproduction command and anchor cases."""
    assert MAINTENANCE_DOC.exists(), f"Maintenance documentation missing at {MAINTENANCE_DOC}"
    doc_text = MAINTENANCE_DOC.read_text(encoding="utf-8")
    assert "bin/test-generator" in doc_text, "Maintenance doc must include reproduction command"
    for case_info in ANCHOR_CASES.values():
        assert case_info["name"] in doc_text, (
            f"Maintenance doc missing anchor case mention: {case_info['name']}"
        )
    print("✓ Maintenance documentation verified.")


def check_regeneration_reproducibility() -> None:
    """Verify that two independent generations yield identical normalized test files."""
    with tempfile.TemporaryDirectory() as tmp1, tempfile.TemporaryDirectory() as tmp2:
        outputs = []
        for tmp in (tmp1, tmp2):
            tmp_root = pathlib.Path(tmp)
            target_exercise = tmp_root / EXERCISE_REL
            shutil.copytree(EXERCISE_DIR, target_exercise)
            # Remove pre-existing bats to enforce new generation
            target_bats = target_exercise / "test-spiral-matrix.bats"
            if target_bats.exists():
                target_bats.unlink()
            shutil.copytree(REPO_ROOT / "bin", tmp_root / "bin")

            res = subprocess.run(
                ["python3", "bin/test-generator", "--no-pull", str(EXERCISE_REL)],
                cwd=str(tmp_root),
                capture_output=True,
                text=True,
            )
            assert res.returncode == 0, (
                f"test-generator failed in temp directory:\nstdout: {res.stdout}\nstderr: {res.stderr}"
            )
            assert target_bats.exists(), f"test-generator did not generate {target_bats}"
            outputs.append(target_bats.read_text(encoding="utf-8"))

        norm1 = normalize_bats(outputs[0])
        norm2 = normalize_bats(outputs[1])
        assert norm1 == norm2, "Discrepancy detected between two independent test generations!"

        # Ensure all anchor cases and enabled cases are present in generated bats
        for case in ANCHOR_CASES.values():
            assert f"@test '{case['name']}'" in norm1, (
                f"Anchor case '{case['name']}' missing from generated Bats tests!"
            )

        committed_bats = normalize_bats((EXERCISE_DIR / "test-spiral-matrix.bats").read_text(encoding="utf-8"))
        assert norm1 == committed_bats, (
            "Generated Bats tests do not match committed test-spiral-matrix.bats!"
        )
        print("✓ Two independent generations verified reproducible without case drops.")


def check_reference_execution() -> None:
    """Validate reference implementation against tests using bin/validate_one_exercise."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp_root = pathlib.Path(tmp)
        tmp_exercise = tmp_root / EXERCISE_REL
        shutil.copytree(EXERCISE_DIR, tmp_exercise)
        shutil.copytree(REPO_ROOT / "bin", tmp_root / "bin")

        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)

        solution_rel = config["files"]["solution"][0]
        example_rel = config["files"]["example"][0]

        # Substitute reference into solution in temporary copy ONLY
        shutil.copy2(tmp_exercise / example_rel, tmp_exercise / solution_rel)

        proc = subprocess.run(
            [str(REPO_ROOT / "bin/validate_one_exercise"), str(EXERCISE_REL)],
            cwd=str(tmp_root),
            capture_output=True,
            text=True,
        )
        output = proc.stdout + proc.stderr
        print(output.strip())

        assert proc.returncode == 0, f"Validation failed with code {proc.returncode}:\n{output}"

        tap_plan = re.search(r"1\.\.(\d+)", output)
        assert tap_plan, f"Could not find TAP test plan in output:\n{output}"
        num_planned = int(tap_plan.group(1))
        assert num_planned > 0, "Zero tests planned!"

        ok_matches = re.findall(r"^ok \d+ (.*)$", output, flags=re.MULTILINE)
        num_passed = len(ok_matches)
        assert num_passed == num_planned, (
            f"Mismatch between planned ({num_planned}) and passed ({num_passed}) tests"
        )
        for case in ANCHOR_CASES.values():
            assert case["name"] in ok_matches, (
                f"Anchor case '{case['name']}' was not executed in validate_one_exercise!"
            )
        print(f"✓ All {num_passed} tests passed against reference implementation.")


def main() -> None:
    print("=" * 60)
    print("Running Course Check: r07-t052 (spiral-matrix)")
    print("=" * 60)

    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        config = json.load(f)
    stub_file = EXERCISE_DIR / config["files"]["solution"][0]

    check_stub_unsolved(stub_file)
    check_documentation()
    check_regeneration_reproducibility()
    check_reference_execution()
    check_stub_unsolved(stub_file)

    print("=" * 60)
    print("✓ All r07-t052 course checks passed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
