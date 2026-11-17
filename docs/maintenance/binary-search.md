# Binary Search Isolated Runner Guide

## Overview
This document specifies the isolated test execution pattern for `binary-search` via `tools/course_checks/r07-t039.py`.

## Requirements & Invariance
1. **Learner Stub Protection**: The learner starter file `binary-search.jq` must remain unsolved in the working tree.
2. **Hash Invariance**: Cryptographic SHA-256 hashes of all files in `exercises/practice/binary-search` must remain strictly identical before and after test runs.
3. **Isolated Testing**: Tests execute against the reference implementation (`.meta/example.jq`) inside a temporary sandbox directory, resolving paths dynamically from `.meta/config.json`.
4. **Temporary Cleanup**: All scratch directories are guaranteed to be cleaned up upon exit.

## Running the Isolated Check
```bash
python3 tools/course_checks/r07-t039.py
```
