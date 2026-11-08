---
name: dedicated-server-no-client-state
description: Use when a feature works in Editor host/host-client tests but does nothing against a dedicated (headless) server. Server code must not read client-only registries or lists filled in OnStartClient.
triggers: dedicated server, headless server, host works server not, client list empty, OnStartClient list, FishNet server, server khong chay
---
# Dedicated server has no client state

A static list filled in `OnStartClient` (e.g. `CLIENT_PANES`) is EMPTY on a dedicated server. Server-side logic that calls such a lookup silently gets null; Editor host mode hides it because the host is also a client.
- Give server code its own registry (add in `OnStartServer`, remove in `OnStopServer`) or look up through server-owned state.
- Always run the feature once against a built headless server with scripted clients (e.g. `-testrotate` style flag logging the synced value) before calling it done; a host/Editor pass is not evidence.
- Grep for `CLIENT_` statics used inside `IsServerStarted` branches.
