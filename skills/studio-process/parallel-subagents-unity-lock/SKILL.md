---
name: parallel-subagents-unity-lock
description: "Editor lock rules for parallel agents sharing one Unity Editor: FIFO lock with heartbeat, one writer, keep compiling, stop on denied calls. Use when several agents might use the Editor or MCP at once."
triggers: editor lock, mcp lock, parallel agents, heartbeat, single writer, compile, shared editor
---

# Unity Editor lock for parallel agents
- One Editor = one writer. Take the lock file (queue order, heartbeat timestamp) before any MCP mutation or compile; release at once.
- Stale heartbeat (older than a few minutes) may be taken over; note it in the handoff.
- Never run several script-execute calls in parallel; chunk long bakes.
- Leave the project compiling; on a denied call stop and report.
- See `editor-lane-single-writer` and `agent-team-protocol` for the full protocol.
