# R07-T028 validation notes

The exercise metadata is in `exercises/practice/proverb/.meta/config.json`. Every entry in its `files` object is a path relative to the exercise directory. `bin/validate_one_exercise` changes into that directory before reading the metadata. The checker parses every category (including `editor` or `invalidator` when present), rejects absolute paths and parent traversal, resolves symlinks, and requires every declared file to exist within the exercise.

- The learner stub is `exercises/practice/proverb/proverb.jq` (`files.solution[0]`). It remains unsolved.
- The maintained reference is `exercises/practice/proverb/.meta/example.jq` (`files.example[0]`).
- The Bats suite is `exercises/practice/proverb/test-proverb.bats` (`files.test[0]`).
- The declared test-helper (`invalidator`) files are `exercises/practice/proverb/bats-extra.bash` and `exercises/practice/proverb/bats-jq.bash`. They are copied by the validator so Bats can load its assertion helpers.

The validator locates `exercises/practice/proverb/test-proverb.bats` and `exercises/practice/proverb/.meta/example.jq` by resolving their `files.test[0]` and `files.example[0]` entries after changing into `exercises/practice/proverb`. It copies the reference to the configured solution filename in its own temporary directory, copies the tests and helper files there, and runs Bats. The checker first copies the complete exercise, including dotfiles, to a temporary tree, substitutes the reference for the stub only in that copy, and invokes `bin/validate_one_exercise exercises/practice/proverb` from that tree. It never changes the working tree's stub.

The learner starter is `exercises/practice/proverb/proverb.jq`; the maintained reference is `exercises/practice/proverb/.meta/example.jq`. `.meta/tests.toml` contains configlet-managed case metadata, while `test-proverb.bats` is the generated executable test suite used by the validator. `.meta/template.j2` is the generation template, not a test input read by `bin/validate_one_exercise`. The checker does not regenerate or modify any of these files.

`work/R07-T028/evidence.json` is generated check output containing metadata fixture inputs, expected and actual results, test counts, and tool versions. The checker also forces a zero-execution Bats run in a temporary copy and confirms that the run is rejected. All temporary validation copies are discarded after each run.

Run the checks with:

```sh
python3 work/R07-T028/check.py
```
