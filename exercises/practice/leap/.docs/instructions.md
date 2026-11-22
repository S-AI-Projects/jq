# Instructions

Your task is to determine whether a given year is a leap year.

## A jq detail in the reference

The reference starts with `.year // 0`. In jq, `//` is the alternative
operator: it uses the right-hand value when the left side produces `null` or
`false`. This is broader than “use the default only if the field is missing.”
The exercise contract supplies an integer year, so the fallback is not a
substitute for validating arbitrary input.

For example, compare an explicitly null year with a false value:

```jq
[({year: null} | (.year // 2024)), ({year: false} | (.year // 2024))]
```

This outputs `[2024, 2024]`: `//` chooses the fallback in both cases. The
contrast makes the pitfall visible:

```jq
[({year: false} | (.year == null)), ({year: false} | (.year // 0))]
```

This outputs `[false, 0]`. The value `false` is not equal to `null`, but the
alternative operator still treats it as a reason to use the fallback. In this
exercise the input is a year number, not a boolean; this example explains jq's
operator behavior rather than adding boolean inputs to the leap-year contract.
