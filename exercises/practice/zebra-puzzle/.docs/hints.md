# Hints

## General
- The Zebra Puzzle is a constraint satisfaction problem involving 5 houses and multiple attributes.

## Language Specifics: Stream Cardinality & `rightOf`

### Boolean Truthiness vs Stream Filtering
In jq, helper predicates like `rightOf` return boolean values:
```jq
def rightOf($house): . == $house + 1;
```

A common pitfall is treating boolean predicates as stream filters:
```jq
# PITFALL: Pipe directly into a boolean predicate
3 | rightOf(5)
```
- The above expression emits `false`.
- Crucially, `false` is a legitimate value in jq; it does **not** prune or terminate the stream!
- If piped into subsequent generator steps, `false` continues downstream rather than halting execution.

### Correct Stream Pruning with `empty`
To prune non-matching permutation branches in a backtracking solver, conditionally emit `empty`:
```jq
# CORRECT: Conditional pruning emitting empty on failure
if 3 | rightOf(2) then "valid" else empty end
```
- When true (`3 == 2 + 1`), it emits `"valid"` (cardinality 1).
- When false (`3 | rightOf(5)`), `else empty end` emits zero outputs (cardinality 0), cleanly terminating that candidate branch.
- Official jq manual reference: [Conditionals and Comparisons](https://jqlang.github.io/jq/manual/#conditionals-and-comparisons).
