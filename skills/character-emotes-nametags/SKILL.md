---
name: character-emotes-nametags
description: Emotes (animator trigger layer, emote wheel) and nametags (single world-space label with a CullingGroup band). Use when the GDD has emotes, player names over heads, or chat-bubble style labels.
---

# Emotes and nametags

No precedent exists in the mined projects (`Character_UI` is only an effect icon + countdown); everything here is a design (INFERRED, report 19 sec 3.2). Keep it small and cheap.

## Emotes
- `EmoteId` (int) + `TriggerEmote` parameters on an emote layer of the rig controller; the emote list per rig is part of the rig asset and `character-catalog.json` (`emotes`); clips are authored per rig and whitelisted in the required parameters.
- `Event_Character_Emote(id, character)` (`static-bus-events`); the animator plays it, the camera and movement are not blocked unless the design says so; moving cancels looping emotes.
- UI: an emote wheel or row uses popup/anchor rules (`ui-popup-anatomy`, `mobile-hud-layout`), a button per owned emote, locked ones dimmed; ownership in the data block.
- Bots may trigger emotes at a low random rate (flavour); throttle by cooldown.

## Nametags
- One text per character, enabled only inside a near `CullingGroup` band (~25 m), max 8 visible (`character-perf-budgets`); text set only when the name changes; shared font atlas; shared pooled canvas or a reused 3D text (`ui-text-tmp`: project text component).
- Colour/outline for the local player vs others; billboard to the camera; scale by distance within limits; localized default names when empty.
- Anchor: the rig slot `nametag` (head bone + offset), resolved once at skin load.
- Do not rebuild text or layout every frame; no per-nametag Update (one manager ticks all).

Verify: 20 characters, 8 tags visible, none beyond the band, names update on change only, emote triggers work for player and bots on every rig.
