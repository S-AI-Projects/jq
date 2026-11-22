# R07-T028 validation notes

The exercise metadata is in `exercises/practice/proverb/.meta/config.json`. Its `files` entries are paths relative to the exercise directory: `bin/validate_one_exercise` changes into that directory before reading the metadata.

- The learner stub is `exercises/practice/proverb/proverb.jq` (`files.solution[0]`). It remains unsolved.
- The maintained reference is `exercises/practice/proverb/.meta/example.jq` (`files.example[0]`).
- The Bats suite is `exercises/practice/proverb/test-proverb.bats` (`files.test[0]`).
- The declared invalidator files are `exercises/practice/proverb/bats-extra.bash` and `exercises/practice/proverb/bats-jq.bash`.

The validator locates `test-proverb.bats` and `.meta/example.jq` by resolving those metadata paths after changing into `exercises/practice/proverb`. It copies the reference to the configured solution filename in its own temporary directory, copies the tests and helper files there, and runs Bats. The checker first copies the complete exercise, including dotfiles, to a temporary tree, substitutes the reference for the stub only in that copy, and invokes `bin/validate_one_exercise exercises/practice/proverb` from that tree. It never changes the working tree's stub.

`work/R07-T028/evidence.json` is generated check output containing metadata fixture inputs, expected and actual results, test counts, and tool versions. The validator's temporary implementation copy is discarded after the run. `.meta/tests.toml` is configlet-generated exercise metadata; it is not changed by this task. The existing Bats suite is used as-is, including the zero-, one-, two-, three-, full-proverb, and modernized cases.

Run the checks with:

```sh
python3 work/R07-T028/check.py
```
