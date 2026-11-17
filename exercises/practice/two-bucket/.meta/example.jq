# Validate the input to check if the goal can be attained
def validate:
  # local helper function
  def gcd:
    if .[1] == 0
      then .[0]
      else [.[1], .[0] % .[1]] | gcd
    end;

  ([.bucketOne, .bucketTwo] | max) as $max |
  ([.bucketOne, .bucketTwo] | gcd) as $gcd |
  if (.goal > $max) or ($gcd != 1 and .goal % $gcd != 0)
    then ("impossible" | halt_error)
    else .
  end;


# Find the solution to the two bucket problem
#
# input:    2-element array: [firstBucket, secondBucket]
# argument: goal
# output:   result object {moves, goalBucket, otherBucket}
#
# Invariant:
# State is tracked as [bucket1, bucket2, moveCount].
# At each step, actions follow a deterministic priority rule:
# 1. Terminate when either bucket contains the goal amount.
# 2. Fill the first bucket if it is empty.
# 3. Fill the second bucket if its capacity exactly equals the goal.
# 4. Empty the second bucket if it is completely full.
# 5. Otherwise, pour from the first bucket into the second until full or empty.
def solve($goal):

  # tail-call optimization only applies for 0-arity functions.
  # https://github.com/jqlang/jq/wiki/Advanced-Topics#recursion-and-tail-recursion-optimization
  # input to inner function is: [firstBucket, secondBucket, currentMove]
  def _solve:
    .[0] as $b1 | .[1] as $b2 | .[2] as $moves |
    if $b1.amount == $goal
      then {moves: $moves, goalBucket: $b1.name, otherBucket: $b2.amount}
    elif $b2.amount == $goal
      then {moves: $moves, goalBucket: $b2.name, otherBucket: $b1.amount}
    else
      # Rule 1: if first bucket is empty, fill it to capacity
      if .[0].amount == 0 then .[0].amount = .[0].size

      # Rule 2: if second bucket capacity matches the goal, fill it
      elif .[1].size == $goal then .[1].amount = .[1].size

      # Rule 3: if second bucket is full, empty it
      elif .[1].amount == .[1].size then .[1].amount = 0

      # Rule 4: transfer water from first bucket into second bucket
      else
        ([.[0].amount, .[1].size - .[1].amount] | min) as $transferQty |
        .[0].amount -= $transferQty |
        .[1].amount += $transferQty
      end
      # increment move counter and continue tail-recursive search
      | .[2] += 1 | _solve
    end;

  # initialize move counter to 0 on the state tuple
  . + [0] | _solve;


# "main"
#
validate |
.goal as $goal |
{ name: "one", amount: 0, size: .bucketOne } as $one |
{ name: "two", amount: 0, size: .bucketTwo } as $two |
if .startBucket == "one"
  then [$one, $two]
  else [$two, $one]
end |
solve($goal)
