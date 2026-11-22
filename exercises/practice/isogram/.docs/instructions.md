# Instructions

Determine if a word or phrase is an isogram.

An isogram (also known as a "non-pattern word") is a word or phrase without a repeating letter, however spaces and hyphens are allowed to appear multiple times.

Examples of isograms:

- lumberjacks
- background
- downstream
- six-year-old

The word _isograms_, however, is not an isogram, because the s repeats.

## Reference implementation cost

Let `n` be the number of characters in the input phrase and `m` the number of
ASCII letters left after filtering (`m <= n`). The reference first uppercases
and splits the phrase, then scans the characters to retain `A` through `Z`.
Those passes take linear work. `group_by(.)` sorts the retained letters before
forming groups, so the dominant work is typically `O(m log m)` comparisons;
checking group lengths and applying `all` takes `O(m)` work. The pipeline
materializes character/group arrays, using `O(n + m)` auxiliary space. The
final `all` can stop at a false value, but only after the preceding `map` has
checked every group.

The exercise accepts variable-length words and phrases, so these checks use
three valid lowercase-letter strings of different lengths. Correctness was
checked against the reference before taking five timing samples per input:

| Input characters | Expected / actual | Median subprocess wall time |
| ---: | --- | ---: |
| 16 | `true` / `true` | 2.524 ms |
| 256 | `false` / `false` | 2.715 ms |
| 4096 | `false` / `false` | 7.635 ms |

Each longer input cycles through the lowercase alphabet; repeated letters
therefore make the 256- and 4096-character inputs non-isograms. These are
illustrative measurements, not a speedup claim. The timed interval includes
starting a new `jq` process and parsing its filter on every repetition, so it
does not isolate algorithm execution time. No separate compilation step is
measured. To reproduce the reference tests and measurements from the
repository root, run `python3 work/R07-T025/check.py`; the detailed inputs,
outputs, individual samples, and tool versions are recorded in
`work/R07-T025/evidence.json`.
