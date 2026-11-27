# Zebra Puzzle Guidance & Stream Cardinality Analysis

## Overview
This document supplements `exercises/practice/zebra-puzzle/.docs/hints.md` with detailed analysis of how `rightOf` and stream cardinality interact in constraint solving.

## Linguistic Construct
The helper `rightOf($house)`:
```jq
def rightOf($house): . == $house + 1;
```
operates on integer house indices $1 \dots 5$.

## Stream Semantics & Cardinality
1. **Match**: When `$green | rightOf($ivory)` is `true`, the `then` branch executes, preserving the search branch (cardinality 1).
2. **Mismatch & Pruning**: When `false`, the `else empty` branch produces `empty` (stream cardinality 0), effectively halting traversal down an impossible configuration branch.
3. **Contrast Pitfall**: Direct evaluation `rightOf($house)` returns a boolean token without pruning the generator stream. Stream pruning requires explicit branch discarding via `empty` or `select(...)`.
