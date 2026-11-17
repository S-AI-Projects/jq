#!/usr/bin/env python3
"""Path and configuration validator for sieve (R07-T018)."""

import json
import os
import sys


def validate_config(exercise_dir: str, config_dict: dict = None) -> tuple[bool, str]:
    """Validate files declared in config.json resolve strictly inside exercise_dir without traversal."""
    if config_dict is None:
        config_path = os.path.join(exercise_dir, ".meta/config.json")
        if not os.path.exists(config_path):
            return False, f"Config file not found: {config_path}"
        with open(config_path, "r", encoding="utf-8") as f:
            config_dict = json.load(f)

    files_obj = config_dict.get("files", {})
    required_keys = ["solution", "test", "example"]

    exercise_dir_real = os.path.realpath(exercise_dir)

    for key in required_keys:
        file_list = files_obj.get(key, [])
        if not file_list:
            return False, f"Missing required file role key in files object: {key}"

        for rel_path in file_list:
            # Check for parent traversal
            resolved = os.path.realpath(os.path.join(exercise_dir, rel_path))
            if not resolved.startswith(exercise_dir_real + os.sep) and resolved != exercise_dir_real:
                return False, f"Parent traversal forbidden for {key}: '{rel_path}' resolves outside exercise directory"

            if not os.path.exists(resolved):
                return False, f"Declared {key} file does not exist: '{rel_path}' (resolved: {resolved})"

    # Optional invalidator/editor files
    for key in ["editor", "invalidator"]:
        for rel_path in files_obj.get(key, []):
            resolved = os.path.realpath(os.path.join(exercise_dir, rel_path))
            if not resolved.startswith(exercise_dir_real + os.sep) and resolved != exercise_dir_real:
                return False, f"Parent traversal forbidden for {key}: '{rel_path}'"

    return True, "All declared paths valid and resolved inside exercise directory."


def main():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    exercise_dir = os.path.join(repo_root, "exercises/practice/sieve")

    # 1. Validate real metadata
    valid, msg = validate_config(exercise_dir)
    if not valid:
        print(f"ERROR: Real sieve metadata failed validation: {msg}", file=sys.stderr)
        sys.exit(1)

    print("SUCCESS: Real sieve metadata passed path validation.")


if __name__ == "__main__":
    main()
