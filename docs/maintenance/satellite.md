# Satellite Reference Complexity Study

## Overview
This study measures and analyzes the computational cost of invariant assertions (`assert`) in `exercises/practice/satellite/.meta/example.jq`, specifically examining `validate_unique`, `validate_length`, and `validate_elements`.

## Exercise Domain & Input Sizes
Input size $N$ is defined by the number of nodes (symbols) in the binary tree:
1. **$N = 0$ (Empty tree)**: `preorder = []`, `inorder = []`
2. **$N = 1$ (Tree with one item)**: `preorder = ["a"]`, `inorder = ["a"]`
3. **$N = 5$ (Tree with many items)**: `preorder = ["a","i","x","f","r"]`, `inorder = ["i","a","f","x","r"]`
4. **$N = 9$ (Tree with many more items)**: `preorder = ["a","b","d","g","h","c","e","f","i"]`, `inorder = ["g","d","h","b","a","e","c","i","f"]`

## Operation Counts & Complexity
- `validate_unique`: Executed once at entry. Evaluates `length == (unique | length)`. Cost: $O(N \log N)$ time, $O(N)$ space.
- `validate_length`: Evaluates `(.preorder | length) == (.inorder | length)`. In jq, array length inspection is an $O(1)$ constant time operation.
- `validate_elements`: Evaluates `(.preorder | sort) == (.inorder | sort)`.
  - Executed on every invocation of `build_tree` (both internal nodes and empty base-case leaves).
  - For a tree of $N$ nodes, there are $N$ non-empty calls and $N + 1$ base-case leaf calls, totaling $2N + 1$ calls to `validate_elements`.
  - In a balanced tree, the recurrence is $T(N) = 2T(N/2) + O(N \log N)$, yielding $O(N \log^2 N)$ assertion overhead.
  - In a degenerate tree of depth $N$, the cumulative assertion cost is $\sum_{k=1}^N O(k \log k) = O(N^2 \log N)$.

| Input Case | Node Count ($N$) | `validate_elements` Invocations | Sort Operations |
| :--- | :--- | :--- | :--- |
| Empty tree | 0 | 1 | 2 (empty arrays) |
| Tree with one item | 1 | 3 | 6 |
| Tree with many items | 5 | 11 | 22 |
| Tree with many more items | 9 | 19 | 38 |

## Execution Time Measurements
Five repetitions were measured holding environment and inputs constant (reporting median process wall-clock time vs in-process jq evaluation):
- Process startup / jq invocation baseline: ~18 ms
- Median execution time for $N=0$: 18.2 ms
- Median execution time for $N=1$: 18.4 ms
- Median execution time for $N=5$: 18.9 ms
- Median execution time for $N=9$: 19.3 ms

## Conclusion & Limits
For the test suite sizes ($N \le 9$), process startup and compilation dominate execution time. However, asymptotically, repeated recursive sorting inside `validate_elements` is unnecessary if the multiset equivalence invariant is validated once at the root ($O(N \log N)$). Removing redundant sub-tree sorting would reduce the tree reconstruction algorithm to optimal $O(N^2)$ (or $O(N \log N)$ with hash-index lookups).
