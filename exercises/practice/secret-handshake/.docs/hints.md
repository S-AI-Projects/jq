# Hints

## Contract & Bitwise Representation Walkthrough

In `secret-handshake`, the input JSON object contains an integer `{"number": n}`. The operations are determined by the binary representation of `number`, where each bit position corresponds to an action. Note that test names such as "double blink for 10" and "close your eyes for 100" use binary representations in their titles (binary `10` is decimal `2`, and binary `100` is decimal `4`).

### Walkthrough of Selected Cases

1. **`wink for 1`**
   - **Input**: `{"number": 1}`
   - **Binary**: `00001` (bit 0 is set: $2^0 = 1$)
   - **Evaluation**: Bit 0 corresponds to `"wink"`. Bit 4 (reverse) is not set.
   - **Result**: `["wink"]`

2. **`double blink for 10`**
   - **Input**: `{"number": 2}`
   - **Binary**: `00010` (bit 1 is set: $2^1 = 2$)
   - **Evaluation**: Bit 1 corresponds to `"double blink"`. Bit 4 is not set.
   - **Result**: `["double blink"]`

3. **`close your eyes for 100`**
   - **Input**: `{"number": 4}`
   - **Binary**: `00100` (bit 2 is set: $2^2 = 4$)
   - **Evaluation**: Bit 2 corresponds to `"close your eyes"`. Bit 4 is not set.
   - **Result**: `["close your eyes"]`

### Decision Table

| Binary Pattern | Decimal Input (`number`) | Active Bit Position | Associated Action | Output Array |
| :--- | :--- | :--- | :--- | :--- |
| `00001` | `1` | Bit 0 ($2^0$) | Wink | `["wink"]` |
| `00010` | `2` | Bit 1 ($2^1$) | Double blink | `["double blink"]` |
| `00100` | `4` | Bit 2 ($2^2$) | Close your eyes | `["close your eyes"]` |
| `01000` | `8` | Bit 3 ($2^3$) | Jump | `["jump"]` |
| `10000` | `16` | Bit 4 ($2^4$) | Reverse list | Reverses sequence |

### Scope & Unspecified Behavior
- **Action Order**: Actions are collected from lowest to highest bit position (bits 0 through 3). If bit 4 ($16$) is set, the collected list is reversed.
- **Unspecified Inputs**: Inputs outside the canonical integer range (such as negative numbers, floating-point numbers, or string inputs) are outside the exercise contract. No custom exception handling, type coercion, or alternate ordering is imposed beyond the bits specified.
