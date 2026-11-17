# Reverse String Mutation & Regression Analysis

## Overview
This study validates that the existing canonical test suite catches subtle ordering mistakes in `reverse-string`.

## Reference Implementation
```jq
.value | reduce split("")[] as $char (""; $char + .)
```

## Deliberate Mutation: Accumulator Append
```jq
.value | reduce split("")[] as $char (""; . + $char)
```
- **Mistaken Assumption**: Assuming that reducing left-to-right with string concatenation reverses the elements, when appending actually preserves input order.
- **Passing Cases**:
  - `an empty string` (UUID `c3b7d806-dced-49ee-8543-933fd1719b1c`): `"" -> ""` passes.
  - `a palindrome` (UUID `1f8ed2f3-56f3-459b-8f3e-6d8d654a1f6c`): `"racecar" -> "racecar"` passes.
- **Rejecting Test Cases**:
  - `a word` (UUID `01ebf55b-bebb-414e-9dec-06f7bb0bee3c`):
    - Input: `{"value": "robot"}`
    - Expected Output: `"tobor"`
    - Mutant Output: `"robot"` (Assertion Failure: `robot != tobor`).
  - `a capitalized word` (UUID `0f7c07e4-efd1-4aaa-a07a-90b49ce0b746`):
    - Input: `{"value": "Ramen"}`
    - Expected Output: `"nemaR"`
    - Mutant Output: `"Ramen"` (Assertion Failure: `Ramen != nemaR`).
