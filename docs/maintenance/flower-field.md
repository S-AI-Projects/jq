# Flower Field: Isolated Test Runner & Maintenance Guide

## Overview

The `flower-field` exercise annotates a grid representing a garden of flowers (`*`) and empty spaces (`.`), counting the number of horizontally, vertically, and diagonally adjacent flowers for each empty cell (analogous to the Minesweeper board annotation).

This document details the isolated test execution route, tool prerequisites, and non-destructive execution policy ensuring learner solution files remain untouched in the working tree.

---

## Tool Requirements & Prerequisites

The test execution suite and course checks require:
- **Python**: $\ge 3.10$ (standard library only; no external package dependencies)
- **jq**: $\ge 1.8$ (`jq` CLI with `-s`, `-R`, `-c` slurp and raw string options)
- **Bats**: $\ge 1.10$ (`bats-core` runner)
- **GNU Bash**: $\ge 5.0$
- **GNU Grep**: $\ge 3.8$ (`ggrep` on macOS with PCRE `-P` support)

---

## Isolated Execution Architecture

Exercism exercises maintain a learner solution stub (`exercises/practice/flower-field/flower-field.jq`) that must remain pristine and unsolved in git commits. To validate reference implementations without polluting or modifying learner files, testing must execute inside an ephemeral directory:

```
[Repository Root]
├── exercises/practice/flower-field/
│   ├── flower-field.jq (Unsolved Stub - NEVER OVERWRITTEN)
│   ├── test-flower-field.bats
│   └── .meta/example.jq (Reference Solution)
│
└── [Ephemeral Temporary Directory] (mktemp -d)
    ├── flower-field.jq  <-- Copied from .meta/example.jq
    ├── test-flower-field.bats
    ├── bats-extra.bash
    └── bats-jq.bash
```

---

## Validation Commands

### 1. Dedicated Reusable Course Runner
```bash
python3 tools/course_checks/r07-t059.py
```
This script validates file integrity, executes all 12 canonical tests in an isolated sandbox, verifies anchor cases (`no columns`, `no flowers`, `vertical line`), and confirms that `flower-field.jq` in the working tree remains completely unaltered.

### 2. Standard Track Validator
```bash
bin/validate_one_exercise exercises/practice/flower-field
```
Runs the standard Exercism track validation script, which verifies TAP test output and ensures zero commented skips.
