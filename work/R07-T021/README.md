# R07-T021 square-root case review

## Metadata review

The six canonical test entries are all included: `include` is omitted for each UUID, and the test generator treats an omitted value as `true`. There are **6 included and 0 excluded** entries before and after this review. No `include` value or generated test has been changed.

The generator defines `reimplemented` cases as exclusions too, but this file has no `reimplements` fields. Thus none of the six cases is replaced or excluded through that mechanism.

## Selected UUID rationales

- `9b748478-7b0a-490c-b87a-609dacf631fd` — **root of 1**, input `radicand: 1`, expected `1`. `init_b` computes the starting power-of-four scale (`pow(4; floor(log(1)/log(4)))`, which is `1`). In `find_root`, `1 >= 0 + 1`; the candidate is accepted, the remaining number becomes zero, and the returned root is `1`.
- `7d3aa9ba-9ac6-4e93-a18b-2e8b477139bb` — **root of 4**, input `radicand: 4`, expected `2`. `init_b` starts at `4`. `find_root` accepts that scale (`4 >= 0 + 4`), then tests the next scale `1`; it rejects `0 >= 4 + 1` and halves the candidate with `intdiv`, yielding `2`.
- `6624aabf-3659-4ae0-a1c8-25ae7f33c6ef` — **root of 25**, input `radicand: 25`, expected `5`. `init_b` starts at `16`. `find_root` accepts 16 (remainder 9), rejects the next candidate threshold 20, and then accepts the candidate step at scale 1 because `9 >= 8 + 1`. The remaining value reaches zero and the returned root is `5`.

These are supported, included perfect-square inputs. The instructions promise positive whole-number radicands whose roots are positive whole numbers; behavior for zero, negative, fractional, or non-square inputs is not part of this test contract. No unsupported behavior is inferred as a reason to exclude a case.

## Validation

Run `python3 work/R07-T021/check.py`. It resolves files from `.meta/config.json`, parses `.meta/tests.toml` with Python's `tomllib` (or pip's vendored `tomli` on Python 3.9), copies the full exercise (including dotfiles) to temporary trees, substitutes the reference only for the learner solution in the successful reference run, and runs `bin/validate_one_exercise exercises/practice/square-root`. It also forces an all-skipped run and a deliberately failing reference to verify zero-test and assertion-failure detection. It verifies TAP plan/result counts, that no tests were skipped or failed in the real run, the selected outputs, and unchanged learner-file hashes. It saves results and tool versions in `evidence.json`.
