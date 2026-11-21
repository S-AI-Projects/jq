# Pig Latin Isolated Test Runner & Maintenance Guide

## Overview
This document specifies the isolated test execution pattern for `exercises/practice/pig-latin` via `tools/course_checks/r07-t009.py`.

## Requirements & Invariance
1. **Learner Stub Protection**: The learner starter stub `exercises/practice/pig-latin/pig-latin.jq` must remain unsolved and untouched in the working tree.
2. **Cryptographic Hash Invariance**: The SHA-256 hash of `pig-latin.jq` is verified before and after every execution pass, ensuring complete zero-mutation of learner files.
3. **Isolated Sandboxing**: Dynamic path resolution reads `.meta/config.json`, copies all files to a clean temporary directory (`tempfile.TemporaryDirectory`), substitutes the reference solution only inside the scratch environment, and invokes `bin/validate_one_exercise`.
4. **Failure Propagation & Zero-Test Detection**: Child return codes are propagated directly. A non-zero exit from Bats or a run producing zero passing tests triggers an immediate non-zero exit from the runner.
5. **Clean Exit**: Scratch files and directories are automatically destroyed upon completion.

## Reproduction Command
```bash
python3 tools/course_checks/r07-t009.py
```

## Test Modes Evaluated
1. **Real Reference**: Executes all 23 canonical tests against `.meta/example.jq` (100% pass rate).
2. **Deliberately Failing Reference**: Evaluates an intentional mutant to confirm child failure detection and return code propagation.
3. **Empty Test Selection**: Evaluates empty test suite behavior to guarantee zero-test runs fail.
