# R07-T024 reference readability check

The reference implementation previously called its color-to-number lookup `$colors`. That name could be mistaken for the ordered list returned by the `colors` operation. Renaming it to `$color_codes` makes its role explicit at both lookup sites; the mapping, dispatch, outputs, ordering, and error behavior are unchanged.

The checker obtains the pre-change reference from the merge base with `origin/main`, reads every enabled input and expected output from the configured Bats file, and runs each input through both reference versions in temporary copies. It also copies the complete exercise (including dotfiles), substitutes the maintained reference only in that copy, and runs:

```sh
bin/validate_one_exercise exercises/practice/resistor-color
```

The checker validates child status, TAP test counts, skips, assertions, before/after output equality, and that learner solution files remain unchanged. `work/R07-T024/evidence.json` records the inputs, expected and actual outputs, tool versions, and validator results.
