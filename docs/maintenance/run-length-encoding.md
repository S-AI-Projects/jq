# Run-Length Encoding Maintenance Guide

## Overview

The `run-length-encoding` exercise implements data compression and decompression using run-length encoding.
In jq, the reference solution (`.meta/example.jq`) uses `scan("(.)(\\1*)")` to extract runs and `reduce` to construct compressed strings, selectively prefixing the count when run length $> 1$.

## Deliberate Mutation & Regression Test

To verify test suite sensitivity, we constructed a deliberate semantic mutant of the encoding logic:

### Reference Implementation
```jq
def encode:
  reduce scan("(.)(\\1*)") as $s ("";
    (1 + ($s[1] | length) | tostring) as $count |
    . + if $count == "1" then "" else $count end + $s[0]
  );
```

### Deliberate Mutant
```jq
def encode:
  reduce scan("(.)(\\1*)") as $s ("";
    (1 + ($s[1] | length) | tostring) as $count |
    . + $count + $s[0]
  );
```
The mutant incorrectly assumes that all character runs should be prefixed with their occurrence count, including single characters.

### Rejecting Test Case
- **Test Name**: `run-length encode a string:single characters only are encoded without count`
- **Canonical UUID**: `52012823-b7e6-4277-893c-5b96d42f82de`
- **Input**: `{"property": "encode", "input": {"string": "XYZ"}}`
- **Expected Result**: `"XYZ"`
- **Mutant Result**: `"1X1Y1Z"`
- **Assertion**: Rejected by Bats `assert_equal "$output" "$expected"`.

### Baseline Anchor Cases
1. `run-length encode a string:empty string` (`13b916bb-49e8-466c-9dd6-0351ce890c25`) — Reference passes (`""`).
2. `run-length encode a string:single characters only are encoded without count` (`52012823-b7e6-4277-893c-5b96d42f82de`) — Reference passes; mutant fails.
3. `run-length encode a string:string with no single characters` (`b7868492-7e3a-415f-8da3-d88f51f80409`) — Both pass since all counts are $> 1$.

## Automated Verification

Run the mutation check and isolated test runner:
```bash
python3 work/R07-T043/check.py
```
This script confirms that the reference passes all 13 canonical tests, the mutant fails specifically on `run-length encode a string:single characters only are encoded without count`, and the learner stub remains unsolved.
