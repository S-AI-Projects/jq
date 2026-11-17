# Collatz Conjecture Maintenance & Mutation Analysis

## Overview
This document records the mutation analysis performed on the `collatz-conjecture` reference implementation to ensure the test suite rigorously rejects incorrect contracts.

## Mutation Details
- **Target File**: `exercises/practice/collatz-conjecture/.meta/example.jq`
- **Mutant Concept**: Off-by-one termination count on the base case (`.[0] == 1`).
- **Mutation Diff**:
  ```diff
  --- .meta/example.jq
  +++ .meta/mutant.jq
  @@ -3,3 +3,3 @@
       def _steps:
  -        if (.[0] == 1) then .[1]
  +        if (.[0] == 1) then .[1] + 1
           elif (.[0] % 2 == 0) then [.[0] / 2, .[1] + 1] | _steps
  ```

## Rejecting Test Case
- **Test Name**: `zero steps for one`
- **Canonical UUID**: `b01da42a-9ea0-47b7-b088-251f2fc27357`
- **Smallest Valid Input**: `{"number": 1}`
- **Expected Behavior**: Expected output is `0` (zero steps to reach 1 from 1).
- **Mutant Behavior**: Produces output `1`.
- **Test Assertion Result**: BATS test fails with exit status 1 due to mismatch (`output "1" != expected "0"`).

## Test Suite Coverage
All 6 canonical test cases in `test-collatz-conjecture.bats` pass with the valid reference implementation:
1. `zero steps for one` (input: 1 -> output: 0)
2. `divide if even` (input: 16 -> output: 4)
3. `even and odd steps` (input: 12 -> output: 9)
4. `large number of even and odd steps` (input: 1000000 -> output: 152)
5. `zero is an error` (input: 0 -> error: "Only positive integers are allowed")
6. `negative value is an error` (input: -15 -> error: "Only positive integers are allowed")
