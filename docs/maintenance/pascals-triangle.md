# Pascal's Triangle Maintained Files & Metadata Map

## Overview
This document specifies the file-role mappings, path resolution guarantees, and validation mechanisms for `exercises/practice/pascals-triangle`.

## File-Role Map

| Declared Path | Role in `config.json` | Nature | Description |
| :--- | :--- | :--- | :--- |
| `pascals-triangle.jq` | `files.solution` | Hand-Maintained | Unsolved learner starter stub containing the entrypoint contract. |
| `test-pascals-triangle.bats` | `files.test` | Generated Artifact | Bats test suite generated from canonical specifications. |
| `.meta/example.jq` | `files.example` | Hand-Maintained | Reference implementation used for exercise validation. |
| `.meta/config.json` | Metadata | Hand-Maintained | Track metadata defining author, blurb, and file-role mappings. |
| `.meta/tests.toml` | Metadata | Hand-Maintained / Synced | Canonical test case selection flags and reimplementations. |

## Runner Path Resolution Mechanics
The track validation script `bin/validate_one_exercise` locates exercise components by parsing `.meta/config.json`:
1. `stub=$(jq -r '.files.solution[0]' "$config")` resolves `pascals-triangle.jq`.
2. `tests=$(jq -r '.files.test[0]' "$config")` resolves `test-pascals-triangle.bats`.
3. `solution=$(jq -r '.files.example[0] // .files.exemplar[0]' "$config")` resolves `.meta/example.jq`.

The runner then sets up an isolated temporary directory sandbox, copies the reference implementation into `${dir}/${stub}` and `${tests}` into `${dir}/${tests}`, and executes the suite with `bats`.

## Path Traversal and Existence Verification
The custom verification tool `tools/course_checks/r07-t008.py` verifies:
- All paths are strictly relative to the exercise root without parent directory traversal (`..`).
- Every declared file physically exists.
- Negative testing confirms that deliberate defects (`missing-reference`, `missing-test`, and `outside-exercise`) fail with explicit errors.

## Reproducible Validation Commands
```bash
# 1. Run the path/metadata checker
python3 tools/course_checks/r07-t008.py

# 2. Run the full exercise test runner
bin/validate_one_exercise exercises/practice/pascals-triangle
```
