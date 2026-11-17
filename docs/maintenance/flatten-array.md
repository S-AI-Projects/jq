# Flatten Array Maintenance & Canonical Case Rationales

## Overview
The `flatten-array` exercise canonical test suite comprises 15 test cases defined in canonical problem specifications:
- 11 cases are included and actively tested.
- 4 cases are excluded because they use "list" phrasing instead of jq's idiomatic "array" data type, and each is replaced by a corresponding jq-specific reimplementation.

## Canonical Case Mapping Table

| UUID | Description / Test Name | Status | Rationale |
| --- | --- | --- | --- |
| `8c71dabd-da60-422d-a290-4a571471fb14` | empty | Included | Base case: empty array `[]` flattens to `[]`. |
| `d268b919-963c-442d-9f07-82b93f1b518c` | no nesting | Included | 1D array `[0, 1, 2]` remains unchanged. |
| `3f15bede-c856-479e-bb71-1684b20c6a30` | flattens a nested array | Included | Verifies multi-level nesting without nulls. |
| `c84440cc-bb3a-48a6-862c-94cf23f2815d` | flattens array with just integers present | Included | Nested integers flattened to 1D list. |
| `d3d99d39-6be5-44f5-a31d-6037d92ba34f` | 5 level nesting | Included | Deep nesting recursion verification. |
| `d572bdba-c127-43ed-bdcd-6222ac83d9f7` | 6 level nesting | Included | Extreme nesting boundary check. |
| `0705a8e5-dc86-4cec-8909-150c5e54fa9c` | null values are omitted from the final result | Included | Verifies filtering of null values via `map(select(. != null))`. |
| `c6cf26de-8ccd-4410-84bd-b9efd88fd2bc` | consecutive null values at the front of the list are omitted from the final result | Excluded | Excluded: problem specification uses "list" naming; replaced by array-named reimplementation `bc72da10-5f55-4ada-baf3-50e4da02ec8e`. |
| `bc72da10-5f55-4ada-baf3-50e4da02ec8e` | consecutive null values at the front of the array are omitted from the final result | Included | Track reimplementation of `c6cf26de` with jq-idiomatic array phrasing. |
| `382c5242-587e-4577-b8ce-a5fb51e385a1` | consecutive null values in the middle of the list are omitted from the final result | Excluded | Excluded: problem specification uses "list" naming; replaced by array-named reimplementation `6991836d-0d9b-4703-80a0-3f1f23eb5981`. |
| `6991836d-0d9b-4703-80a0-3f1f23eb5981` | consecutive null values in the middle of the array are omitted from the final result | Included | Track reimplementation of `382c5242` with jq-idiomatic array phrasing. |
| `ef1d4790-1b1e-4939-a179-51ace0829dbd` | 6 level nest list with null values | Excluded | Excluded: problem specification uses "list" naming; replaced by array-named reimplementation `dc90a09c-5376-449c-a7b3-c2d20d540069`. |
| `dc90a09c-5376-449c-a7b3-c2d20d540069` | 6 level nested array with null values | Included | Track reimplementation of `ef1d4790` with jq-idiomatic array phrasing. |
| `85721643-705a-4150-93ab-7ae398e2942d` | all values in nested list are null | Excluded | Excluded: problem specification uses "list" naming; replaced by array-named reimplementation `51f5d9af-8f7f-4fb5-a156-69e8282cb275`. |
| `51f5d9af-8f7f-4fb5-a156-69e8282cb275` | all values in nested array are null | Included | Track reimplementation of `85721643` with jq-idiomatic array phrasing. |

## Reference Implementation Details
In `exercises/practice/flatten-array/.meta/example.jq`:
```jq
flatten | map(select(. != null))
```
- Built-in `flatten` unwinds all nested arrays recursively.
- `map(select(. != null))` strips out null entries, satisfying the specification.
