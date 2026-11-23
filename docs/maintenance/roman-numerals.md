# Roman Numerals Metadata & Maintenance Guide

## Overview

The `roman-numerals` exercise converts modern Arabic numbers into Roman numerals.
This document details the file-role mapping defined in `exercises/practice/roman-numerals/.meta/config.json`, explains how the track test runner discovers files, and documents the configuration validation suite.

## Exercise File-Role Mapping

All files defined in `.meta/config.json` resolve relative to `exercises/practice/roman-numerals/`:

| Config Role Key | Mapped Path | File Nature | Description |
|-----------------|-------------|-------------|-------------|
| `files.solution` | `roman-numerals.jq` | Hand-maintained | Learner starter stub; must remain strictly unsolved in the repository. |
| `files.test` | `test-roman-numerals.bats` | Generated artifact | Bats test suite generated from canonical specifications. |
| `files.example` | `.meta/example.jq` | Hand-maintained | Track reference implementation used for test validation. |
| `files.invalidator` | `bats-extra.bash`, `bats-jq.bash` | Track shared assets | Helper libraries providing Bats assertion helpers. |

## Test Runner Discovery Mechanism

The track test runner (`bin/validate_one_exercise`) inspects `.meta/config.json` using `jq`:
1. **Locate Stub**: Reads `.files.solution[0]` to find `roman-numerals.jq`.
2. **Locate Tests**: Reads `.files.test[0]` to identify `test-roman-numerals.bats`.
3. **Locate Reference**: Reads `.files.example[0] // .files.exemplar[0]` to resolve `.meta/example.jq`.

Because the runner resolves relative to the exercise root directory, any path misconfiguration or missing file causes immediate runner failure.

## Metadata Integrity & Negative Fixture Checks

The configuration validator (`tools/course_checks/r07-t048.py`) verifies that the real metadata passes, and tests three deliberately invalid fixtures:
1. **Fixture 1 (Invalid Solution)**: Points `.files.solution[0]` to non-existent file `missing-stub.jq`. Fails with missing solution error.
2. **Fixture 2 (Invalid Test)**: Points `.files.test[0]` to non-existent file `missing-test.bats`. Fails with missing test suite error.
3. **Fixture 3 (Invalid Example)**: Points `.files.example[0]` to non-existent file `.meta/missing-example.jq`. Fails with missing reference solution error.

## Anchor Cases

1. `1 is I` — Input: `{"number": 1}`, Expected: `"I"`
2. `2 is II` — Input: `{"number": 2}`, Expected: `"II"`
3. `3 is III` — Input: `{"number": 3}`, Expected: `"III"`

## Validation Commands

### 1. Reusable Path & Metadata Checker
```bash
python3 tools/course_checks/r07-t048.py
```

### 2. Coursework Verification Check
```bash
python3 work/R07-T048/check.py
```
