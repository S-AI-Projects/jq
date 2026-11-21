# Armstrong Numbers Reference Implementation Refactor

## Overview
This document describes the readability refactoring of the integer exponentiation function `ipow` in `exercises/practice/armstrong-numbers/.meta/example.jq`.

## Background & Motivation
In the original reference implementation, `ipow(num; power)` was implemented using a recursive helper function `_ipow`:
```jq
def ipow(num; power):
  # could be implemented with a reduce, or even `pow|floor`
  def _ipow:
    if first == 0
      then last
      else [first - 1, last * num] | _ipow
    end
  ;
  [power, 1] | _ipow
;
```
While functionally correct, this approach had several drawbacks:
1. **Ambiguous Local State**: State was maintained in an unlabelled 2-element array `[power_remaining, accumulator]`, accessed via `first` and `last`.
2. **Allocation & Recursion Overhead**: Each recursive step constructed a new array `[first - 1, last * num]`.
3. **Idiomatic jq Clarity**: In jq, bounded repetitions with an accumulator are idiomatically expressed using `reduce range(...)`.

## Refactored Implementation
```jq
# Integer exponentiation (num^power) via iterative multiplication.
# Invariant: num^0 == 1 for all base digits; iterative reduction preserves exact integer values without float inaccuracies.
def ipow(num; power):
  reduce range(power) as $_ (1; . * num)
;
```

## Invariants & Equivalence
- **Base Case**: For `power == 0`, `range(0)` generates an empty stream, immediately returning the initial value `1`.
- **Positive Exponents**: For `power > 0`, the accumulator starts at `1` and is multiplied by `num` exactly `power` times.
- **Precision**: Does not introduce floating-point rounding errors that can occur with `pow | floor`.
- **API & Return Types**: The function signature `ipow(num; power)` and its behavior remain identical across all canonical test cases.

## Verification
Automated checks in `work/R07-T004/check.py` verify that all 9 test cases pass and the learner starter stub remains unsolved.
