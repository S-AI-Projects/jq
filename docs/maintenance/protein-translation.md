# Protein Translation: Mutation Analysis & Test Regression

## Overview

In `protein-translation`, an RNA sequence is translated into a list of protein names by chunking the strand into consecutive codons of 3 nucleotides. Translation terminates when a `STOP` codon is encountered, or fails with an error (`Invalid codon`) when an unrecognized or incomplete codon is encountered.

---

## Documented Mutant Implementation

### Mistaken Assumption
When breaking an RNA strand into codons using regular expressions in jq, a common mistake is scanning with fixed-width groups of 3:
```jq
.strand | scan(".{3}")
```
Because `scan(".{3}")` only matches complete 3-character blocks, any trailing remainder of length 1 or 2 is silently omitted from the emitted stream. Consequently, incomplete strands fail to reach the validation and lookup logic.

### Mutant Code
```jq
{
    "AUG": "Methionine", "UUU": "Phenylalanine", "UUC": "Phenylalanine",
    "UUA": "Leucine", "UUG": "Leucine", "UCU": "Serine", "UCC": "Serine",
    "UCA": "Serine", "UCG": "Serine", "UAU": "Tyrosine", "UAC": "Tyrosine",
    "UGU": "Cysteine", "UGC": "Cysteine", "UGG": "Tryptophan",
    "UAA": "STOP", "UAG": "STOP", "UGA": "STOP"
} as $c2p |
[
    label $translate |
    foreach (.strand | scan(".{3}")) as $codon (null; $c2p[$codon];
        if . == "STOP" then break $translate
        elif . then .
        else "Invalid codon" | halt_error
        end
    )
]
```

---

## Rejecting Test Case

- **Test Name**: `Incomplete RNA sequence can't translate`
- **Canonical UUID**: `9d73899f-e68e-4291-b1e2-7bf87c00f024`
- **Test Input**:
  ```json
  {
    "strand": "AUGU"
  }
  ```
- **Expected Behavior**:
  - Exit code: Non-zero (`assert_failure`)
  - Standard error / output: `"Invalid codon"`
- **Mutant Actual Behavior**:
  - Exit code: `0` (`assert_success`)
  - Output: `["Methionine"]`
  - Rejection: Fails Bats assertion `assert_failure`.

---

## Reference Implementation Correctness

The track reference implementation in `.meta/example.jq` scans with:
```jq
.strand | scan(".{1,3}")
```
For input `"AUGU"`, this yields two items in sequence:
1. `"AUG"` -> translates to `"Methionine"`
2. `"U"` -> not present in `$c2p` map -> evaluates to `null` in `$c2p[$codon]` -> triggers `"Invalid codon" | halt_error`.

Thus, trailing partial codons are guaranteed to reach the error branch unless preceded by a valid `STOP` codon.
