---
name: fishnet-external-move-reconcile
description: Use when a FishNet predicted player is moved by the server outside Replicate (carry, teleport, knockback) and the owner client stays at a stale position, jitters, or snaps late. Fixes idle-owner reconcile starvation.
triggers: fishnet, reconcile, prediction, client position wrong, desync, carry, teleport, knockback, server moves player, lech vi tri, giat client
---
# FishNet: server-side moves need forced reconciles

**Trap:** FishNet only keeps sending `[Reconcile]` while the owner is replicating (`_remainingReconcileResends`, re-armed by replicate activity). If the server moves an idle owner by itself (partner carry, teleport/respawn, knock), `CreateReconcile` runs every tick but nothing reaches the client: the owner stays at the old spot while the server has moved it.

**Fix (measured: 0.88 m error and 0 reconciles -> 0.001-0.04 m, 120 reconciles/2 s):**
1. Keep a counter set by every server-side external move (`ServerCarry/ServerTeleport/ServerKnock`, ~8 ticks).
2. In `CreateReconcile`, while the counter > 0 pass `Channel.Reliable` to the `[Reconcile]` method (FishNet re-arms the resend count for reliable) and decrement.
3. A pull that the owner cannot simulate lags by `pullSpeed x reconcileLeadTicks`; put the last pull velocity in the reconcile state and apply it (with mild decay) inside the owner's replicate `Step` so replays stay close.

**Diagnose first:** log, per owner client, reconciles received per 2 s and `|predicted(tick) - rs.Position|` (ring buffer by tick); a server count of 120 vs a client count of ~0 proves starvation. Gate the logs behind a scripting define.
Also: TickRate 60 halves step size; stop Play Mode before asset refresh in the Editor.
