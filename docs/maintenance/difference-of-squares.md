# Difference of Squares Complexity & Maintenance Guide

## Overview

The `difference-of-squares` exercise computes the difference between the square of the sum and the sum of the squares of the first $N$ natural numbers.

## Reference Complexity Analysis

The reference solution in `.meta/example.jq` implements the direct iteration approach:
- `seq`: constructs an array `[range(1; . + 1)]` containing $N$ integers.
- `squareOfSum`: generates array of size $N$, performs $N-1$ additions via `add`, and $1$ multiplication via `square`. Total arithmetic ops: $N$.
- `sumOfSquares`: generates array of size $N$, performs $N$ multiplications via `map(square)`, and $N-1$ additions via `add`. Total arithmetic ops: $2N - 1$.
- `difference`: computes `squareOfSum - sumOfSquares`, performing both branches plus $1$ subtraction. Total arithmetic ops: $N + (2N - 1) + 1 = 3N$.

### Comparison Across Benchmark Input Sizes

| Input Size ($N$) | Case Description | Array Allocations | Executed Operations ($3N$) | Expected Result | Complexity Class |
|------------------|------------------|-------------------|----------------------------|-----------------|------------------|
| $N = 1$ | `difference of squares 1` | 3 arrays of size 1 | 3 operations | `0` | $O(N)$ linear |
| $N = 5$ | `difference of squares 5` | 3 arrays of size 5 | 15 operations | `170` | $O(N)$ linear |
| $N = 100$ | `difference of squares 100` | 3 arrays of size 100 | 300 operations | `25164150` | $O(N)$ linear |

### Asymptotic Scaling vs Closed-Form

- **Reference Solution**: $O(N)$ time and $O(N)$ auxiliary heap memory due to materializing intermediate integer arrays in jq.
- **Closed-Form Alternative**: Using Gauss's formula $\sum_{i=1}^N i = \frac{N(N+1)}{2}$ and the square pyramidal formula $\sum_{i=1}^N i^2 = \frac{N(N+1)(2N+1)}{6}$ would achieve $O(1)$ constant time and $O(1)$ constant space with 0 array allocations.

## Verification

To run the complexity verification check:
```bash
python3 work/R07-T045/check.py
```
Or run the track validator:
```bash
bin/validate_one_exercise exercises/practice/difference-of-squares
```
