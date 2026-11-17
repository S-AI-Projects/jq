# Hamming Exercise Maintenance

## Canonical Case Decisions & Mapping

The canonical test suite for `hamming` defines 15 cases. In the jq track, 9 cases are active and 6 cases are excluded.
Below is the mapping of all 15 cases with their inclusion status and rationale in jq.

| UUID | Description | Status | Rationale / Reimplementation |
| :--- | :--- | :--- | :--- |
| `f6dcb64f-03b0-4b60-81b1-3c9dbf47e887` | empty strands | Included | Base case: distance between two empty strands is 0. |
| `54681314-eee2-439a-9db0-b0636c656156` | single letter identical strands | Included | Identity check for single character strings; distance is 0. |
| `294479a3-a4c8-478f-8d63-6209815a827b` | single letter different strands | Included | Single character difference; distance is 1. |
| `9aed5f34-5693-4344-9b31-40c692fb5592` | long identical strands | Included | Multi-character identical strands; distance is 0. |
| `cd2273a5-c576-46c8-a52b-dee251c3e6e5` | long different strands | Included | Multi-character differences counted via `explode \| transpose \| map(select(.[0] != .[1])) \| length`. |
| `919f8ef0-b767-4d1b-8516-6379d07fcb28` | disallow first strand longer | Excluded | Superseded by `b9228bb1-465f-4141-b40f-1f99812de5a8` in problem-specifications; jq validates length mismatch via `(.strand1 \| length) == (.strand2 \| length)` and calls `halt_error(1)`. |
| `b9228bb1-465f-4141-b40f-1f99812de5a8` | disallow first strand longer | Included | Reimplements `919f8ef0-b767-4d1b-8516-6379d07fcb28` with standardized error specification. |
| `8a2d4ed0-ead5-4fdd-924d-27c4cf56e60e` | disallow second strand longer | Excluded | Superseded by `dab38838-26bb-4fff-acbe-3b0a9bfeba2d` in problem-specifications; jq validates length mismatch via `(.strand1 \| length) == (.strand2 \| length)` and calls `halt_error(1)`. |
| `dab38838-26bb-4fff-acbe-3b0a9bfeba2d` | disallow second strand longer | Included | Reimplements `8a2d4ed0-ead5-4fdd-924d-27c4cf56e60e` with standardized error specification. |
| `5dce058b-28d4-4ca7-aa64-adfe4e17784c` | disallow left empty strand | Excluded | Original canonical case superseded by `db92e77e-7c72-499d-8fe6-9354d2bfd504` and subsequently `b764d47c-83ff-4de2-ab10-6cfe4b15c0f3` ('disallow empty first strand') to standardize terminology. |
| `db92e77e-7c72-499d-8fe6-9354d2bfd504` | disallow left empty strand | Excluded | Intermediate reimplementation superseded by `b764d47c-83ff-4de2-ab10-6cfe4b15c0f3`. |
| `b764d47c-83ff-4de2-ab10-6cfe4b15c0f3` | disallow empty first strand | Included | Active replacement case ensuring strands must be of equal length. |
| `38826d4b-16fb-4639-ac3e-ba027dec8b5f` | disallow right empty strand | Excluded | Superseded by `920cd6e3-18f4-4143-b6b8-74270bb8f8a3` and `9ab9262f-3521-4191-81f5-0ed184a5aa89`. |
| `920cd6e3-18f4-4143-b6b8-74270bb8f8a3` | disallow right empty strand | Excluded | Intermediate reimplementation superseded by `9ab9262f-3521-4191-81f5-0ed184a5aa89`. |
| `9ab9262f-3521-4191-81f5-0ed184a5aa89` | disallow empty second strand | Included | Active replacement case ensuring strands must be of equal length. |

## Implementation Mechanics in jq
The reference implementation enforces string length equality prior to computing character differences:
```jq
assert((.strand1 | length) == (.strand2 | length); "strands must be of equal length")
```
Differences are computed by converting strings to byte arrays (`explode`), pairing codepoints (`transpose`), and counting unequal pairs (`map(select(.[0] != .[1])) | length`).
