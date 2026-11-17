# Prime Factors Maintenance

## Canonical Cases Overview

The `prime-factors` exercise canonical test suite comprises 12 test cases defined in canonical problem specifications.
All 12 cases are supported and enabled (12 included, 0 excluded).

## Canonical Case Mapping Table

| UUID | Test Name / Description | Status | Reference Behavior & jq Operation Rationale |
| --- | --- | --- | --- |
| `924fc966-a8f5-4288-82f2-6b9224819ccd` | no factors | Included | Input `1` has no prime factors. In `example.jq`, the loop condition `until(.factor * .factor > .number; ...)` terminates immediately (`2 * 2 > 1` is true) without trial division; the conditional `[if .number > 1 then .number else empty end]` evaluates the `empty` generator, returning `[]`. |
| `17e30670-b105-4305-af53-ddde182cb6ad` | prime number | Included | Smallest prime `2`. In `example.jq`, `until(.factor * .factor > .number; ...)` terminates immediately (`2 * 2 > 2` is true); the trailing conditional `if .number > 1 then .number else empty end` evaluates `.number` (`2`), appending `[2]` via array concatenation `+`. |
| `238d57c8-4c12-42ef-af34-ae4929f94789` | another prime number | Included | Smallest odd prime `3`. In `example.jq`, `until(.factor * .factor > .number; ...)` terminates immediately (`2 * 2 > 3` is true); the trailing conditional `if .number > 1 then .number else empty end` evaluates `.number` (`3`), appending `[3]` via array concatenation `+`. |
| `f59b8350-a180-495a-8fb1-1712fbee1158` | square of a prime | Included | Input `9`. Tested via trial division: factor 2 skipped (`9 % 2 != 0`), factor 3 divides `9` twice yielding `[3, 3]`. |
| `756949d3-3158-4e3d-91f2-c4f9f043ee70` | product of first prime | Included | Input `4`. Inner `until` loop divides by 2 repeatedly yielding `[2, 2]`. |
| `bc8c113f-9580-4516-8669-c5fc29512ceb` | cube of a prime | Included | Input `8`. Repeated division by 2 yields `[2, 2, 2]`. |
| `7d6a3300-a4cb-4065-bd33-0ced1de6cb44` | product of second prime | Included | Input `27`. Repeated division by 3 yields `[3, 3, 3]`. |
| `073ac0b2-c915-4362-929d-fc45f7b9a9e4` | product of third prime | Included | Input `625`. Repeated division by 5 yields `[5, 5, 5, 5]`. |
| `6e0e4912-7fb6-47f3-a9ad-dbcd79340c75` | product of first and second prime | Included | Input `6`. Factor 2 divides leaving 3, factor 3 divides leaving 1, returning `[2, 3]`. |
| `00485cd3-a3fe-4fbe-a64a-a4308fc1f870` | product of primes and non-primes | Included | Input `12`. Factor 2 divides twice leaving 3, returning `[2, 2, 3]`. |
| `02251d54-3ca1-4a9b-85e1-b38f4b0ccb91` | product of primes | Included | Input `901255`. Trial division finds factors `[5, 17, 23, 461]`. |
| `070cf8dc-e202-4285-aa37-8d775c9cd473` | factors include a large prime | Included | Input `93819012551`. Factors `11` and `9539` are factored out, leaving large prime `894119` captured by `.number > 1`. |

## Reference Implementation Mechanics

The reference implementation in `.meta/example.jq`:
```jq
{ number: .value, factor: 2, primes: [] }
| until(
    .factor * .factor > .number;
    until(
      .number % .factor != 0;
      .number /= .factor | .primes += [.factor]
    )
    | .factor += 1
  )
| .primes + [if .number > 1 then .number else empty end]
```

Key jq language operations utilized:
- `until(cond; next)`: iteratively executes `next` until `cond` holds.
- `%=`, `/=`, `+=`: arithmetic and array assignment operations.
- `empty`: returns 0 outputs, allowing `[if .number > 1 then .number else empty end]` to produce `[]` when `.number <= 1` and `[.number]` when `.number > 1`.
- `+`: concatenates accumulated prime factors with any remaining cofactor.
