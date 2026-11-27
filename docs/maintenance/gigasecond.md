# Gigasecond Approach Comparison

## Overview
This document compares two valid techniques for implementing `gigasecond` in jq.

## Approach 1: Reference Implementation (Exception-Driven ISO-8601)
```jq
1000000000 as $Gigasecond
| .moment as $dt
| try ($dt + "Z" | fromdateiso8601)
  catch ($dt + "T00:00:00Z" | fromdateiso8601)
| . + $Gigasecond
| strftime("%FT%T")
```

## Approach 2: Alternative Implementation (Explicit Normalization with strptime/mktime)
```jq
1000000000 as $Gigasecond
| .moment
| (if contains("T") then . else . + "T00:00:00" end)
| strptime("%Y-%m-%dT%H:%M:%S")
| mktime + $Gigasecond
| strftime("%Y-%m-%dT%H:%M:%S")
```

## Comparison Matrix

| Criteria | Approach 1 (Reference) | Approach 2 (Alternative) |
| --- | --- | --- |
| Date-only handling | `try ... catch` exception fallback | Explicit `contains("T")` string check |
| Parser primitive | `fromdateiso8601` (C-level ISO) | `strptime` with format pattern |
| Conversion | Epoch seconds directly | Broken-down time array via `mktime` |
| Test suite results | 5/5 tests passing | 5/5 tests passing |
