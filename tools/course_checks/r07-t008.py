#!/usr/bin/env python3
"""Path and configuration validator for pascals-triangle (R07-T008)."""

import json
import os
import sys


def validate_config(cfg, exercise_dir):
    """
    Validates declared paths in exercise config.
    Rejects parent traversal and ensures declared files exist.
    """
    if "files" not in cfg:
        raise ValueError("Missing 'files' object in config")

    files_obj = cfg["files"]
    checked_roles = ["solution", "test", "example"]

    for role in checked_roles:
        if role not in files_obj or not files_obj[role]:
            raise ValueError(f"Missing required file role: '{role}'")

        for rel_path in files_obj[role]:
            # Reject parent traversal and absolute paths
            if os.path.isabs(rel_path) or ".." in rel_path.split(os.sep):
                raise ValueError(f"Security error: path '{rel_path}' in role '{role}' contains forbidden traversal")

            full_path = os.path.normpath(os.path.join(exercise_dir, rel_path))
            # Ensure resolved path remains strictly within exercise_dir
            if not full_path.startswith(os.path.abspath(exercise_dir) + os.sep):
                raise ValueError(f"Traversal error: path '{rel_path}' escapes exercise root")

            if not os.path.isfile(full_path):
                raise ValueError(f"Missing file error: declared {role} file '{rel_path}' does not exist")

    return True


def run_negative_tests(exercise_dir):
    """Verifies that deliberate metadata defects fail with appropriate reasons."""
    # 1. Missing reference
    bad_cfg_ref = {
        "files": {
            "solution": ["pascals-triangle.jq"],
            "test": ["test-pascals-triangle.bats"],
            "example": [".meta/non-existent-example.jq"]
        }
    }
    try:
        validate_config(bad_cfg_ref, exercise_dir)
        print("ERROR: missing-reference fixture unexpectedly passed!", file=sys.stderr)
        return False
    except ValueError as e:
        if "Missing file error" not in str(e):
            print(f"ERROR: missing-reference failed with unexpected error: {e}", file=sys.stderr)
            return False

    # 2. Missing test
    bad_cfg_test = {
        "files": {
            "solution": ["pascals-triangle.jq"],
            "test": ["missing-test-pascals-triangle.bats"],
            "example": [".meta/example.jq"]
        }
    }
    try:
        validate_config(bad_cfg_test, exercise_dir)
        print("ERROR: missing-test fixture unexpectedly passed!", file=sys.stderr)
        return False
    except ValueError as e:
        if "Missing file error" not in str(e):
            print(f"ERROR: missing-test failed with unexpected error: {e}", file=sys.stderr)
            return False

    # 3. Outside exercise (traversal)
    bad_cfg_outside = {
        "files": {
            "solution": ["pascals-triangle.jq"],
            "test": ["test-pascals-triangle.bats"],
            "example": ["../outside-example.jq"]
        }
    }
    try:
        validate_config(bad_cfg_outside, exercise_dir)
        print("ERROR: outside-exercise fixture unexpectedly passed!", file=sys.stderr)
        return False
    except ValueError as e:
        if "forbidden traversal" not in str(e) and "escapes exercise root" not in str(e):
            print(f"ERROR: outside-exercise failed with unexpected error: {e}", file=sys.stderr)
            return False

    return True


def main():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    exercise_rel = "exercises/practice/pascals-triangle"
    exercise_dir = os.path.join(repo_root, exercise_rel)

    config_path = os.path.join(exercise_dir, ".meta/config.json")
    with open(config_path, "r", encoding="utf-8") as f:
        real_cfg = json.load(f)

    # Validate real configuration
    try:
        validate_config(real_cfg, exercise_dir)
    except Exception as e:
        print(f"ERROR: Real config failed validation: {e}", file=sys.stderr)
        sys.exit(1)

    # Run negative tests
    if not run_negative_tests(exercise_dir):
        print("ERROR: One or more invalid metadata fixtures did not fail as expected!", file=sys.stderr)
        sys.exit(1)

    print("Path and configuration check passed: real metadata valid and 3 defect fixtures caught.")


if __name__ == "__main__":
    main()
