# Hints

## Approach Selection

When counting nucleotides in jq, there are two primary design approaches:

### Approach 1: Incremental Stream Reduction (Reference)
- **Data Representation**: An accumulator object initialized to `{A: 0, C: 0, G: 0, T: 0}`.
- **Control Flow**: Deconstruct the strand into individual single-character tokens and process them in a single `reduce` loop. At each step, test if the incoming character exists in the accumulator dictionary. If valid, increment the corresponding count; otherwise, halt with an error.
- **Trade-offs**: Performs a single pass over the strand with minimal intermediate allocations beyond character decomposition. Errors are caught eagerly on the first invalid nucleotide.

### Approach 2: Upfront Validation with Multi-pass Filtering (Alternative)
- **Data Representation**: The strand is split into a character array `$chars`, and counts are computed by filtering for each target symbol (`A`, `C`, `G`, `T`).
- **Control Flow**:
  1. Validate the whole string upfront using a regular expression such as `test("^[ACGT]*$")`. If invalid, halt immediately.
  2. For each nucleotide key, filter the character array and take the length.
- **Trade-offs**: Separates validation logic cleanly from aggregation logic. Highly declarative, but scans the character array multiple times (one pass for each nucleotide type) and allocates temporary filtered lists.

### Worked Example: Counting `"G"` or `"AC"`
- Given input `{"strand": "G"}`:
  - Approach 1: Begins with `{A:0, C:0, G:0, T:0}`, sees `"G"`, increments key `"G"`, returning `{"A":0, "C":0, "G":1, "T":0}`.
  - Approach 2: Matches regex `^[ACGT]*$`, decomposes into `["G"]`, evaluates lengths for each of `A` (0), `C` (0), `G` (1), and `T` (0).
