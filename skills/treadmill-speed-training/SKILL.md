---
name: treadmill-speed-training
description: "Treadmill / speed-training loop: auto-training state, tick-based speed earn, level-scaled speed and jump, treadmill tiers with unlocks, fake runners. Use when the clone has a train-to-run-faster mechanic."
---

# Treadmill speed training

From monkey-escape `Treadmill`, `Character_Monkey`, `Character_Treadmill_Manager` (report 04 sec 2.2, 8.5, VERIFIED). Genre context: `roblox-genre-patterns`. Economy numbers are tuned by the balance loop (`economy-auto-balance`).

- `Treadmill : OptCollisionRegister`; types (Normal, Candy, Chocolate, Admin, VIP, IAP x10, God, Infinity, x200, x20K, Special) each with a multiplier; unlock by Free / Reward / Cup (currency) / IAP / Subscription; multiplier as a compact number string in the reference, use a typed double + formatter in new code.
- Entering a treadmill sets the character to `AutoTraining` and the KCC state `Treadmill`: force-run animation, jump blocked, movement limited to the base speed, trained speed is not carried while on it.
- Earn tick: every 0.15 s while moving above 0.5 m/s (and on the treadmill): `gain = speedLogicMultiplier * treadmillPoint * expMultiplier * (1 + boost)`; aura/trail multipliers apply (`cosmetic-slot-providers`).
- Speed from level: real speed = 4.5 + `max(0, level - world.LevelRequired) * 0.5`; jump +0.1 per level; display speed converts with `(display + 14.5) / 5`; `SpeedLimitFactor` scales only the added speed (`kcc-character-controller/references/feel-table.md`).
- Fake multiplayer: the manager spawns fake runners with random skins that swap every 90-120 s (first load staggered over 1.5 s) (`bots-as-players`).
- UI: run/buy/ads states on the treadmill button; ad-break poll every 1 s; red dot when an unlock is affordable (`ui-button-anatomy`).
- Persist level, trained speed and unlocked treadmills in the data block; rebirth later resets them (`rebirth` pattern).

Verify: speed rises at the expected rate (measured with a clean save at timeScale 1, `rule-qa-validity`), jump blocked on the belt, leaving restores controls, runners swap skins.
