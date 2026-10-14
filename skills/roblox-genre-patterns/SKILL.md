---
name: roblox-genre-patterns
description: Catalog of Roblox genres (simulator, pet/egg, tycoon, steal/carry, obby, TD, treadmill, fighting, survival) with core loops and required systems. Use when planning a clone or deciding which systems it needs.
---

# Roblox genre patterns

Roblox hits are built from a small set of recurring loops. Identify the genre first; it tells you which systems are non-negotiable and which numbers to study. Details per genre are in `references/genres.md` (read the relevant section only).

## How to use
1. Classify the reference game (often a hybrid, e.g. egg hatching + carry-and-defend + treadmill).
2. Read the matching genre sections; build the **required systems** checklist for the clone.
3. Compare with what `gameplay-video-analysis` found. Anything in the checklist that the analysis didn't show is an open question for the human to verify, not something to silently add.
4. Pick mobile adaptations (see below) before building.

## Cross-genre building blocks (recur everywhere)
- **Currency loop**: earn -> spend on a multiplier -> earn faster. Always a visible next goal.
- **Zones/worlds** gated by a stat (speed, strength, coins) with a recommended-level banner.
- **Collectibles with rarity tiers** (color-coded, rarer = better FX and bigger).
- **Rebirth/prestige** resetting progress for a permanent multiplier.
- **Pets/companions** giving income or boosts; equip slots; eggs/gacha with luck boosts.
- **Shops**: gear, trails/cosmetics, boosts, passes (permanent multipliers), limited offers.
- **Other-player presence**: real or simulated (bots) so the world feels alive and competitive.
- **Safe zone / base** and risk outside it.
- **Daily rewards, timed events, leaderboards** for retention.
- **Social proof UI**: join/leave toasts, global announcements for rare drops.

## Mobile adaptation rules of thumb
- Everything reachable with two thumbs; one primary action button (see `mobile-hud-layout`).
- Auto-actions (auto-collect, auto-attack near target) because holding and aiming is costly on touch.
- Short sessions: first reward under 30 s, meaningful upgrade within 2-3 min.
- Cut Roblox-only mechanics (chat, complex trading, user-generated content) unless the reference depends on them.
- Replace multiplayer with bots unless netcode is in scope (`npc-bots-and-enemies`).
