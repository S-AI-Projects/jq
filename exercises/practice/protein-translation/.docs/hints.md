# Hints

## General

- Translation proceeds sequentially by dividing an RNA strand into triplets (codons) of 3 nucleotides each.
- Each codon maps to an amino acid or a `STOP` signal.
- If a `STOP` codon is encountered, translation stops immediately and all subsequent nucleotides are ignored.

## Debugging: Handling Incomplete Strands

- A common pitfall occurs when slicing or scanning the strand into 3-character segments.
- If a regular expression or loop strictly expects 3 characters (for example, scanning exclusively with `.{3}`), any trailing fragment of 1 or 2 nucleotides at the end of the strand will be silently omitted from the stream instead of being processed.
- Consider the diagnostic input:
  ```json
  {"strand": "AUGU"}
  ```
  Here, `AUG` represents Methionine, but the sequence terminates with an incomplete codon `U`.
- If incomplete codons are silently ignored, the function might mistakenly succeed and return `["Methionine"]`. However, the exercise specification requires incomplete sequences to fail with `"Invalid codon"`.
- Ensure your chunking logic accounts for remainder segments (such as scanning with `.{1,3}`) so that trailing partial codons reach the translation table and trigger the invalid codon error if they are not 3 nucleotides long or not recognised.
