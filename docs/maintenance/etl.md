# ETL Language Guidance & Maintenance Guide

## Overview

The `etl` exercise converts legacy Scrabble score data (grouped by score: `{ "1": ["A", "E"] }`) into a modern format where each lowercase letter maps to its point value (`{ "a": 1, "e": 1 }`).

## Stream Cardinality & jq Mechanics

The reference implementation in `.meta/example.jq`:
```jq
[
    .legacy | to_entries[] |
    {
        key: (.value[] | ascii_downcase),
        value: (.key | tonumber)
    }
]
| sort_by(.key)
| from_entries
```

### Key Language Concepts
- **`to_entries` & Array Streaming**: Unwraps legacy map into stream of `{key, value}` entry objects.
- **Stream Cardinality (`.value[]`)**: Inside the `{key: ..., value: ...}` literal, iterating `.value[]` multiplies stream cardinality: if `.value` has 3 items, jq emits 3 objects.
- **`from_entries`**: Ingests array of `{key, value}` pairs to construct the final inverted object.

## Micro-Examples & Assertions

| Example | Expression | Input | Expected Output |
|---------|------------|-------|-----------------|
| **1** | Stream Cardinality Expansion | `{"1": ["A", "B"]}` | `[{"key": "a", "value": 1}, {"key": "b", "value": 1}]` |
| **2** | Dict Reassembly via `from_entries` | `[{"key": "a", "value": 1}, {"key": "b", "value": 1}]` | `{"a": 1, "b": 1}` |

## Verification

Run the automated check:
```bash
python3 work/R07-T047/check.py
```
Or execute the track validation:
```bash
bin/validate_one_exercise exercises/practice/etl
```
