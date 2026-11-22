# Hints

## Structure of the Song

Each verse follows a repetitive 4-line stanza:
1. `<Count> green bottle(s) hanging on the wall,`
2. `<Count> green bottle(s) hanging on the wall,`
3. `And if one green bottle should accidentally fall,`
4. `There'll be <count - 1> green bottle(s) hanging on the wall.`

Between consecutive verses, an empty string line `""` acts as a delimiter in the final array output.

## Approach Selection

When implementing this in `jq`, consider two main structural approaches:

### Approach 1: Direct Index-Mapped Array with String Interpolation
- **Data Representation**: Store English number words in an array indexed by integer `0` through `10`:
  `["No", "One", "Two", ..., "Ten"]`.
- **Formatting**:
  - Dynamically attach `" green bottle"` followed by `"s"` if the count is not `1`.
  - For line 4, evaluate the decrement `(. - 1)` and transform the number word to lowercase (e.g., using `ascii_downcase`).
- **Verse Iteration**:
  - Use `range(.startBottles; .startBottles - .takeDown; -1)` to generate verses as line arrays prepended with an empty string `""`, then flatten with `add` and drop the initial leading blank line.
- **Trade-offs**: Very concise and idiomatic in jq; minimizes redundant code.

### Approach 2: Modular Single-Verse Constructor with Reducer
- **Data Representation**: Decompose the logic into dedicated helper functions:
  - `number_word($n)`: Maps integer to word string.
  - `bottle_phrase($n; $capitalize)`: Formats number and handles singular vs plural suffix (`"bottle"` vs `"bottles"`).
  - `verse($n)`: Returns the 4-line array for a single bottle count.
- **Verse Iteration**:
  - Collect verses into an array using `[ range(...) | verse(.) ]` and join them using `reduce` or interspersing `""`.
- **Trade-offs**: Clean separation of responsibilities, making single verses easy to test and debug independently, with slightly more helper definitions.

## Worked Example: Handling the Plural-to-Singular Transition

Consider input:
```json
{
  "startBottles": 2,
  "takeDown": 1
}
```
- **Initial Count (`2`)**:
  - Lines 1 and 2 start with capitalized `"Two"` and use the plural `"green bottles"`.
- **Decremented Count (`1`)**:
  - Line 4 decrements to `1`, uses lowercase `"one"`, and must drop the plural suffix to produce `"one green bottle"`.
- **Expected Output**:
  ```json
  [
    "Two green bottles hanging on the wall,",
    "Two green bottles hanging on the wall,",
    "And if one green bottle should accidentally fall,",
    "There'll be one green bottle hanging on the wall."
  ]
  ```
