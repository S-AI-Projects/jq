#!/usr/bin/env python3
"""Reusable regeneration check for pangram (R07-T002)."""

import os
import re
import shutil
import subprocess
import sys
import tempfile


def normalize_bats(text):
    return [re.sub(r"# generated on .*", "# generated on <NORMALIZED>", l) for l in text.splitlines()]


def verify_regeneration(repo_root):
    exercise_rel = "exercises/practice/pangram"
    exercise_dir = os.path.join(repo_root, exercise_rel)
    gen_script = os.path.join(repo_root, "bin/test-generator")

    with tempfile.TemporaryDirectory() as tmp1, tempfile.TemporaryDirectory() as tmp2:
        for tdir in (tmp1, tmp2):
            shutil.copytree(repo_root, os.path.join(tdir, "repo"), ignore=shutil.ignore_patterns(".git", ".venv", "work"))
            env = os.environ.copy()
            env["XDG_CACHE_HOME"] = os.path.expanduser("~/Library/Caches")
            python_bin_dir = os.path.dirname(sys.executable)
            env["PATH"] = f"{python_bin_dir}:/opt/homebrew/bin:{env.get('PATH', '')}"
            res = subprocess.run(
                [sys.executable, "./bin/test-generator", "--no-pull", "pangram"],
                cwd=os.path.join(tdir, "repo"),
                capture_output=True,
                text=True,
                env=env
            )
            if res.returncode != 0:
                print(f"Generator failed in {tdir}:\n" + res.stdout + "\n" + res.stderr, file=sys.stderr)
                return False

        t1 = os.path.join(tmp1, "repo", exercise_rel, "test-pangram.bats")
        t2 = os.path.join(tmp2, "repo", exercise_rel, "test-pangram.bats")
        norm1 = normalize_bats(open(t1).read())
        norm2 = normalize_bats(open(t2).read())

        if norm1 != norm2:
            print("ERROR: Test generation outputs differ across fresh runs!", file=sys.stderr)
            return False

        content = "\n".join(norm1)
        for anchor in ("empty sentence", "perfect lower case", "only lower case"):
            if anchor not in content:
                print(f"ERROR: Missing anchor case '{anchor}' in generated tests!", file=sys.stderr)
                return False

    return True


if __name__ == "__main__":
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    if not verify_regeneration(repo_root):
        sys.exit(1)
    print("Regeneration check passed successfully.")
