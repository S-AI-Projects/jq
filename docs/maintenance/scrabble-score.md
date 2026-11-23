# Scrabble Score Approach Comparison & Maintenance Guide

## Overview

The `scrabble-score` exercise computes the Scrabble value of a given word according to official letter point assignments.
This guide compares two distinct implementation strategies in jq: the maintained reference technique using direct ASCII array indexing and an independently written alternative using dictionary object lookups.

## Implementation Approaches

### Approach A: Maintained Reference (ASCII Array Indexing)
Defined in `exercises/practice/scrabble-score/.meta/example.jq`:
```jq
(
    []
    | .[65]=1      # A
    | .[66]=3      # B
    | .[67]=3      # C
    | .[68]=2      # D
    | .[69]=1      # E
    | .[70]=4      # F
    | .[71]=2      # G
    | .[72]=4      # H
    | .[73]=1      # I
    | .[74]=8      # J
    | .[75]=5      # K
    | .[76]=1      # L
    | .[77]=3      # M
    | .[78]=1      # N
    | .[79]=1      # O
    | .[80]=3      # P
    | .[81]=10     # Q
    | .[82]=1      # R
    | .[83]=1      # S
    | .[84]=1      # T
    | .[85]=1      # U
    | .[86]=4      # V
    | .[87]=4      # W
    | .[88]=8      # X
    | .[89]=4      # Y
    | .[90]=10     # Z
) as $tiles
| .word
| ascii_upcase
| . + " "               # no empty strings
| explode
| map($tiles[.] // 0)
| add
```

### Approach B: Alternative Technique (Object Dictionary Lookup)
```jq
.word as $w
| {
    "A": 1, "E": 1, "I": 1, "O": 1, "U": 1, "L": 1, "N": 1, "R": 1, "S": 1, "T": 1,
    "D": 2, "G": 2,
    "B": 3, "C": 3, "M": 3, "P": 3,
    "F": 4, "H": 4, "V": 4, "W": 4, "Y": 4,
    "K": 5,
    "J": 8, "X": 8,
    "Q": 10, "Z": 10
  } as $points
| ($w // "")
| ascii_upcase
| split("")
| map($points[.] // 0)
| add // 0
```

## Comparative Analysis & Trade-offs

| Criterion | Approach A (ASCII Array Indexing) | Approach B (Object Dictionary Lookup) |
|-----------|----------------------------------|---------------------------------------|
| **Data Structure** | 91-element sparse array indexed by ASCII byte value | JSON Key-Value Map |
| **String Traversal** | `explode` yields integer codepoint stream | `split("")` yields 1-character string array |
| **Lookup Operation** | Direct integer indexing `.[codepoint]` ($O(1)$) | String hash table lookup `.[char]` |
| **Edge Cases** | Requires appending dummy whitespace to prevent empty array reduction issues with `explode` | Handles `null` or empty strings directly via `($w // "")` and default fallback `// 0` |
| **Readability** | High boilerplate array creation; obscure ASCII constants (65-90) | Explicit, declarative, self-documenting Scrabble tile values |

## Parity & Benchmark Verification

Both implementations were verified against all 11 canonical test cases with 100% agreement:

| Case Description | Input (`word`) | Expected Score | Approach A Result | Approach B Result |
|------------------|----------------|----------------|-------------------|-------------------|
| `lowercase letter` | `"a"` | `1` | `1` | `1` |
| `uppercase letter` | `"A"` | `1` | `1` | `1` |
| `valuable letter` | `"f"` | `4` | `4` | `4` |
| `short word` | `"at"` | `2` | `2` | `2` |
| `medium word` | `"street"` | `6` | `6` | `6` |
| `medium, valuable word` | `"quirky"` | `22` | `22` | `22` |
| `long, mixed-case word` | `"OxyphenButazone"` | `41` | `41` | `41` |
| `english-like word` | `"pinata"` | `8` | `8` | `8` |
| `empty input` | `""` | `0` | `0` | `0` |
| `entire alphabet available` | `"abcdefghijklmnopqrstuvwxyz"` | `87` | `87` | `87` |

## Automated Verification

Run the parity checker:
```bash
python3 work/R07-T046/check.py
```
This runs both implementations in independent isolated temporary directories, verifies test equivalence, and checks that the learner starter file remains unsolved.
