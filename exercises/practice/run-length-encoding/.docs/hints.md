# Hints

## General

- Consider using jq's regular expression utilities, such as `scan`, to group consecutive repeating characters.
- Jq supports `reduce` to fold over streamed character sequences and accumulate the encoded or decoded result string.

## Debugging

- **Omitting unit counts:** The run-length encoding specification requires that single occurrences of characters are encoded *without* a count prefix. For instance, the sequence `"XYZ"` must encode directly as `"XYZ"`, not `"1X1Y1Z"`.
- If your encoder always formats each run as `<count><char>` unconditionally, test cases such as `run-length encode a string:single characters only are encoded without count` will fail. Ensure your reducer checks whether the run length is greater than `1` before prefixing the numeric count.
