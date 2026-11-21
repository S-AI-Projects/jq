# Raindrops Guidance & Language Construct Analysis

## Overview
This document examines the jq language constructs used in `exercises/practice/raindrops/.meta/example.jq` with particular attention to stream cardinality, piped conditional evaluation, and identity preservation.

## Language Construct in Reference Implementation
The reference implementation uses piped conditional updates to build the output string:
```jq
# add the sounds as applicable
if ($n % 3 == 0) then . + "Pling" else . end |
if ($n % 5 == 0) then . + "Plang" else . end |
if ($n % 7 == 0) then . + "Plong" else . end |
```

### Stream Cardinality and `else .`
In jq, filters evaluate over streams of values. In an `if <cond> then <expr1> else <expr2> end` construct:
1. `else .`: Produces exactly one value (the identity input), maintaining stream cardinality of 1 so subsequent pipe segments execute.
2. `else empty`: Produces zero values, collapsing the stream and short-circuiting all subsequent pipeline stages.

## Micro-Example Comparison

### 1. Correct Identity Preservation
Expression:
```bash
jq -n '"" | if (1 % 3 == 0) then . + "Pling" else . end'
```
Output:
```json
""
```
Cardinality is maintained (1 element), allowing downstream evaluation.

### 2. Contrasting Pitfall (Stream Collapse)
Expression:
```bash
jq -n '"" | if (1 % 3 == 0) then . + "Pling" else empty end'
```
Output:
No output (stream cardinality = 0).

## Automated Verification
Script `work/R07-T007/check.py` asserts:
1. Micro-example 1 outputs `""`.
2. Micro-example 2 produces an empty stream (0 items).
3. The reference implementation passes all 18 canonical tests in an isolated sandbox.
4. The learner starter stub remains unsolved.
