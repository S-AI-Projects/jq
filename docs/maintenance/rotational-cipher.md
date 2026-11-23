# Rotational Cipher Maintenance Guide

## Overview

The `rotational-cipher` exercise implements the Caesar cipher for arbitrary shift keys from 0 to 26.
The reference solution (`.meta/example.jq`) constructs an explicit character translation dictionary using `makeMap($shift)` and recursively translates each character in the input string.

## Readability Refactoring in `makeMap`

### Before
```jq
def makeMap($shift):
  "abcdefghijklmnopqrstuvwxyz" as $lower
  | ($lower | [.[$shift:26], .[0:$shift+1]] | add) as $rotated
  | reduce range(26) as $i ({};
      $lower[$i:$i+1] as $from
      | $rotated[$i:$i+1] as $to
      | . + {($from): $to} + {($from | ascii_upcase): ($to |  ascii_upcase)}
    )
;
```
*Issues in original implementation*:
- `[.[$shift:26], .[0:$shift+1]]` produced an asymmetric 27-character string when `$shift` was 0, relying on `range(26)` index cutoff.
- Repeated object concatenation (`+ {($from): $to} + {($from | ascii_upcase): ...}`) generated multiple temporary objects per iteration.

### After
```jq
# Generates a substitution lookup map for both lowercase and uppercase letters.
# Invariant: Shift distance is normalized modulo 26 ($shift % 26).
# The rotated alphabet is split and re-concatenated ($lower[$s:] + $lower[:$s]),
# preserving 1-to-1 letter mapping for all shifts in range [0, 26].
def makeMap($shift):
  "abcdefghijklmnopqrstuvwxyz" as $lower
  | ($shift % 26) as $s
  | ($lower[$s:] + $lower[:$s]) as $rotated
  | reduce range(26) as $i ({};
      $lower[$i:$i+1] as $from
      | $rotated[$i:$i+1] as $to
      | . + {($from): $to, ($from | ascii_upcase): ($to | ascii_upcase)}
    )
;
```
*Improvements*:
- Explicit invariant normalization: `($shift % 26) as $s`.
- Direct string slicing `($lower[$s:] + $lower[:$s])` accurately yields exactly 26 rotated characters for any `$s`.
- Unified dictionary construction `{($from): $to, ($from | ascii_upcase): ...}` improves clarity and eliminates redundant merge operations.

## Behavioral Baseline & Anchor Cases

The refactored implementation preserves full compatibility with all canonical test cases:

| Case Description | Input (`text`, `shiftKey`) | Expected Result | Invariant Verified |
|------------------|----------------------------|-----------------|--------------------|
| `rotate a by 0, same output as input` | `{"text": "a", "shiftKey": 0}` | `"a"` | Zero shift identity: `$s = 0`, alphabet invariant preserved |
| `rotate a by 1` | `{"text": "a", "shiftKey": 1}` | `"b"` | Standard elementary unit step rotation |
| `rotate a by 26, same output as input` | `{"text": "a", "shiftKey": 26}` | `"a"` | Full circle cycle modulo 26: `26 % 26 = 0` |

## Verification

Run the isolated verification suite:
```bash
python3 work/R07-T044/check.py
```
Or validate through standard track tooling:
```bash
bin/validate_one_exercise exercises/practice/rotational-cipher
```
