# Hints

## Approach Selection

When computing Scrabble scores in jq, there are two primary design choices for data representation and character scoring:

### 1. Direct ASCII Array Indexing
- **Representation**: An array where each index corresponds directly to the ASCII codepoint of an uppercase letter (A = 65, ..., Z = 90).
- **Lookup**: Transforming the input word with `ascii_upcase` and `explode` produces integer codepoints that directly index the array (`$tiles[codepoint]`).
- **Trade-offs**: Fast array indexing without string hashing, but requires careful array construction up to index 90 and handling of empty or non-alphabetic inputs.

### 2. Object Dictionary Lookup
- **Representation**: A JSON object mapping uppercase character strings directly to their point values (`{"A": 1, "B": 3, ...}`).
- **Lookup**: Splitting the upper-cased word into character strings with `split("")` and querying the object (`$dict[char]`).
- **Trade-offs**: Highly declarative and self-documenting; however, requires allocating single-character strings for every letter and performing hash table lookups.

### Worked Example: Scrabble Evaluation for `"f"` and `"cabbage"`
- **Input `"f"`**:
  - Normalized: `"F"`
  - Lookup: `"F"` maps to value `4`
  - Total score: `4`
- **Input `"cabbage"`**:
  - Normalized: `"CABBAGE"`
  - Character sequence: `["C", "A", "B", "B", "A", "G", "E"]`
  - Mapped points: `[3, 1, 3, 3, 1, 2, 1]`
  - Total score: `14`
