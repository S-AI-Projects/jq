# Generates a substitution lookup map for both lowercase and uppercase letters.
# Invariant: Shift distance is normalized modulo 26 ($shift % 26).
# The rotated alphabet is split and re-concatenated ($lower[$s:] + $lower[:$s]),
# preserving 1-to-1 letter mapping for all shifts in range [0, 26].
def makeMap($shift):
  "abcdefghijklmnopqrstuvwxyz" as $lower
  | ($shift % 26) as $s
  | ($lower[$s:] + $lower[:$s]) as $rotated
  | reduce range(26) as $i ({};
      $lower[$i:$i+1] as $from
      | $rotated[$i:$i+1] as $to
      | . + {($from): $to, ($from | ascii_upcase): ($to | ascii_upcase)}
    )
;

def rotate:
  if .text == ""
  then .rotated
  else
    .text[0:1] as $char
    | .text |= .[1:length]
    | .rotated += (.rotation[$char] // $char)
    | rotate
  end
;

{"text": .text, "rotated": "", "rotation": makeMap(.shiftKey)} | rotate
