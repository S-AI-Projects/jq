# Luhn Maintenance & Metadata Path Mapping

## Overview
This document specifies the file-role mappings declared in `exercises/practice/luhn/.meta/config.json` and details how the test runner discovers test and reference files.

## File Role Mappings
- **Solution Stub (`files.solution`)**: `luhn.jq` - unsolved starter template provided to learners.
- **Test Suite (`files.test`)**: `test-luhn.bats` - generated Bats test file covering all canonical cases.
- **Reference Implementation (`files.example`)**: `.meta/example.jq` - track reference solution used to validate test suites.
- **Invalidator Files (`files.invalidator`)**: `bats-extra.bash`, `bats-jq.bash` - test runner support libraries.

## Path Resolution Invariants
All paths declared in `config.json` must:
1. Resolve strictly within `exercises/practice/luhn`.
2. Prohibit parent directory traversal (`..`).
3. Exist on disk.

## Validation Command
```bash
python3 tools/course_checks/r07-t038.py
```
