# Instructions

Given a person's allergy score, determine whether or not they're allergic to a given item, and their full list of allergies.

An allergy test produces a single numeric score which contains the information about all the allergies the person has (that they were tested for).

The list of items (and their value) that were tested are:

- eggs (1)
- peanuts (2)
- shellfish (4)
- strawberries (8)
- tomatoes (16)
- chocolate (32)
- pollen (64)
- cats (128)

So if Tom is allergic to peanuts and chocolate, he gets a score of 34.

Now, given just that score of 34, your program should be able to say:

- Whether Tom is allergic to any one of those allergens listed above.
- All the allergens Tom is allergic to.

Note: a given score may include allergens **not** listed above (i.e. allergens that score 256, 512, 1024, etc.).
Your program should ignore those components of the score.
For example, if the allergy score is 257, your program should only report the eggs (1) allergy.

For the `allergicTo` operation, these selected tests use the following inputs and expected results:

| Test case | Item | Score | Why the result follows from the specification | Expected |
|---|---|---:|---|---|
| `testing for eggs allergy:not allergic to anything` | `eggs` | `0` | No tested allergen is present in the score. | `false` |
| `testing for eggs allergy:allergic only to eggs` | `eggs` | `1` | The score contains the eggs value (`1`). | `true` |
| `testing for eggs allergy:allergic to eggs and something else` | `eggs` | `3` | The score is eggs (`1`) plus peanuts (`2`), so the eggs value is present. | `true` |

These are exact in-contract examples: an allergy score encodes the listed allergens, and the eggs value is `1`. Other allergens in the score do not cancel eggs. The specification also says to ignore score components for allergens not listed above (for example, `256`) when reporting the allergy list.

The exercise does not specify behavior for inputs outside this contract, such as a non-numeric score or querying an item that is not in the listed allergen set. These examples do not impose coercion, extra exception rules, or an ordering requirement.
