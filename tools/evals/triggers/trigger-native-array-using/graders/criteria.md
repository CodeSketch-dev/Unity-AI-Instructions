---
type: llm
weight: 1
---
The agent must consult the `native-array-using-mutation` skill, identify the readonly using value-type binding, recommend an ordinary mutable NativeArray with try/finally disposal after dependent jobs complete, preserve read-only using arrays and avoid unsafe/copy ownership workarounds. It must distinguish lint from actual assembly compile and scheduled test evidence. Negative case: a read-only using array or ordinary mutable NativeArray should not be rewritten merely because it mentions NativeArray.
