# Beer Song: Maintenance Mapping & Configuration Audit

## Overview

The `beer-song` exercise generates lyrics to the traditional cumulative reverse-counting song *99 Bottles of Beer on the Wall*. Given a starting bottle count and a number of verses to take down, it outputs an array of lyric strings separated by empty lines.

This maintenance document maps the exercise file structure, classifies file maintenance roles, documents the reproducible validation command, and audits the exercise configuration in `.meta/config.json`.

---

## Exercise File Role Map

| File Path | Classification | Maintenance Role / Purpose | `config.json` Key |
| :--- | :--- | :--- | :--- |
| `exercises/practice/beer-song/beer-song.jq` | Hand-Maintained | Learner solution stub; must remain strictly unsolved (`halt_error`). | `files.solution` |
| `exercises/practice/beer-song/test-beer-song.bats` | Generated / Hand-Managed | Bats test suite defining 8 canonical TAP tests. | `files.test` |
| `exercises/practice/beer-song/.meta/config.json` | Hand-Maintained | Exercise metadata, author tracking, and track file mappings. | N/A (Root exercise manifest) |
| `exercises/practice/beer-song/.meta/example.jq` | Hand-Maintained | Track reference implementation passing all test cases. | `files.example` |
| `exercises/practice/beer-song/.meta/tests.toml` | Track-Maintained | Canonical test case inclusion and exclusion manifest. | N/A (Configlet sync tracking) |
| `exercises/practice/beer-song/bats-extra.bash` | Track Helper | Shared Bats assertions library (`assert_success`, `assert_equal`). | `files.invalidator` |
| `exercises/practice/beer-song/bats-jq.bash` | Track Helper | Track-specific Bats helper for executing `jq` scripts. | `files.invalidator` |
| `exercises/practice/beer-song/.docs/instructions.md` | Problem Spec Sync | Problem description, constraints, and problem background. | N/A (Shared Exercism spec) |

---

## Configuration Audit (`.meta/config.json`)

The path and configuration checker (`tools/course_checks/r07-t058.py`) audited `.meta/config.json` against filesystem reality:
- `files.solution[0]` resolves to `beer-song.jq` (verified present on disk).
- `files.test[0]` resolves to `test-beer-song.bats` (verified present on disk).
- `files.example[0]` resolves to `.meta/example.jq` (verified present on disk).
- `files.invalidator` entries resolve to `bats-extra.bash` and `bats-jq.bash` (verified present on disk).

**Conclusion**: The configuration in `.meta/config.json` matches filesystem reality 100%; no path discrepancies exist.

---

## Reproducible Validation Command

To validate the reference implementation in an isolated environment without modifying learner files:

```bash
bin/validate_one_exercise exercises/practice/beer-song
```

### Execution Flow:
1. `bin/validate_one_exercise` creates a temporary directory (`mktemp -d`).
2. Copies `.meta/example.jq` to `beer-song.jq`, copies `test-beer-song.bats`, and copies `bats-*.bash`.
3. Runs `BATS_RUN_SKIPPED=true bats test-beer-song.bats`.
4. Asserts all 8 TAP tests pass with return code 0.
5. Deletes the temporary directory on trap exit.
