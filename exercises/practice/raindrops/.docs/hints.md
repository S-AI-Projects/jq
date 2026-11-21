# Hints

## General

- The goal is to convert a number to a string based on whether it has 3, 5, or 7 as factors.
- If none of these are factors, return the number itself as a string.

## jq Conditionals & Stream Cardinality

In jq, every expression produces a stream of zero, one, or more values. When accumulating string results sequentially through piped conditional blocks:

```jq
if <condition> then <updated_string> else . end
```

The `else .` branch is critical because it preserves stream cardinality:
- When the condition is met, the pipeline produces the updated string.
- When the condition is not met, the identity filter `.` passes the input string forward unchanged to the next pipe stage.

### Executable Micro-Example

Preserving the accumulator string when a divisibility test fails:
```jq
"" | if (1 % 3 == 0) then . + "Pling" else . end
```
Expected output:
```json
""
```

### Pitfall: Stream Collapse with `empty`

A common pitfall in jq is writing `else empty`:
```jq
"" | if (1 % 3 == 0) then . + "Pling" else empty end
```
Expected output:
No output (empty stream).

Because `empty` generates a stream of 0 items, any subsequent piped filters will never receive an input and will never execute. To maintain an accumulator through piped stages, always use `else .` rather than `else empty`.

For more details on conditional evaluation and stream behavior, see the [jq Manual on Conditionals and Comparisons](https://jqlang.org/manual/#conditionals-and-comparisons).
