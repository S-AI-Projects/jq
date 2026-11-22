# R07-T027 guidance

The maintained reference in `exercises/practice/leap/.meta/example.jq` uses the jq alternative operator `//` together with variable binding:

```jq
(.year // 0) as $year
| $year % 4 == 0 and $year % 100 != 0 or $year % 400 == 0
```

In jq, `//` replaces both `null` and `false` when they appear on the left. This is why `null // 0` and `false // 0` both produce `0`. The exercise is an object input containing a `year` field, so `(.year // 0)` safely gives a missing or false field a fallback of `0`. It does not treat `false` as a zero value in the same way as `false // 0` may appear to: `//` is a fallback, while the modulus expression receives `0` and returns `false` for the leap calculation.

Small stand-alone examples:

```sh
jq -n '{"year": null} | (.year // 0)'       # 0
jq -n '{"year": false} | (.year // 0)'      # 0
jq -n '{"year": 1996} | ((.year // 0) as $year | $year % 4 == 0 and $year % 100 != 0 or $year % 400 == 0)' # true
```

Pitfall: applying `.year` directly to a non-object scalar such as `false` or `null` can be an indexing error. Keep this exercise's input as an object: `{"year":1996}`. A missing field returns `null` and `// 0` safely turns it into the fallback, but a direct `.year` expression on `false` is not the same as indexing an object field.

## Maintained files

- Learner stub: `exercises/practice/leap/leap.jq`
- Maintained reference: `exercises/practice/leap/.meta/example.jq`
- Bats suite: `exercises/practice/leap/test-leap.bats`
- Metadata: `exercises/practice/leap/.meta/config.json`
- Enabled test metadata: `exercises/practice/leap/.meta/tests.toml`

The `.meta/tests.toml` and `.meta/example.jq` files are maintained source artifacts. `work/R07-T027/evidence.json` is generated evidence for this task, not an exercise source file.

## Runner behavior

The checker reads `files.solution`, `files.test`, and `files.example` from the config rather than searching filenames. It verifies parent traversal and file existence, copies the complete leap exercise including dotfiles into a temporary directory, copies the example into the temporary learner solution path, and runs:

```sh
bin/validate_one_exercise exercises/practice/leap
```

The working tree is not modified. Run:

```sh
python3 work/R07-T027/check.py
```

The check exits non-zero for a failed child, a missing or zero test plan, a test-count mismatch, a micro-example mismatch, or invalid metadata that is accepted.
