# Two Bucket Reference Refactoring & Invariants

## Overview
This refactoring improves the clarity and maintainability of `def solve($goal)` in `exercises/practice/two-bucket/.meta/example.jq` without changing public interfaces, dependencies, or algorithmic complexity.

## Key Changes
1. **Explicit Invariant Documentation**: Documented the five-stage deterministic priority rule governing state transitions.
2. **Clarified Local State Variables**: Unpacked `.[0] as $b1`, `.[1] as $b2`, and `.[2] as $moves` at the base-case checks to eliminate obscure indexing in result constructors.
3. **Descriptive Pour Variable**: Renamed ambiguous `$qty` to `$transferQty` for clarity.

## Behavioral Verification
The baseline test cases pass with identical results:
- `Measure using bucket one of size 3 and bucket two of size 5 - start with bucket one`
- `Measure using bucket one of size 3 and bucket two of size 5 - start with bucket two`
- `Measure using bucket one of size 7 and bucket two of size 11 - start with bucket one`
