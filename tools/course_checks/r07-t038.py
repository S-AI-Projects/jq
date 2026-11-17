#!/usr/bin/env python3
"""Path and metadata configuration validator for luhn (R07-T038)."""
import copy
import json
import os
import sys

def validate_config(exercise_dir, config_data):
    files = config_data.get("files", {})
    required_keys = ["solution", "test", "example"]
    for rk in required_keys:
        if rk not in files or not files[rk]:
            raise ValueError(f"Missing required key in files: {rk}")

    for role, paths in files.items():
        for p in paths:
            if ".." in p.split("/"):
                raise ValueError(f"Parent traversal detected in path: {p}")
            full_path = os.path.normpath(os.path.join(exercise_dir, p))
            if not full_path.startswith(exercise_dir):
                raise ValueError(f"Path escapes exercise root: {p}")
            if not os.path.exists(full_path):
                raise FileNotFoundError(f"Declared file not found on disk: {p}")

    return True

def main():
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    exercise_dir = os.path.join(root, "exercises/practice/luhn")
    config_path = os.path.join(exercise_dir, ".meta/config.json")

    with open(config_path, "r") as f:
        real_config = json.load(f)

    # 1. Validate real config
    try:
        validate_config(exercise_dir, real_config)
    except Exception as e:
        print(f"ERROR: Real config validation failed: {e}", file=sys.stderr)
        sys.exit(1)

    # 2. Validate fixture 1: missing reference
    cfg_bad_example = copy.deepcopy(real_config)
    cfg_bad_example["files"]["example"] = [".meta/non_existent_example.jq"]
    try:
        validate_config(exercise_dir, cfg_bad_example)
        print("ERROR: Missing example fixture did not fail!", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        pass

    # 3. Validate fixture 2: missing test
    cfg_bad_test = copy.deepcopy(real_config)
    cfg_bad_test["files"]["test"] = ["missing_test.bats"]
    try:
        validate_config(exercise_dir, cfg_bad_test)
        print("ERROR: Missing test fixture did not fail!", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        pass

    # 4. Validate fixture 3: outside exercise / traversal
    cfg_traversal = copy.deepcopy(real_config)
    cfg_traversal["files"]["solution"] = ["../luhn.jq"]
    try:
        validate_config(exercise_dir, cfg_traversal)
        print("ERROR: Traversal fixture did not fail!", file=sys.stderr)
        sys.exit(1)
    except ValueError:
        pass

    print("Metadata check passed successfully for real config and 3 invalid fixtures.")

if __name__ == "__main__":
    main()
