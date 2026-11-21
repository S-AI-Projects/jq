# Hints

## General

- In Resistor Color Trio, the first two color bands denote the significant digits, while the third band denotes the power-of-ten multiplier.
- The resistance in ohms is computed as:
  $$\text{ohms} = (10 \times \text{color}_1 + \text{color}_2) \times 10^{\text{color}_3}$$
- The output format must be a JSON object with integer `value` and string `unit`:
  ```json
  {
    "value": 33,
    "unit": "ohms"
  }
  ```

## Metric Prefix Reduction

When the raw resistance value in ohms is a non-zero multiple of 1000, scale the value down by factors of 1000 and select the appropriate metric prefix:
- `< 1000 ohms`: `ohms`
- `1,000` to `999,999 ohms`: `kiloohms`
- `1,000,000` to `999,999,999 ohms`: `megaohms`
- `1,000,000,000+ ohms`: `gigaohms`

## Decision Table for Selected Cases

| Input Colors | Significant Digits | Multiplier | Raw Ohms | Metric Scaling | Expected Result |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `["orange", "orange", "black"]` | `3`, `3` $\to 33$ | $10^0 = 1$ | $33$ | Value $< 1000$; no kilo prefix | `{"value": 33, "unit": "ohms"}` |
| `["blue", "grey", "brown"]` | `6`, `8` $\to 68$ | $10^1 = 10$ | $680$ | Value $< 1000$; no kilo prefix | `{"value": 680, "unit": "ohms"}` |

## Specified vs Unspecified Contract Behavior
- **Extra Colors**: If the input array has more than 3 colors (e.g. `["green", "brown", "orange", "yellow"]`), the specification requires ignoring any color beyond the first three.
- **Unspecified Inputs**: Inputs with fewer than 3 colors, invalid color strings, or non-array inputs are outside the exercise contract. Solutions should avoid imposing custom exceptions or validations not demanded by the canonical tests.
