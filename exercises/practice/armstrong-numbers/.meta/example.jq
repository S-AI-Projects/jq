# Integer exponentiation (num^power) via iterative multiplication.
# Invariant: num^0 == 1 for all base digits; iterative reduction preserves exact integer values without float inaccuracies.
def ipow(num; power):
  reduce range(power) as $_ (1; . * num)
;

def armstrong_sum:
  ((log10 | floor) + 1) as $wid
  | reduce range($wid) as $i ([0, .];
      . as [$sum, $num]
      | [ $sum + ipow($num % 10; $wid)
        , ($num / 10 | floor)
      ]
    )
  | first
;

.number | armstrong_sum == .
