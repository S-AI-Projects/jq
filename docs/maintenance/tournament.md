# Tournament Test Generation & Maintenance Guide

## Overview

The `tournament` exercise tallies the results of small football competitions given a list of played matches, and outputs a formatted scoreboard.

## Test Generation Route

The test suite `exercises/practice/tournament/test-tournament.bats` is generated from canonical problem specifications using Jinja2 templates.

### Input Files
1. **Canonical Test Specifications**: `problem-specifications/exercises/tournament/canonical-data.json`
2. **Track Case Inclusion Configuration**: `exercises/practice/tournament/.meta/tests.toml`
3. **Track Bats Template**: `exercises/practice/tournament/.meta/template.j2`

### Exact Generation Command
```bash
bin/test-generator --no-pull tournament
```
The `--no-pull` flag ensures generation uses the cached problem specifications without network dependencies or cache pollution.

### Output File
- `exercises/practice/tournament/test-tournament.bats`

The only dynamic element across regeneration runs is the timestamp in the file header (`# generated on <TIMESTAMP>`). When this timestamp is normalized, successive generations yield bit-for-bit identical test suites.

## Anchor Cases & Mapping

All 12 canonical test cases are included in `tests.toml`. The three anchor cases are mapped below:

| UUID | Case Description | Input Matches (`rows`) | Expected Scoreboard Output |
|------|------------------|------------------------|---------------------------|
| `67e9fab1-07c1-49cf-9159-bc8671cc7c9c` | `just the header if no input` | `[]` | `Team                           \| MP \|  W \|  D \|  L \|  P` |
| `1b4a8aef-0734-4007-80a2-0626178c88f4` | `a win is three points, a loss is zero points` | `["Allegoric Alaskans;Blithering Badgers;win"]` | `Allegoric Alaskans             \|  1 \|  1 \|  0 \|  0 \|  3`<br>`Blithering Badgers            \|  1 \|  0 \|  0 \|  1 \|  0` |
| `5f45ac09-4efe-46e7-8ddb-75ad85f86e05` | `a win can also be expressed as a loss` | `["Blithering Badgers;Allegoric Alaskans;loss"]` | `Allegoric Alaskans             \|  1 \|  1 \|  0 \|  0 \|  3`<br>`Blithering Badgers            \|  1 \|  0 \|  0 \|  1 \|  0` |

## Validation Commands

### 1. Reusable Course Regeneration Check
```bash
python3 tools/course_checks/r07-t042.py
```
This check verifies that:
- Regeneration from `template.j2` and `tests.toml` is completely deterministic (timestamp-normalized comparison passes).
- Reference solution in `.meta/example.jq` passes all 12 generated test cases.
- Working tree learner stub `tournament.jq` remains unsolved and untouched.

### 2. Isolated Verification Runner
```bash
python3 work/R07-T042/check.py
```
Runs the suite in an isolated temporary environment and saves run evidence.
