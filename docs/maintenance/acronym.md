# Acronym Isolated Test Runner Guide

## Overview
This document specifies the isolated test execution pattern for the `acronym` exercise via `tools/course_checks/r07-t019.py`.

## Tool Requirements & Prerequisites
- **Python**: 3.9+ (utilizing standard library `subprocess`, `tempfile`, `hashlib`, `json`)
- **Bash**: 4.0+ (Homebrew bash providing `readarray`)
- **Bats**: 1.14+ (`bats-core` runner)
- **jq**: 1.7+
- **GNU grep**: `ggrep` supporting PCRE patterns (`-P`)

## Isolation & Invariance Guarantees
1. **Learner Starter File Protection**:
   The learner solution stub `exercises/practice/acronym/acronym.jq` must remain unsolved in the repository working tree.
2. **Cryptographic Hash Invariance**:
   The SHA-256 hash of `acronym.jq` is asserted before and after every execution. Even under error or interrupted runs, the working tree files are untouched.
3. **Sandbox Execution**:
   Tests execute inside an ephemeral temporary directory (`tempfile.TemporaryDirectory`). File paths are resolved dynamically from `.meta/config.json`.
4. **Failure Propagation**:
   The runner accurately propagates child process exit codes and TAP test results. Deliberately failing solutions and zero-test runs are rejected with non-zero status codes.

## Running the Isolated Check
```bash
python3 tools/course_checks/r07-t019.py
```
