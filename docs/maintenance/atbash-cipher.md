# Atbash Cipher Test Generation & Maintenance Guide

## Overview
This document specifies the exact route from canonical problem specifications and `.meta/tests.toml` to the generated Bats test file `exercises/practice/atbash-cipher/test-atbash-cipher.bats`.

## Generation Pipeline
- **Generator Entrypoint**: `bin/test-generator`
- **Template**: `exercises/practice/atbash-cipher/.meta/template.j2`
- **Config & Inclusions**: `exercises/practice/atbash-cipher/.meta/tests.toml`
- **Problem Specifications Cache**: `$XDG_CACHE_HOME/exercism/configlet/problem-specifications/exercises/atbash-cipher/canonical-data.json`

## Reproduction Command
To regenerate the tests deterministically:
```bash
XDG_CACHE_HOME="$HOME/Library/Caches" ./bin/test-generator atbash-cipher
```

## Anchor Case Mapping

| Test Name / Case | Source Property | Input Phrase | Expected Output | Generator Mapping |
| --- | --- | --- | --- | --- |
| `encode:encode yes` | `encode` | `"yes"` | `"bvh"` | Rendered into `@test 'encode:encode yes'` via `template.j2` |
| `encode:encode no` | `encode` | `"no"` | `"ml"` | Rendered into `@test 'encode:encode no'` via `template.j2` |
| `encode:encode OMG` | `encode` | `"OMG"` | `"lnt"` | Rendered into `@test 'encode:encode OMG'` via `template.j2` |

## Reproducibility & Timestamp Normalization
Subsequent runs of `bin/test-generator` yield identical test assertions and case ordering. The only line that changes between runs without cached problem updates is the generated timestamp header:
```bash
# generated on <ISO8601_TIMESTAMP>
```
Normalizing this header produces byte-for-byte identical test suites across multiple generation passes.
