# Hints

## General
- A gigasecond is $10^9$ seconds ($1,000,000,000$ seconds).
- Input timestamps may specify either a date only (`YYYY-MM-DD`) or a full date-time (`YYYY-MM-DDTHH:MM:SS`).

## Approach Selection & Trade-Offs

### Approach A: Exception Handling (`fromdateiso8601`)
- Attempts to parse the timestamp directly by appending `"Z"`. If the format lacks a time component, `fromdateiso8601` throws an error which is caught via `try ... catch ...`, where `"T00:00:00Z"` is appended instead.
- **Trade-off**: Concise expression relying on built-in C-level ISO parsing, but relies on exception flow for standard date-only inputs.

### Approach B: Explicit Normalization (`strptime` / `mktime`)
- Normalizes the input string explicitly by testing whether `"T"` is present (`if contains("T") then . else . + "T00:00:00" end`).
- Then parses using `strptime("%Y-%m-%dT%H:%M:%S") | mktime`, adds $10^9$, and formats back with `strftime`.
- **Trade-off**: Clear declarative branching avoiding exception propagation, but requires format string specification.

### Worked Example
- Given input `{"moment": "2011-04-25"}`:
  - Normalized to `"2011-04-25T00:00:00Z"`.
  - Parsed epoch seconds: `1303689600`.
  - Adding $10^9$ yields: `2303689600`.
  - Formatted UTC result: `"2043-01-01T01:46:40"`.
