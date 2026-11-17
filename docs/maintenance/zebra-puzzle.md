# Zebra Puzzle Semantics & Stream Pruning Guide

## Overview
This document analyzes the semantic behavior of `rightOf` in `exercises/practice/zebra-puzzle/.meta/example.jq`:
```jq
def rightOf($house): . == $house + 1;
```

## Stream Cardinality Analysis
1. `rightOf` produces scalar boolean values (`true` or `false`).
2. In jq streams, values passing through a pipeline are not filtered by boolean evaluation unless guarded by `select(...)` or `if ... then ... else empty end`.
3. In `example.jq`, candidate pruning is achieved in `solveForColour`:
```jq
if $green | rightOf($ivory)
then ($state + ...) | permute5 | solveForNationality($state)
else empty
end
```
Using `else empty` ensures stream cardinality becomes 0 when the positional constraint is violated, terminating search on impossible permutation prefixes.
