# Knapsack Isolated Test Runner & Maintenance Guide

## Overview

The `knapsack` exercise solves the classic 0/1 knapsack optimization problem: given a maximum weight capacity and a set of items each with a weight and a value, determine the maximum total value that can fit into the knapsack without exceeding capacity.

## Tool Requirements & Prerequisites

The test execution suite and course checks require:
- **Python**: $\ge 3.10$ (standard library only; no external package dependencies)
- **jq**: $\ge 1.8$ (`jq` CLI with raw string and JSON parsing options)
- **Bats**: $\ge 1.10$ (`bats-core` runner)
- **GNU Bash**: $\ge 5.0$
- **GNU Grep**: $\ge 3.8$ (`ggrep` on macOS with PCRE `-P` support)

## Isolated Execution Architecture

To ensure the learner solution stub (`exercises/practice/knapsack/knapsack.jq`) remains strictly unsolved in git commits, test execution takes place entirely within an ephemeral temporary directory:

```
[Repository Root]
├── exercises/practice/knapsack/
│   ├── knapsack.jq (Unsolved Starter Stub - NEVER OVERWRITTEN)
│   ├── test-knapsack.bats
│   └── .meta/example.jq (Reference Solution)
│
└── [Ephemeral Temporary Directory] (mktemp -d)
    ├── knapsack.jq  <-- Copied from .meta/example.jq
    ├── test-knapsack.bats
    ├── bats-extra.bash
    └── bats-jq.bash
```

The runner computes cryptographic SHA-256 hashes of `knapsack.jq` before and after test execution (including in simulated failure runs) to guarantee complete non-interference.

## Anchor Cases

1. `no items` — Input: `{"maximumWeight": 100, "items": []}`, Expected: `0`
2. `one item, too heavy` — Input: `{"maximumWeight": 10, "items": [{"weight": 100, "value": 1}]}`, Expected: `0`
3. `five items (cannot be greedy by weight)` — Input: 5 items where weight-greedy strategy fails, Expected: `145`

## Validation Commands

### 1. Dedicated Reusable Course Runner
```bash
python3 tools/course_checks/r07-t049.py
```
Validates hash invariance, executes all 7 canonical tests in an isolated sandbox, confirms anchor cases, verifies exit codes for failure/zero-test runs, and cleans up temporary files.

### 2. Standard Track Validator
```bash
bin/validate_one_exercise exercises/practice/knapsack
```
Runs the standard Exercism track validation script.
