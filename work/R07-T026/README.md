# R07-T026 phone-number implementation comparison

## Approaches

The maintained reference removes the six explicitly allowed formatting characters with `gsub("[() +.-]"; "")`, then validates the normalized string in sequence.

The independent scratch alternative visits the input's Unicode code points with `explode` and `reduce`. It appends each code point except ASCII space, parentheses, plus, dot, and hyphen, then runs the same length, country-code, character, and NANP checks in the same order. This changes the representation/control flow, not just variable names, while preserving validation messages and precedence.

For `223.456   7890`, the walk skips `.` and the repeated spaces and produces `2234567890`. A per-character pass is easier to explain when rules need individual treatment. It materializes a code-point array and accumulates a separate cleaned string, adding temporary space and per-character work; the reference's regex substitution is more concise and avoids that explicit array.

## Validation

Run `python3 work/R07-T026/check.py`. The checker reads the configured solution, Bats test, and reference paths from `.meta/config.json`, extracts every enabled Bats case and its expected success/error result, then runs identical inputs through both references in temporary copies. It also copies the whole exercise (including dotfiles), substitutes only the reference in each copy, and runs `bin/validate_one_exercise exercises/practice/phone-number` for each approach. Evidence and tool versions are saved to `evidence.json`.
