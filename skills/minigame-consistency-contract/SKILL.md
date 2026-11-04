---
name: minigame-consistency-contract
description: "One design system across all minigames: fill a consistency matrix against the reference games (shop, popups, bars, icons, pets, labels, camera, fog, audio, perf) before building or fixing, and sweep each defect class everywhere. Use for new minigames, ports, clones, owner defect reports."
triggers: consistency, dong bo, minigame, game khac nhau, cung style, shop, popup, pets, label, currency bar, design system, sweep, kiem tra toan bo, khong nhat quan
---

# Minigame consistency contract
Owner rule: all minigames feel like one studio game. Shared systems are reused; only content, cash balance and original-game specifics differ.

## 0. Prefab ownership (owner order, never violate)
- Each minigame owns SEPARATE UI prefabs and SEPARATE code for its popups, shop pages AND shop tabs, cards/rows, toasts, HUD plates, reveal. Never make one minigame's popup an instance, variant or nested copy of another minigame's prefab, and never share their scripts or a common shop/popup base class. Why: minigames differ (this one has no tab that another has), and sharing makes the code tangled.
- Shared prefabs are ONLY: the currency bar and a few small common buttons (settings button, shop button, close-style buttons). Everything else is per-minigame.
- "Same UI" means same ART (sprites, frames, fonts, colours) and same STRUCTURE (hierarchy, layout, spacing, sizes), copied into the minigame's own prefab by reference to the same sprite assets. Open the reference prefab to copy values, do not reuse it.

## 1. Matrix first (before code)
Create `docs/superpowers/plans/<date>-<game>-consistency-plan.md` with a table: System | Reference of truth | This game today | Gap/action | Owner | Status. Mandatory rows: shop (Shop_All look and structure, own prefab and own tabs per minigame; cards, gem buttons), popups (frame/header/close/fonts from the reference style), currency bars and icons (one shared prefab, shared icons; cash balance per minigame), toast/hints/settings/offline, HUD plates, pets (size logic + overhead label from the reference minigames), world labels/billboards, camera + far render + fog, map material/shader, audio/SFX, economy numbers, scene authoring (prefab-first), performance on low-end. Show the plan to the owner in the reply, then execute without waiting.
## 2. Defect-class sweep (stop ping-pong prompts)
When the owner reports a defect: name its class (overlap, blurry icon, wrong size, missing label, off-style popup...), grep/audit EVERY screen and EVERY minigame for the class, fix all, add a check to the matrix and the retro, publish the rule.
## 3. Rules that always hold
Reference first, reuse ART and STRUCTURE (not prefabs or code, see section 0), generated art only for missing pieces in the reference style, no invented products/UI, shared icons everywhere, measured audits (overlap script, dx/dy, text bounds), Play screenshot vs reference, one Editor writer at a time, parallel Codex for code.
## 4. Done
Matrix all green with evidence, boss bar (`studio-boss-quality-bar`) >= 4 on every axis, retro published.
