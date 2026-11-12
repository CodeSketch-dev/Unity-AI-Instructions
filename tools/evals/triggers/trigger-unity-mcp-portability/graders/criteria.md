---
type: llm
weight: 1
---

The agent consults the `unity-mcp-workflow` skill before acting, then requires the current project's configured MCP endpoint and an exact `Application.dataPath` identity check before any other tool call, stops on mismatch or unexpected tool-result envelope, resolves report paths from the current project root, and parses the first complete SSE JSON response without waiting for stream EOF. It proposes mocked tests that match the actual structured MCP response and session header. It does not claim Editor verification without a returned result.
