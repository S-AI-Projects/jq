# Exercise Invariant:
# When transposing lines of varying lengths, shorter input lines create `null` entries.
# - Trailing nulls (where no subsequent lines had characters) must be trimmed off
#   so transposed lines do not have trailing whitespace.
# - Internal nulls (where earlier lines were shorter than subsequent lines) must be
#   padded with space characters (ASCII 32) to maintain horizontal alignment.

32 as $SPACE_CODEPOINT |

# Right-trim trailing null entries from a codepoint array
def rtrim_nulls:
    until(length == 0 or .[-1] != null; .[:-1]);

# Convert transposed row of codepoints/nulls into a string:
# 1. Strip trailing nulls (no trailing padding)
# 2. Convert internal nulls to space codepoints (ASCII 32)
# 3. Implode codepoints into string
def row_to_string:
    rtrim_nulls
    | map(. // $SPACE_CODEPOINT)
    | implode;

.lines
| map(explode)
| transpose
| map(row_to_string)
