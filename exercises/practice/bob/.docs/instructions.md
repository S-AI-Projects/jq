# Instructions

Your task is to determine what Bob will reply to someone when they say something to him or ask him a question.

Bob only ever answers one of five things:

- **"Sure."**
  This is his response if you ask him a question, such as "How are you?"
  The convention used for questions is that it ends with a question mark.
- **"Whoa, chill out!"**
  This is his answer if you YELL AT HIM.
  The convention used for yelling is ALL CAPITAL LETTERS.
- **"Calm down, I know what I'm doing!"**
  This is what he says if you yell a question at him.
- **"Fine. Be that way!"**
  This is how he responds to silence.
  The convention used for silence is nothing, or various combinations of whitespace characters.
- **"Whatever."**
  This is what he answers to anything else.

## Test maintenance

The generated Bats cases come from the Bob `canonical-data.json` in
Exercism's problem-specifications repository. `.meta/tests.toml` maps canonical
UUIDs to the exercise's selected cases: `8a2e771d-d6f1-4e3f-b6c6-b41495556e37`
is **asking a question**, `a5193c61-4a92-4f68-93e2-f554eb385ec6` is
**forceful question**, and `e162fead-606f-437a-a166-d051915cea8e` is
**stating something**.

From the jq repository root, regenerate `test-bob.bats` with
`bin/test-generator --no-pull bob` when the local problem-specifications cache
is available. `--no-pull` keeps the command from updating that cache. The
generator reads `.meta/tests.toml` and `.meta/template.j2`; it writes the
selected cases to `test-bob.bats`. The TOML file is configlet-generated
metadata, and the Bats file is generated. The template and these instructions
are maintained by hand, as are `.meta/config.json`, `.meta/example.jq`, and
`bob.jq`. The generator's only intentionally variable output is its
`# generated on ...` line; the check compares all remaining content without
normalization. The CI workflow validates exercise tests; it does not
regenerate them. The scheduled configlet workflow sets `sync_tests: false`, so
it does not refresh this exercise's TOML metadata either.
