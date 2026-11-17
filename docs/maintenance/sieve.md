# Sieve Exercise Maintenance & File Mapping

## File-Role Map
The metadata file `exercises/practice/sieve/.meta/config.json` governs file discovery and role assignment:

| Role Key | Declared Path | Description | Type |
| :--- | :--- | :--- | :--- |
| `solution` | `sieve.jq` | Starter solution stub provided to learners. Must remain unsolved in repo. | Maintained |
| `test` | `test-sieve.bats` | BATS test suite generated from canonical data or maintained for the track. | Generated / Maintained |
| `example` | `.meta/example.jq` | Reference implementation used to validate track test suite. | Maintained |
| `invalidator` | `bats-extra.bash`, `bats-jq.bash` | Track test helpers that trigger test invalidation on changes. | Maintained |

## Runner File Resolution Mechanics
The track validation harness `bin/validate_one_exercise` operates as follows:
1. Receives the exercise directory path as `$1` (e.g. `exercises/practice/sieve`).
2. Reads the configuration file `.meta/config.json` via `jq`:
   ```bash
   stub=$(jq -r '.files.solution[0]' "$config")
   tests=$(jq -r '.files.test[0]' "$config")
   solution=$(jq -r '.files.example[0] // .files.exemplar[0]' "$config")
   ```
3. Resolves each relative path strictly within `$1`:
   - Stub: `exercises/practice/sieve/sieve.jq`
   - Tests: `exercises/practice/sieve/test-sieve.bats`
   - Reference: `exercises/practice/sieve/.meta/example.jq`
4. Creates an isolated temporary directory, stages `solution` as `$stub`, stages `$tests`, and executes BATS tests with skipped tests enabled (`BATS_RUN_SKIPPED=true`).

## Path & Boundary Guarantees
- All declared files must exist and resolve strictly within `exercises/practice/sieve`.
- Directory traversal sequences (`../`) that escape the exercise boundary are prohibited and rejected by `tools/course_checks/r07-t018.py`.

## Validation Commands
```bash
# Validate metadata configuration and path containment:
python3 tools/course_checks/r07-t018.py

# Validate test execution against the reference:
bin/validate_one_exercise exercises/practice/sieve
```
