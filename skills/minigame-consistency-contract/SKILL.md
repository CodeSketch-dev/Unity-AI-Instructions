---
name: minigame-consistency-contract
description: "One design system across all minigames: fill a consistency matrix against the reference games (shop, popups, bars, icons, pets, labels, camera, fog, audio, perf) before building or fixing, and sweep each defect class everywhere. Use for new minigames, ports, clones, owner defect reports."
triggers: consistency, dong bo, minigame, game khac nhau, cung style, shop, popup, pets, label, currency bar, design system, sweep, kiem tra toan bo, khong nhat quan
---

# Minigame consistency contract
Owner rule: all minigames feel like one studio game. Shared systems are reused; only content, cash balance and original-game specifics differ.

## 1. Matrix first (before code)
Create `docs/superpowers/plans/<date>-<game>-consistency-plan.md` with a table: System | Reference of truth | This game today | Gap/action | Owner | Status. Mandatory rows: shop (shared Shop_All, tabs, cards, gem buttons), popups (frame/header/close/fonts from the reference style), currency bars and icons (one shared prefab, shared icons; cash balance per minigame), toast/hints/settings/offline, HUD plates, pets (size logic + overhead label from the reference minigames), world labels/billboards, camera + far render + fog, map material/shader, audio/SFX, economy numbers, scene authoring (prefab-first), performance on low-end. Show the plan to the owner in the reply, then execute without waiting.
## 2. Defect-class sweep (stop ping-pong prompts)
When the owner reports a defect: name its class (overlap, blurry icon, wrong size, missing label, off-style popup...), grep/audit EVERY screen and EVERY minigame for the class, fix all, add a check to the matrix and the retro, publish the rule.
## 3. Rules that always hold
Reference first, reuse before create, generated art only for missing pieces in the reference style, no invented products/UI, shared icons everywhere, measured audits (overlap script, dx/dy, text bounds), Play screenshot vs reference, one Editor writer at a time, parallel Codex for code.
## 4. Done
Matrix all green with evidence, boss bar (`studio-boss-quality-bar`) >= 4 on every axis, retro published.
