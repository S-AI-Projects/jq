# Hints

## Language-Specific Guidance: Array Construction & Stack Manipulation

In Forth, the evaluation stack stores integer values. In jq, the stack is represented as a JSON array of integers (`{"stack": [...]}`).

### Array Construction in `push`
The reference implementation defines the push operation as:
```jq
def push($num): .stack += [$num];
```

In jq, the addition operator `+` performs array concatenation only when both operands are arrays. Therefore, the single scalar integer `$num` must be wrapped in square brackets `[$num]` to construct a single-element array before adding.

#### Executable Micro-Example
When appending integer `3` to an existing stack `[1, 2]`:
```bash
$ jq -c -n '{"stack": [1, 2]} | .stack += [3]'
{"stack":[1,2,3]}
```
**Expected Output**:
`{"stack":[1,2,3]}`

### The Contrasting Pitfall
If the enclosing brackets are omitted (`.stack += $num`), jq attempts to add a scalar number to an array:
```bash
$ jq -c -n 'try ({"stack": [1, 2]} | .stack += 3) catch .'
"array ([1,2]) and number (3) cannot be added"
```
**Why the Outcomes Differ**:
Unlike languages that permit implicit element coercion during array insertion, jq's `+` operator strictly requires type matching. Adding an array and a number results in a fatal runtime error (`array and number cannot be added`).

### Handling Negative Numbers
When parsing tokens, note that `"-1" | tonumber` evaluates to `-1` (a negative integer pushed to the stack), whereas the single dash `"-"` represents subtraction. Wrapping `tonumber` in `try ... catch false` provides a reliable predicate for distinguishing numbers from arithmetic operators.

For more details on jq array concatenation and operators, refer to the [jq Manual: Addition](https://jqlang.github.io/jq/manual/v1.7/#addition-).
