---
max_turns: 6
allowed_tools: [Read, Glob, Grep, Skill]
---
A Unity Editor tool fails with CS1654 after declaring `using var vertices = new NativeArray<float3>(count, Allocator.TempJob);` and assigning `vertices[0] = value;`. Explain the smallest correct ownership/lifetime fix, keep scheduled jobs safe and say what evidence would verify it. A neighboring using NativeArray only reads its elements; leave it unchanged.
