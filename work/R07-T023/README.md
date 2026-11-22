# R07-T023 anagram mutation check

## Mutation and result

The scratch mutant removes only the `ascii_upcase != $subj` condition from the `matches` predicate. It still compares the full sorted character encoding, so it remains sensitive to letter counts and cannot match subsets.

The enabled case **words are not anagrams of themselves** rejects this mutation: the original reference returns `[]` for subject `BANANA` and candidate `BANANA`, while the mutant returns `["BANANA"]`. The smallest input allowed by the contract that exposes the same defect is subject `"a"` with candidate `"a"`: the original returns `[]`, and the mutant returns `["a"]`.

The mutant does not turn `goGoGO` into an anagram of `go`; its complete letter multiset still differs. This is why the repeated-word test is not the selected rejecting case. The suite already has an enabled exact-self case, so no additional proposed test or Bats change was needed.

## Validation

Run `python3 work/R07-T023/check.py`. It resolves files from `.meta/config.json`, parses every Bats case's input and expected output, exercises identical inputs against the original and a mutated reference in temporary copies, and runs `bin/validate_one_exercise exercises/practice/anagram` for both copies. It checks TAP counts and failing assertions, the contract diagnostic input, and learner solution hashes. Results and tool versions are recorded in `evidence.json`.
