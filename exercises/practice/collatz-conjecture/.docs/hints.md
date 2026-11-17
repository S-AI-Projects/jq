# Hints

## Debugging

- Pay special attention to the base case for the Collatz sequence: reaching the number `1` requires **zero** additional steps.
  - If your algorithm starts with input `1`, no division or multiplication operations are performed, so the step counter should immediately return `0`.
  - A common pitfall is counting the initial state or post-incrementing the step counter when checking `.[0] == 1`, which leads to an off-by-one error where input `1` produces `1` instead of `0`.
- Diagnostic check: verify that your base case terminates immediately with `0` when `{"number": 1}` is provided.
- Remember that positive integers are defined as integers strictly greater than 0 (`> 0`). An input of `0` or negative integers must be rejected with the error `"Only positive integers are allowed"`.
