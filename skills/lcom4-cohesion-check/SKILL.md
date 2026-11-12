---
name: lcom4-cohesion-check
description: "Use when a class feels too big, mixes responsibilities, or is under review for splitting: compute LCOM4 (connected components of methods linked by shared instance fields) and split when it is above 1."
triggers: lcom4, cohesion, god class, class too big, single responsibility, split class, tach class, class qua lon, review architecture
---

# LCOM4 cohesion check

A deterministic answer to "does this class do more than one thing?". Idea from a friend's skill set (FakeMG/ai-instructions), adapted to our Unity C# house style.

## Algorithm
1. List the instance fields (`_field`, serialized fields, auto-props backing state). Ignore `static` and `const`.
2. Drop methods that say nothing about cohesion: constructors, trivial getters/setters (1-2 lines, one field), static methods, Unity empty callbacks.
3. For each remaining method list the instance fields it reads or writes (explicit `this._x` and implicit `_x` count the same). Field sharing only; do not link methods by calling each other.
4. Graph: methods are nodes, an edge joins two methods that share at least one field. LCOM4 = number of connected components (Union-Find or DFS).

## Special cases
- A method that touches no instance field is its own component (+1). Name it explicitly: it probably belongs in a static helper.
- One remaining method: LCOM4 = 1. No remaining methods: N/A.

## Verdict and output
- `LCOM4 = 1`: cohesive, leave it.
- `LCOM4 > 1`: propose N classes, one per component. Report `LCOM4: <n>`, then per component a responsibility label (or "unnamed, review manually"), its methods and fields, then the excluded and isolated methods.
- A split must keep the feature facade (see `house-code-patterns`, `static-bus-events`): the old class stays the owner and composes the new focused components. Never split just to hit the number when two components share a MonoBehaviour lifecycle on purpose; say so and stop.

## Use with
`superpowers:requesting-code-review` (add the number to the review), `staged-refactor-playbook` (do the split in a green batch).
