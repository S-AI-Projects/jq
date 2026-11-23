# Matching Brackets Maintenance Guide

## Overview

The `matching-brackets` exercise determines whether all brackets (`[]`, `{}`, `()`) in a given string are correctly paired and nested.
In jq, the reference implementation (`.meta/example.jq`) strips non-bracket characters with `gsub("[^[\\](){}]"; "")` and recursively collapses adjacent matching bracket pairs using `gsub_recursively("(\\[\\])|(\\(\\))|(\\{\\})"; "")`.

## Canonical Case Rationale & Mapping

All 20 canonical cases are included (0 exclusions). The rationale for the three selected canonical UUIDs is detailed below:

| UUID | Case Name | Input | Expected | jq Reference Mechanism | Coverage Rationale |
|------|-----------|-------|----------|------------------------|--------------------|
| `81ec11da-38dd-442a-bcf9-3de7754609a5` | paired square brackets | `"[]"` | `true` | Retains `"[]"`, collapses via `gsub_recursively` to `""`, evaluates `. == ""` | Baseline verification for simplest balanced square bracket pair. |
| `287f0167-ac60-4b64-8452-a0aa8f4e5238` | empty string | `""` | `true` | Non-bracket stripping leaves `""`, recursion terminates on base case, `. == ""` is `true` | Boundary case: empty input is vacuously balanced without recursive reductions. |
| `6c3615a3-df01-4130-a731-8ef5f5d78dac` | unpaired brackets | `"[["` | `false` | Filtering leaves `"[["`, pattern has no adjacent matching close bracket, recursion halts with residual `"[["` | Negative baseline: ensures unmatched opening brackets are correctly detected as unbalanced. |

## Canonical Case Counts

- Total canonical cases: 20
- Included cases: 20
- Excluded cases: 0

## Verification

To run tests against the reference solution without modifying the learner stub:
```bash
python3 work/R07-T041/check.py
```
Or with track validator:
```bash
bin/validate_one_exercise exercises/practice/matching-brackets
```
