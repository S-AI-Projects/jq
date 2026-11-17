# Alternative constant-space trial-division approach for nth-prime (R07-T016)
def is_prime:
  . as $c
  | if $c < 2 then false
    elif $c == 2 then true
    elif $c % 2 == 0 then false
    else
      [3, ($c | sqrt | floor)] as [$d, $limit]
      | def check_div($div):
          if $div > $limit then true
          elif $c % $div == 0 then false
          else check_div($div + 2)
          end;
      check_div(3)
    end;

if $n == 0 then "there is no zeroth prime" | halt_error
elif $n == 1 then 2
else
  # State: [primes_found_count, current_candidate]
  [1, 1]
  | until(.[0] == $n;
      .[1] += 2
      | if (.[1] | is_prime) then [.[0] + 1, .[1]] else . end
    )
  | .[1]
end
