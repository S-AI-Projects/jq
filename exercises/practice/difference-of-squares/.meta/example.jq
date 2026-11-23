# Complexity and Invariant Analysis:
# - Time Complexity: O(N) linear time with respect to input N.
#   - seq generates an array of N integers via range(1; N + 1).
#   - squareOfSum executes seq (N elements), add (N - 1 additions), and square (1 multiplication).
#   - sumOfSquares executes seq (N elements), map(square) (N multiplications), and add (N - 1 additions).
#   - differenceOfSquares performs both computations and 1 subtraction, yielding exactly 3*N operations.
# - Space Complexity: O(N) auxiliary memory, allocating 3 arrays of size N in total.
# - Benchmark Operation Bounds:
#   - N = 1: 3 operations, result = 0
#   - N = 5: 15 operations, result = 170
#   - N = 100: 300 operations, result = 25164150
# Note: An algebraic closed-form formula would achieve O(1) time and space.

def seq: [range(1; . + 1)];
def square: . * .;
def squareOfSum: seq | add | square ;
def sumOfSquares: seq | map(square) | add ;

.property as $fn
| .input.number
| if   $fn == "squareOfSum" then squareOfSum
  elif $fn == "sumOfSquares" then sumOfSquares
  else (squareOfSum - sumOfSquares)
  end
