# Pangram Test Generation & Maintenance Guide

## Overview
This document specifies the exact route from canonical problem specifications and `.meta/tests.toml` to the generated Bats test file `exercises/practice/pangram/test-pangram.bats`.

## Generation Pipeline
- **Generator Entrypoint**: `bin/test-generator`
- **Template**: `exercises/practice/pangram/.meta/template.j2`
- **Config & Inclusions**: `exercises/practice/pangram/.meta/tests.toml`
- **Problem Specifications Cache**: `$XDG_CACHE_HOME/exercism/configlet/problem-specifications/exercises/pangram/canonical-data.json`

## Hand-Maintained vs Generated Files
- **Maintained by hand**:
  - `exercises/practice/pangram/.meta/config.json`: exercise metadata and file declarations
  - `exercises/practice/pangram/.meta/example.jq`: canonical reference implementation
  - `exercises/practice/pangram/pangram.jq`: unsolved learner starter stub
  - `exercises/practice/pangram/.meta/template.j2`: Jinja2 template rendering Bats test blocks
  - `exercises/practice/pangram/.meta/tests.toml`: inclusion/exclusion flags and reimplementation pointers
- **Generated**:
  - `exercises/practice/pangram/test-pangram.bats`: Bats test suite produced by `bin/test-generator`

## Exact Reproduction Command
To regenerate the test suite deterministically:
```bash
XDG_CACHE_HOME="$HOME/Library/Caches" ./bin/test-generator --no-pull pangram
```

## Anchor Case Mapping

| Test Name / Case | UUID | Source Property | Input Sentence | Expected Output | Generator Mapping |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `empty sentence` | `64f61791-508e-4f5c-83ab-05de042b0149` | `isPangram` | `""` | `false` | Rendered into `@test "empty sentence"` with skipped comment on first test |
| `perfect lower case` | `74858f80-4a4d-478b-8a5e-c6477e4e4e84` | `isPangram` | `"abcdefghijklmnopqrstuvwxyz"` | `true` | Rendered into `@test "perfect lower case"` |
| `only lower case` | `61288860-35ca-4abe-ba08-f5df76ecbdcd` | `isPangram` | `"the quick brown fox jumps over the lazy dog"` | `true` | Rendered into `@test "only lower case"` |

## Reproducibility & Timestamp Normalization
Subsequent runs of `bin/test-generator` produce identical test assertions and case ordering. The only line that varies across runs without upstream problem specification updates is the ISO-8601 timestamp in the Bats header:
```bash
# generated on <TIMESTAMP>
```
Normalizing this header line via regular expression `^# generated on .*` yields identical bytes across independent generation passes.
