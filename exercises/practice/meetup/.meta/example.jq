# Get the last day of the month
#
# input: an object with {year, month} numbers
# output: day of month, as a number
def last_day:
    (
        if .month == 12
        then "\(.year+1)-01-01T12:00:00Z"
        else "\(.year)-\(.month+1)-01T12:00:00Z"
        end
        | fromdate
    ) - 86400
    | strftime("%d")
    | tonumber;


# Given the "week" input, return the day of the month where we'll start
def start_day:
    if .week == "first" then 1
    elif .week == "second" then 8
    elif .week == "third" then 15
    elif .week == "fourth" then 22
    elif .week == "teenth" then 13
    elif .week == "last" then (last_day - 6)
    else "Unknown 'week' value: \(.week)" | halt_error
    end;


# Invariant: Each week descriptor defines a fixed 7-day candidate window (e.g., 'teenth' covers days 13..19).
# Since any given weekday occurs exactly once within every 7 consecutive days, iterating at most 7 days
# (days_checked 0..6) is guaranteed to find the matching weekday.
def meetup:
    if .days_checked == 7 then
        "Error: can't get meetup day" | halt_error
    elif (.epoch | strftime("%A")) == .dayofweek then
        .epoch | strftime("%Y-%m-%d")
    else
        # Step forward 1 day (86400 seconds) within the 7-day candidate window
        .epoch += 86400 | .days_checked += 1 | meetup
    end;
        

{
    dayofweek,
    epoch: ("\( .year )-\( .month )-\( start_day )T12:00:00Z" | fromdate),
    days_checked: 0
}
| meetup

