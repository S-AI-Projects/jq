# Hints

## General

- An Earth year comprises exactly `31,557,600` seconds (365.25 Earth days of 86,400 seconds).
- The orbital period of each planet is defined as a multiplier of an Earth solar year:
  - Mercury: `0.2408467`
  - Venus: `0.61519726`
  - Earth: `1.0`
  - Mars: `1.8808158`
  - Jupiter: `11.862615`
  - Saturn: `29.447498`
  - Uranus: `84.016846`
  - Neptune: `164.79132`

## Rounding to Two Decimal Places in jq

In `jq`, the standard mathematical function [`round`](https://jqlang.github.io/jq/manual/#math) rounds any numeric input to the nearest integer.

To round a floating-point value to exactly two decimal places, multiply by `100`, round to the nearest whole integer, and then divide by `100`:

```jq
def two_decimal: ((. * 100) | round) / 100;
```

### Executable Micro-Example

You can run this filter directly in your terminal using `jq`:

```bash
jq -n '31.687537 | ((. * 100) | round) / 100'
```

**Expected output:**
```json
31.69
```

Similarly, for Mercury:
```bash
jq -n '(2134835688 / 31557600 / 0.2408467) | ((. * 100) | round) / 100'
```

**Expected output:**
```json
280.88
```

## Error Handling for Invalid Planets

- Test cases pass input objects with `.planet` and `.seconds`.
- Check whether the requested planet exists in your lookup table (for example, using `has($planet)`).
- If the planet is not supported, raise an error with:
  ```jq
  "not a planet" | halt_error
  ```

For additional built-in mathematical operators and filters, consult the official [jq Manual (Math)](https://jqlang.github.io/jq/manual/#math).
