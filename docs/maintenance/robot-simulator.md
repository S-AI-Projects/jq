# Robot Simulator Reference Complexity Study

## Operation Domain & Bounds
The `turn(t)` operation operates on a strictly finite discrete domain:
- 4 cardinal orientations: `north`, `east`, `south`, `west`
- 2 rotational commands: `left`, `right`

Because the direction state space is constant ($|D| = 4$), the transition dictionary lookup and direction reassignment in `def turn(t)` take strictly $O(1)$ time and $O(1)$ space.

## Algorithmic Scaling vs Process Startup
When simulating an instruction sequence of length $N$:
- Overall algorithmic work scales linearly $O(N)$ with each instruction (Advance, Turn Left, Turn Right) executing in $O(1)$ steps.
- JQ CLI process execution time is dominated by fixed process startup and compilation overhead (~20ms on macOS).

## Empirical Timing Measurements
Measuring instruction strings of varying lengths over 5 repetitions (holding environment constant):
- Size 1 (`"R"`): Median = ~0.021s (1 operation)
- Size 5 (`"LAAAR"`): Median = ~0.022s (5 operations)
- Size 20 (`"RAALAAAARAALAAAARAAL"`): Median = ~0.024s (20 operations)
Algorithmic work scales with $N$, while single-step turns maintain a strict $O(1)$ constant bound.
