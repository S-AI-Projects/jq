# Complexity & Invariants for assert:
# - assert(.span >= 0): O(1) comparison on numeric span.
# - assert(.span <= (.digits | length)): O(N) string length scan (codepoints) + O(1) comparison.
# - assert(.digits | test("^\\d*$")): O(N) linear regex match over string of length N.
# Total assert cost is O(N) time and O(1) auxiliary memory, verifying precondition invariants strictly once before sliding window evaluation.
def assert(cond; msg):
  if cond then . else (msg | halt_error) end
;

def product:
  reduce .[] as $n (1; . * $n)
;

  assert(.span >= 0;                  "span must not be negative")
| assert(.span <= (.digits | length); "span must not exceed string length")
| assert(.digits | test("^\\d*$");    "digits input must only contain digits")

| .span as $span
| (.digits / "" | map(tonumber)) as $digits
| [
    range(($digits | length) - $span + 1)
    | $digits[.:. + $span]
    | product
  ]
| max
