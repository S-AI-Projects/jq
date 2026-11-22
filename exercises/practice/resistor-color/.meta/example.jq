{
    black:   0,
    brown:   1,
    red:     2,
    orange:  3,
    yellow:  4,
    green:   5,
    blue:    6,
    violet:  7,
    grey:    8,
    white:   9
} as $color_codes |

if .property == "colorCode" then $color_codes[.input.color]
elif .property == "colors" then $color_codes | keys | sort_by($color_codes[.])
else empty
end
