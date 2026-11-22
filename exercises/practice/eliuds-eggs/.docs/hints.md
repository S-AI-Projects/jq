# Hints

The tests pass a JSON object and the exercise reads its numeric `.number` field.
Count the `1` digits in that value's binary representation:

| Test | Input | Binary | `1` digits | Required result |
| --- | --- | --- | --- | --- |
| 0 eggs | `{"number": 0}` | `0` | `0` | `0` |
| 1 egg | `{"number": 16}` | `10000` | `1` | `1` |
| 4 eggs | `{"number": 89}` | `1011001` | `4` | `4` |

For example, `89` is `1011001` in binary, which contains four `1` digits.
The jq test invokes the solution with `-r`, so the result is a scalar number,
not an object or array. The exercise requires only this count; there is no
ordering requirement.

The exercise does not specify coercion or error behavior for inputs such as a
missing or non-numeric `.number`, non-integers, or negative values. Those
behaviors are outside the examples' input contract and should not be inferred
from these cases.
