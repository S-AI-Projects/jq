# Hints

## Contract & Decision Table Walkthrough

The `yacht` exercise scores a hand of five dice according to a selected scoring category. The table below connects the specific contract conditions to expected results for key categories:

| Case Description | Input `.dice` | Input `.category` | Condition Evaluated | Expected Score |
|------------------|---------------|-------------------|---------------------|----------------|
| `Yacht` | `[5, 5, 5, 5, 5]` | `"yacht"` | All five dice show identical value | `50` |
| `Not Yacht` | `[1, 3, 3, 2, 5]` | `"yacht"` | Fewer than five dice show identical value | `0` |
| `Ones` | `[1, 1, 1, 3, 5]` | `"ones"` | Sum of all dice showing value `1` ($3 \times 1$) | `3` |

### Jq Representation & Mechanics
- **Input Data**: The input is passed as a JSON object: `{"dice": [d1, d2, d3, d4, d5], "category": "<category-name>"}`.
- **Frequency Counting**: A convenient jq pattern is to compute a frequency array using `reduce`:
  ```jq
  (reduce .dice[] as $d ([null,0,0,0,0,0]; .[$d] += 1)) as $count
  ```
  `$count[1]` gives the number of ones rolled, `$count[5]` gives the number of fives, etc.
- **Yacht Condition**: A Yacht occurs if any face count equals 5 (`5 | IN($count[])`). If this condition is met and `.category == "yacht"`, score `50`; otherwise score `0`.
- **Number Categories (`ones` through `sixes`)**: Multiply the face value by its count in `$count` (e.g. `1 * $count[1]`).

### Contract Invariants & Unspecified Behavior
- **Dice Ordering**: The `.dice` array is unordered. For example, `[1, 1, 1, 3, 5]` and `[3, 1, 5, 1, 1]` must produce identical scores for all categories.
- **Inputs Outside Contract**: The exercise contract specifies that `.dice` always contains exactly five integers between 1 and 6, and `.category` contains a recognized category string. No defensive coercion, error handling, or recovery for non-contract inputs is required.
