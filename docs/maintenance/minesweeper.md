# Minesweeper Test Generation Maintenance

## Overview
This document specifies the test generation and verification pipeline for the `minesweeper` exercise in the jq track.

## Test Generation Command
Test generation is executed using the repository test generator:
```bash
bin/test-generator --no-pull minesweeper
```

### Input Files
1. **Canonical Test Specifications**: `problem-specifications/exercises/minesweeper/canonical-data.json` (upstream canonical cases)
2. **Track Test Configuration**: `exercises/practice/minesweeper/.meta/tests.toml` (controls inclusion/exclusion and reimplementations)
3. **Template**: `exercises/practice/minesweeper/.meta/template.j2` (Jinja2 test template)
4. **Exercise Configuration**: `exercises/practice/minesweeper/.meta/config.json` (defines paths to solution, test, and example files)

### Output Files
- **Generated Test Suite**: `exercises/practice/minesweeper/test-minesweeper.bats`

### Maintained vs Generated Files
- **Maintained by Hand**:
  - `minesweeper.jq`: Learner stub file (must remain unsolved)
  - `.meta/example.jq`: Reference solution
  - `.meta/template.j2`: Jinja2 test template
  - `.meta/config.json`: File mapping configuration
  - `.meta/tests.toml`: Canonical inclusion/exclusion mapping
- **Generated**:
  - `test-minesweeper.bats`: Regenerated automatically by `bin/test-generator`

## Anchored Canonical Cases Mapping

The test-generation path is anchored on three foundational boundary test cases:

| UUID | Case Description | Canonical Input (`minefield`) | Expected Output | Generated Test Header |
| :--- | :--- | :--- | :--- | :--- |
| `0c5ec4bd-dea7-4138-8651-1203e1cb9f44` | no rows | `[]` | `[]` | `@test 'no rows'` |
| `650ac4c0-ad6b-4b41-acde-e4ea5852c3b8` | no columns | `[""]` | `[""]` | `@test 'no columns'` |
| `6fbf8f6d-a03b-42c9-9a58-b489e9235478` | no mines | `["   ", "   ", "   "]` | `["   ", "   ", "   "]` | `@test 'no mines'` |

## Verification
The focused regeneration check `tools/course_checks/r07-t012.py` validates that:
1. Generating tests in two independent temporary copies yields identical test assertions.
2. The only permitted difference is the `# generated on <timestamp>` metadata header.
3. No canonical case is dropped during regeneration.
4. All 12 enabled cases execute and pass against the reference implementation in an isolated sandbox.
