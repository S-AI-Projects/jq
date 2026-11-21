# Hints

## General

- The students are arranged in alphabetical order starting with Alice, Bob, Charlie, etc.
- Each student is assigned **two adjacent cups in each row**.
- When computing the slice of cups belonging to a student at position `$offset` (0 for Alice, 1 for Bob, etc.), remember to scale the starting index by `2`:
  - The slice from each row begins at `$offset * 2` and ends at `$offset * 2 + 2`.
  - A common bug is slicing from `$offset` to `$offset + 2` without multiplying by 2. This mistakenly succeeds for Alice because `0 * 2 == 0`, but produces wrong, overlapping cups for subsequent students.

## Diagnostic Example

Consider two students in a garden:
```json
{
  "diagram": "VVCG\nVVRC",
  "student": "Bob"
}
```
- Alice owns columns `0..1` (`"VV"` top row, `"VV"` bottom row).
- Bob owns columns `2..3` (`"CG"` top row, `"RC"` bottom row).
- Reading row-by-row gives `"CG"` then `"RC"`, producing `["clover", "grass", "radishes", "clover"]`.
- If an unscaled offset `1` is used, the slice reads columns `1..2` (`"VC"` and `"VR"`), yielding `["violets", "clover", "violets", "radishes"]`.
