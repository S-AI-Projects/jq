# Yacht Contract Guidance & Maintenance Guide

## Overview

The `yacht` exercise computes the score of a 5-dice roll given one of twelve Yacht scoring categories.
This document details the decision table for anchor cases (`Yacht`, `Not Yacht`, and `Ones`), distinguishes specified behavior from out-of-contract inputs, and provides reproducible verification checks.

## Decision Table for Selected Cases

| Test Case Name | Input Dice | Input Category | Rule Specification | Expected Outcome |
|----------------|------------|----------------|--------------------|------------------|
| `Yacht` | `[5, 5, 5, 5, 5]` | `"yacht"` | All 5 dice show the same face ($5$ fives). Score is fixed at 50. | `50` |
| `Not Yacht` | `[1, 3, 3, 2, 5]` | `"yacht"` | Not all 5 dice show the same face. Condition fails. Score is 0. | `0` |
| `Ones` | `[1, 1, 1, 3, 5]` | `"ones"` | Three dice show face value 1. Score is $3 \times 1 = 3$. | `3` |

## Contract Boundaries & Invariants

- **Specified Invariants**:
  - Dice array ordering is arbitrary; permutations of dice must evaluate identically.
  - Number categories (`ones` through `sixes`) sum only the dice matching that face value.
  - Category comparison is case-sensitive and uses lowercase strings.
- **Unspecified Inputs**:
  - Malformed rolls (e.g. fewer or greater than 5 dice, die values $<1$ or $>6$).
  - Unknown category names.
  - Non-numeric or null values.
  The reference implementation and test suite assume inputs adhere to the valid domain; no defensive exception or coercion logic is required.

## Verification

To run the contract checker:
```bash
python3 work/R07-T050/check.py
```
Or execute the track runner:
```bash
bin/validate_one_exercise exercises/practice/yacht
```
