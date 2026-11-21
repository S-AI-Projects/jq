# Alternative Approach for nucleotide-count:
# Upfront regex validation followed by multi-pass character filtering.

.strand
| if test("^[ACGT]*$") | not then "Invalid nucleotide in strand" | halt_error end
| split("") as $chars
| {
    A: ($chars | map(select(. == "A")) | length),
    C: ($chars | map(select(. == "C")) | length),
    G: ($chars | map(select(. == "G")) | length),
    T: ($chars | map(select(. == "T")) | length)
  }
