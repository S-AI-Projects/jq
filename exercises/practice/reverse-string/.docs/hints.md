# Hints

## General
- Strings in jq can be split into character streams using `split("")[]` or exploded into codepoint arrays using `explode`.

## Debugging and Accumulator Ordering
- When reversing a string using `reduce ... as $char (""; ...)`, pay careful attention to the concatenation order in the accumulator.
- If you append each character to the end of the accumulator (`. + $char`), the string remains in its original order (`"robot"` remains `"robot"`).
- To reverse the string, each character must be prepended before the accumulated result (`$char + .`).
- Test your logic on simple non-palindromic inputs:
  - Input: `{"value": "robot"}` -> Expected: `"tobor"`
  - If your output produces `"robot"`, verify whether your reduction is appending rather than prepending.
