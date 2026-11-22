# Complexity & Invariants:
# - Time Complexity: O(N) where N is the length of the input DNA strand.
#   - split(""): O(N) string-to-array decomposition into N 1-char strings.
#   - map({...}[.]): O(N) lookups into constant-size 4-element translation table.
#   - join(""): O(N) concatenation into resultant RNA complement string.
# - Space Complexity: O(N) auxiliary memory for intermediate JSON array allocations.
# - Contract Invariant: Preserves strand length and nucleotide order; undefined for non-DNA characters.
def toRna:  split("") |
            map({"G":"C", "C":"G", "A":"U", "T":"A"}[.]) |
            join("");
