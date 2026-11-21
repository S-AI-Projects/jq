# Kindergarten Garden Maintenance & Mutation Analysis

## Overview
This document records a deliberate mutation analysis of the `kindergarten-garden` reference implementation (`.meta/example.jq`) to verify that the canonical test suite distinguishes subtle implementation bugs.

## Reference Implementation vs Mutant

### Original Implementation
```jq
| map(.[$offset * 2:$offset * 2 + 2])
```

### Mutated Implementation
```jq
| map(.[$offset:$offset + 2])
```

## Mistaken Assumption Exposed
The mutation models a common learner mistake: failing to account for the stride of 2 cups per student per row. In this mutant, the student index `$offset` is used directly as the slice start index rather than `$offset * 2`.

- For Alice (`$offset = 0`), the slice is `[0:2]`, which coincidentally matches the correct slice. Thus, single-student tests for Alice pass.
- For Bob (`$offset = 1`), the correct slice is `[2:4]`. The mutant instead extracts `[1:3]`, overlapping with Alice's plants.

## Minimal Rejecting Test Case
The smallest test case in the canonical test suite that rejects this mutant is:

- **Test Name**: `partial garden:garden with two students`
- **Canonical UUID**: `c376fcc8-349c-446c-94b0-903947315757`
- **Input**:
  ```json
  {
    "diagram": "VVCG\nVVRC",
    "student": "Bob"
  }
  ```
- **Expected Outcome**: `["clover","grass","radishes","clover"]`
- **Mutant Outcome**: `["violets","clover","violets","radishes"]`
- **Assertion Result**: The Bats assertion `assert_equal "$output" "$expected"` fails with a non-zero exit code.

## Verification
The automated verification script `work/R07-T003/check.py` validates that:
1. The original reference passes 17/17 tests.
2. The mutated reference is rejected specifically by `partial garden:garden with two students`.
3. The working tree learner starter stub remains unsolved.
