# Approach B: Modular Single-Verse Constructor with Reducer
def num_word:
    ["no", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten"][.];

def capitalize_word:
    (.[0:1] | ascii_upcase) + .[1:];

def bottle_phrase($capitalize):
    (num_word | if $capitalize then capitalize_word else . end)
    + " green bottle"
    + (if . == 1 then "" else "s" end);

def make_verse:
    . as $n |
    [
        "\($n | bottle_phrase(true)) hanging on the wall,",
        "\($n | bottle_phrase(true)) hanging on the wall,",
        "And if one green bottle should accidentally fall,",
        "There'll be \($n - 1 | bottle_phrase(false)) hanging on the wall."
    ];

[ range(.startBottles; .startBottles - .takeDown; -1) | make_verse ]
| if length == 0 then []
  else reduce .[1:][] as $v (.[0]; . + [""] + $v)
  end
