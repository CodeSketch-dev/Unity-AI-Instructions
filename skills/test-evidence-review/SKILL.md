---
name: test-evidence-review
description: "Audit whether tests, screenshots and logs actually prove a claim; list weak-evidence red flags and the missing proof. Use before reporting done, when reviewing a test report, or when a green result seems too easy."
triggers: evidence review, test proof, weak evidence, verify claim, screenshot proof, false positive test, bang chung, kiem chung, test khong du, bao cao that
---

# Test evidence review

Use before saying "verified". A claim needs proof that would FAIL if the claim were false.

## Steps
1. Write the claim as one sentence (e.g. "popup centres at 3 aspects", "no leak on reload").
2. List the evidence offered: test names, screenshot paths, log lines, numbers.
3. For each ask: could this pass while the claim is false? If yes it is weak.
4. Decide: sufficient, add proof, or downgrade the wording ("compiled, not run in Play").
5. Collect the missing proof yourself with the cheapest tool (MCP console read, targeted test, screenshot, measurement script) and re-judge.

## Weak-evidence red flags
- Test passes but asserts nothing about the changed behaviour, or mocks the thing under test.
- Skipped tests counted as pass; the SKIP count changed silently.
- Screenshot taken before the state was reached, in the wrong scene or resolution, or never looked at.
- Console "clean" read before the action ran, or filtered to warnings only.
- Compile success used as proof of serialization, prefab or scene correctness.
- EditMode result used for a Play Mode claim; Editor numbers presented as device numbers.
- "No errors" with no baseline; a single run in a flaky area.
- Measured the wrong object (prefab asset instead of scene instance, rect instead of rendered bounds).
- Results older than the last code change.

## Output
Claim | evidence | strength (strong / weak / none) | action taken. The final report wording must match the strongest proof obtained and name what was not verified.
