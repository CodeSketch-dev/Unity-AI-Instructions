# Combat feel numbers (report 15 sec 6; VERIFIED unless marked)

Soft defaults from knife-tower (KT), thunder-break-egg (TBE), climb-tower (CT); override from the reference footage of the clone.

| Hook | Value |
|---|---|
| Camera shake | amplitude 0.4, frequency 3.5, duration 0.2 (default); boss/fall 0.6 / 4 / 0.3 and 0.3 / 3 / 0.15; fall shake scaled ~x5 over 0.4 s |
| Camera FOV punch | +12 deg, out 0.18 s, back 0.45 s |
| Scale punch on hit | (0.18, -0.22, 0.18) over 0.22 s, elasticity 8; rotation shake z 9 deg over 0.25 s |
| Haptics | medium on player hit/kill (KT), light on egg break (TBE) |
| Floating damage | world-space pooled text, rise 1.6 m, 0.75 s, red normal / gold break or crit (scale 1.0 / 1.25); CT: lives 3 s, normal (1, 0.4, 0.4), critical (1, 0.84, 0) with a crit sprite |
| HP bar | TBE world bar width 1.6, height 0.2, hidden at >= 0.999 and after break; CT red bar + yellow trailing bar (delay 0.1 / 0.1 s, trail 0.5 s) with a 1.2 scale-up for 0.25 s on change; boss bar = fill image with threshold lines |
| Hit fx / audio | pooled hit fx at target + 0.75 up - dir * 0.5; per-tool sfx for used and hit; attackable indicator toggled by the checker |
| Impact timing | 0.88 of the swing clip (TBE) or 0.1 + 0.25 s after press (KT) |
| Hit-stop | NOT implemented in any read project; proposal 0.05-0.08 s time-scale dip or animator speed 0 (INFERRED, unverified) |
| Death / respawn | revive delay 2 s, ragdoll 2.5 s, revive shield; TBE knock lie 1.6 s + stand 0.55 s; egg respawn 3-6 s |

Rules: feedback is event-driven from `Event_Combat_Hit` (`combat-health-status`); pool every spawned text/fx (`pool-everything`); keep camera effects small and short; one feel setting block per game in a factory.
