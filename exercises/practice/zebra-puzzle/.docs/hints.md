# Hints

## General
- The Zebra Puzzle is a constraint satisfaction problem with 5 houses, each having 5 attributes: color, nationality, pet, beverage, and cigarette brand.
- In jq, backtracking search can be naturally implemented using streams and permutations.

## Language-Specific Guidance: Stream Cardinality & `rightOf`

### Constraint Verification Construct
The reference solution defines the relative position helper at `.meta/example.jq#L43`:

```jq
def rightOf($house): . == $house + 1;
```

This function takes an existing house index (`$house`) and tests whether the current context (`.`) is immediately to its right (`. == $house + 1`), returning boolean `true` or `false`.

### Stream Filtering & Backtracking via `empty`
In a permutation search, candidate state configurations must be pruned immediately when a clue condition is violated. In jq, stream cardinality controls backtracking:
- When a candidate matches a constraint, evaluation proceeds, preserving stream cardinality ($1$).
- When a candidate violates a constraint, emitting `empty` drops the value, reducing stream cardinality to $0$ and backtracking.

Inside `solveForColour`:
```jq
if $green | rightOf($ivory) then
    # Clue satisfied: continue search with valid permutation
    ...
else empty
end
```

### Micro-Example 1: Valid Relation and Pruned Stream
Testing whether house 4 is immediately to the right of house 3:
```bash
jq -n 'def rightOf($house): . == $house + 1; 4 | rightOf(3)'
```
**Expected output:**
```json
true
```

When used in a stream filter with `else empty`:
```bash
jq -n 'def rightOf($house): . == $house + 1; 4 | if rightOf(3) then "valid" else empty end'
```
**Expected output:**
```json
"valid"
```

### Micro-Example 2: Contrasting Pitfall (Boolean Stream vs Empty Stream)
Testing whether house 2 is immediately to the right of house 3:
```bash
jq -n 'def rightOf($house): . == $house + 1; 2 | rightOf(3)'
```
**Expected output:**
```json
false
```

When filtered with `else empty`:
```bash
jq -n 'def rightOf($house): . == $house + 1; 2 | if rightOf(3) then "valid" else empty end'
```
**Expected output:** *(empty stream, 0 outputs)*

#### The Exercise-Relevant Pitfall
A common pitfall is emitting boolean results directly rather than filtering the generator stream:
- **Incorrect (Unpruned Stream)**: `[4, 2] | .[] | rightOf(3)` yields `true` and `false` (cardinality 2). The invalid branch is not pruned because boolean `false` is still an emitted value in the pipeline.
- **Correct (Pruned Stream)**: `[4, 2] | .[] | if rightOf(3) then . else empty end` yields only `4` (cardinality 1). Emitting `empty` on `false` completely removes the invalid house arrangement from subsequent pipeline stages.

For further reference, see the [jq Manual on Conditionals and Comparisons](https://jqlang.github.io/jq/manual/#conditionals-and-comparisons).
