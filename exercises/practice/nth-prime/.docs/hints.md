# Hints

## Approach Selection

When determining the $n$-th prime number in jq, two main algorithmic approaches can be used:

### 1. Dynamic Prime Accumulation (Memoized Sieve / Primes List)
- **Data Representation**: Maintain an array of all previously discovered primes: `[2, 3, 5, ...]`.
- **Primality Test**: To test if candidate $c$ is prime, check if $c$ is divisible only by known primes $p \le \sqrt{c}$.
- **Trade-offs**:
  - *Work*: Optimal number of divisibility checks since candidates are never tested against composite divisors.
  - *Memory*: Requires $O(n)$ auxiliary array space to store all primes found so far.
  - *jq Nuance*: Passing arrays through recursion can incur copy overhead; using inner function closures avoids passing large arrays through the main pipeline.

### 2. Constant-Space Direct Trial Division
- **Data Representation**: Track only `[primes_found_count, current_candidate]`. No list of primes is stored.
- **Primality Test**: For each odd candidate $c$, test odd divisors $d = 3, 5, 7, \dots \le \sqrt{c}$.
- **Trade-offs**:
  - *Work*: Evaluates more division operations because composite divisors are tested (e.g., $9, 15, 21$).
  - *Memory*: $O(1)$ constant auxiliary memory.
  - *jq Nuance*: Simple state iteration using `until` or tail-recursive helper without array allocations.

### Worked Example: Sixth Prime ($n = 6$)
The first five primes are $2, 3, 5, 7, 11$. When testing candidate $c = 13$:
- The limit is $\lfloor\sqrt{13}\rfloor = 3$.
- **Accumulation approach**: Checks $13 \pmod 2 \ne 0$ and $13 \pmod 3 \ne 0$. The prime list has length 5, so 13 becomes the 6th prime.
- **Direct trial division**: Steps divisor $d$ from 3 up to 3: $13 \pmod 3 \ne 0$. Increment count from 5 to 6 $\implies$ result is 13.
Both approaches strictly return:
- 1st prime: `2`
- 2nd prime: `3`
- 6th prime: `13`
