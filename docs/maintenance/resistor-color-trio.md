# Resistor Color Trio Contract & Maintenance Guide

## Overview
This document analyzes the exact contract specifications, decision mechanics, and boundary conditions for `exercises/practice/resistor-color-trio`.

## Decision Table for Selected Cases

| Case Name | Colors Input | Band Indices / Math | Raw Ohms | Metric Scaling | Formatted JSON Output |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `Orange and orange and black` | `["orange", "orange", "black"]` | `(10 * 3 + 3) * 10^0` | $33$ | $33 < 1000 \implies$ unit `"ohms"` | `{"value": 33, "unit": "ohms"}` |
| `Blue and grey and brown` | `["blue", "grey", "brown"]` | `(10 * 6 + 8) * 10^1` | $680$ | $680 < 1000 \implies$ unit `"ohms"` | `{"value": 680, "unit": "ohms"}` |

## Prefix Reduction Mechanics
In `exercises/practice/resistor-color-trio/.meta/example.jq`:
```jq
def labelled($unit):
    def get_prefix_idx:
        if .value == 0 or .value % 1000 != 0
          then .
          else .value /= 1000 | .idx += 1 | get_prefix_idx
        end;

    {value: ., idx: 0}
    | get_prefix_idx
    | {value, unit: (["", "kilo", "mega", "giga"][.idx] + $unit)};
```
- Value `33`: `33 % 1000 != 0` $\to$ halts at index 0 $\to$ `"ohms"`.
- Value `680`: `680 % 1000 != 0` $\to$ halts at index 0 $\to$ `"ohms"`.
- Value `2000`: `2000 % 1000 == 0` $\to$ `value = 2, idx = 1` $\to$ `"kiloohms"`.

## Contract Boundaries vs Unspecified Behavior
- **Specified**:
  - The first 3 items in `.colors` represent color names from the standard resistor code.
  - Extra items (e.g. 4th band) must be discarded without raising an error (`Ignore extra colors`).
  - Resistance values that are exact positive multiples of 1000 must be scaled into the appropriate metric prefix (`kiloohms`, `megaohms`, `gigaohms`).
- **Unspecified**:
  - Inputs with fewer than 3 elements or invalid color names are not specified in canonical problem specifications; implementations must not invent custom error behaviors or orderings outside the specification.

## Verification
The automated verification script `work/R07-T010/check.py` validates that:
1. Both selected cases match the decision table exactly against the reference implementation.
2. All 10 canonical test cases pass in an isolated sandbox.
3. The learner starter stub remains unsolved.
