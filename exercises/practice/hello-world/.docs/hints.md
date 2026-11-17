# Hints

## Contract & Decision Table for "Say Hi!"

The `hello-world` exercise requires outputting the exact string `"Hello, World!"`.

### Input / Output Decision Table

| Input Condition | Specification Status | Expected Output | Rationale |
| --- | --- | --- | --- |
| Empty input / null (`null`) | Specified (Canonical) | `"Hello, World!"` | Standard canonical test case (`Say Hi!`). |
| Empty object (`{}`) | Within Contract | `"Hello, World!"` | Valid JSON payload passed by standard runners. |
| Any arbitrary JSON value | Unspecified | `"Hello, World!"` | The specification does not inspect the input; it always emits `"Hello, World!"`. |

### Key Takeaway
No input inspection, parameter validation, string coercion, or error handling is required by the contract. The program unconditionally returns `"Hello, World!"`.
