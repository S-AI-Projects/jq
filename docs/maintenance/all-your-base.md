# All Your Base Exercise Maintenance

## Canonical Case Decisions & Mapping

The canonical test suite for `all-your-base` defines 21 test cases in `exercises/practice/all-your-base/.meta/tests.toml`.
In the jq track, all 21 cases are currently included and supported by the reference implementation in `exercises/practice/all-your-base/.meta/example.jq`.

Below is the mapping of all 21 canonical cases with their UUIDs, descriptions, inclusion status, and jq implementation rationale.

| UUID | Description | Status | jq Implementation Rationale |
| :--- | :--- | :--- | :--- |
| `5ce422f9-7a4b-4f44-ad29-49c67cb32d2c` | single bit one to decimal | Included | Base conversion identity for a single unit bit (`[1]` from base 2 to base 10). `to_decimal(2)` executes `reduce .[] as $d (0; 2 * . + $d)` evaluating `2 * 0 + 1 = 1`, and `to_base(10)` emits `[1]`. |
| `0cc3fea8-bb79-46ac-a2ab-5a2c93051033` | binary to single decimal | Included | Multi-digit positional radix evaluation (`[1, 0, 1]` base 2 to base 10). In jq, `to_decimal(2)` evaluates `((0*2 + 1)*2 + 0)*2 + 1 = 5`, which `to_base(10)` formats into single-digit array `[5]`. |
| `f12db0f9-0d3d-42c2-b3ba-e38cb375a2b8` | single decimal to binary | Included | Radix expansion from single decimal digit `[5]` to multi-digit binary `[1, 0, 1]`. In jq, `to_decimal(10)` evaluates to `5`, and `to_base(2)` uses recursive modulo/division (`.n % base` and `(.n - $digit) / base`) to assemble `[1, 0, 1]`. |
| `2c45cf54-6da3-4748-9733-5a3c765d925b` | binary to multiple decimal | Included | Conversion of multi-digit binary `[1, 0, 1, 0, 1, 0]` to multiple decimal digits `[4, 2]`. Handled by iterative `to_decimal` and recursive decomposition in `to_base`. |
| `65ddb8b4-8899-4fcc-8618-181b2cf0002d` | decimal to binary | Included | Multi-digit decimal `[4, 2]` converted to binary `[1, 0, 1, 0, 1, 0]`. Standard positional radix transformation. |
| `8d418419-02a7-4824-8b7a-352d33c6987e` | trinary to hexadecimal | Included | Base 3 to base 16 conversion across non-decimal bases. Evaluates accumulator through intermediate integer representation. |
| `d3901c80-8190-41b9-bd86-38d988efa956` | hexadecimal to trinary | Included | Inverse of base 16 to base 3 conversion, testing positional arithmetic consistency across arbitrary base combinations. |
| `5d42f85e-21ad-41bd-b9be-a3e8e4258bbf` | 15-bit integer | Included | Stress test for larger values within standard IEEE 754 float representation in jq. |
| `d68788f7-66dd-43f8-a543-f15b6d233f83` | empty list | Included | Boundary condition: empty input array `[]` evaluates to `[0]` via `if .digits == [] then [0] else .digits end`. |
| `5e27e8da-5862-4c5f-b2a9-26c0382b6be7` | single zero | Included | Zero representation: `[0]` remains `[0]`. Handled cleanly without emitting empty arrays. |
| `2e1c2573-77e4-4b9c-8517-6c56c5bcfdf2` | multiple zeros | Included | Repeated zeros `[0, 0, 0]` evaluate to value 0 and normalize to canonical output `[0]`. |
| `3530cd9f-8d6d-43f5-bc6e-b30b1db9629b` | leading zeros | Included | Leading zeros `[0, 6, 0]` are normalized to `[4, 2]` in base 10 by arithmetic accumulation. |
| `a6b476a1-1901-4f2a-92c4-4d91917ae023` | input base is one | Included | Error handling: input base < 2 triggers `"input base must be >= 2" \| halt_error`. |
| `e21a693a-7a69-450b-b393-27415c26a016` | input base is zero | Included | Error handling: input base < 2 triggers `"input base must be >= 2" \| halt_error`. |
| `54a23be5-d99e-41cc-88e0-a650ffe5fcc2` | input base is negative | Included | Error handling: negative input base triggers `"input base must be >= 2" \| halt_error`. |
| `9eccf60c-dcc9-407b-95d8-c37b8be56bb6` | negative digit | Included | Digit validation: checks `0 <= d < inputBase`; negative digit triggers error halt. |
| `232fa4a5-e761-4939-ba0c-ed046cd0676a` | invalid positive digit | Included | Digit validation: digit >= input base triggers `"all digits must satisfy 0 <= d < input base" \| halt_error`. |
| `14238f95-45da-41dc-95ce-18f860b30ad3` | output base is one | Included | Error handling: output base < 2 triggers `"output base must be >= 2" \| halt_error`. |
| `73dac367-da5c-4a37-95fe-c87fad0a4047` | output base is zero | Included | Error handling: output base < 2 triggers `"output base must be >= 2" \| halt_error`. |
| `13f81f42-ff53-4e24-89d9-37603a48ebd9` | output base is negative | Included | Error handling: negative output base triggers `"output base must be >= 2" \| halt_error`. |
| `0e6c895d-8a5d-4868-a345-309d094cfe8d` | both bases are negative | Included | Precedence check: input base validation executes first and fails with expected input base error message. |

## Running the Automated Check
```bash
python3 work/R07-T001/check.py
```
