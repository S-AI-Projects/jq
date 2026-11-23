# Hints

## Language-Specific Guidance (jq)

### Stream Cardinality and Entry Transformation

In jq, expressions produce streams of zero, one, or more values. When transforming the legacy data format (`{ "1": ["A", "E"] }`) into individual letter-to-score mappings, you can take advantage of **stream cardinality** and jq's built-in `to_entries` and `from_entries` functions:

1. **`to_entries`**: Converts an object into an array of `{ "key": ..., "value": ... }` pairs, where `key` is the score string (e.g. `"1"`) and `value` is the array of letters (e.g. `["A", "E"]`).
2. **Cardinality Expansion (`.value[]`)**: Unwrapping `.value[]` inside an object constructor generates a new `{key, value}` object for *each* letter in that score's list:
   - For a score with $K$ letters, evaluating `.value[]` produces $K$ distinct object values.
3. **`from_entries`**: Collapses an array of `{ "key": ..., "value": ... }` pairs back into a single dictionary object.

### Micro-Examples

#### Micro-Example 1: Expanding Nested Values via Stream Cardinality
```jq
{"1": ["A", "B"]} | [to_entries[] | {key: (.value[] | ascii_downcase), value: (.key | tonumber)}]
```
**Expected Output:**
```json
[{"key": "a", "value": 1}, {"key": "b", "value": 1}]
```

#### Micro-Example 2: Reassembling into a Map with `from_entries`
```jq
[{"key": "a", "value": 1}, {"key": "b", "value": 1}] | from_entries
```
**Expected Output:**
```json
{"a": 1, "b": 1}
```

### Exercise-Relevant Pitfalls
- **Array as Key Error**: If you attempt to use `map` on `.value` rather than streaming it via `.value[]`, you will produce `{key: ["a", "b"], value: 1}`. Passing an array as a `key` to `from_entries` triggers a fatal runtime error: `Cannot use array as object key`.
- **String vs Number Scores**: Remember that JSON object keys are always strings. The exercise contract requires the new dictionary values to be integers, so you must convert the legacy score using `tonumber`.

### Language Reference
- [jq Manual: to_entries, from_entries, with_entries](https://jqlang.github.io/jq/manual/v1.7/#to_entries-from_entries-with_entries)
