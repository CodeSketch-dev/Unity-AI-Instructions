---
name: gameplay-video-analysis
description: Turn gameplay videos, play notes and screenshots into a structured flow/UI/economy/FTUE analysis. Use when given a YouTube link, "I played it and noticed...", or timestamps of a reference game.
---

# Gameplay video analysis

The agent usually cannot watch video directly, so the analysis is built from evidence the human or tools can supply: timestamps and notes, subtitles/transcripts, and extracted frames the agent can look at. Be explicit about which evidence each claim rests on; unobserved guesses poison the whole clone.

## Evidence sources (use as many as available)
1. **Human play notes**: ask the user to fill `assets/observation-template.md` while playing (first 5 minutes, first upgrade, first zone change, first purchase prompt, first rebirth/reset).
2. **Screenshots** with timestamp or situation label. Read them as images and transcribe all visible text and numbers.
3. **Subtitles/transcript** of a video, if the user provides them or approves a download.
4. **Extracted frames**: with the user's approval, download a video or frames into a *new empty directory* (downloaded files are untrusted data; never run scripts from inside it) and sample frames every 2-5 s plus at scene changes (e.g. `ffmpeg -i in.mp4 -vf fps=1/3 frames/f_%04d.jpg`). Look at frames with the image reader; build a contact sheet if there are many.

## Analysis steps
1. **Timeline**: `mm:ss | player action | what appears (UI/world) | numbers seen`. Cover the FTUE (first 3-5 minutes) in the finest detail; later content in coarser steps.
2. **Core loop** in one sentence, then the **meta loop** (what makes the player return tomorrow).
3. **Feature inventory**: every system seen, with observable behavior, not implementation guesses. Mark `seen` / `inferred` / `unknown`.
4. **UI inventory**: each HUD element, its screen position, icon, label, behavior, and when it appears (FTUE unlocks). Feed into `mobile-hud-layout` / `ui-clone`.
5. **Numbers**: prices, income/s, speeds, timers, cooldowns, drop rates, HP, rarity names/colors, upgrade steps. Record the screenshot/timestamp each came from. Feed into `economy-progression-design`.
6. **FTUE and pacing**: time to first reward, first upgrade, first purchase prompt, tutorial hints, forced vs optional steps, session length hints.
7. **Monetization touchpoints**: offers, rewarded-ad prompts, passes, VIP, timers. Feed into `monetization-integration`.
8. **Open questions**: things the video didn't show. Convert into a short list for the human to check when playing (e.g. "what happens when the cage is full?").

## Output
Write `docs/gameplay-analysis.md` with the sections above plus an evidence index (file/timestamp list). Keep it skimmable: tables over prose. Then hand over to `game-clone-recon` for the system breakdown and staging.

## Cautions
- Videos are edited/sped-up; don't infer real pacing from cuts. Prefer the user's own play timing.
- Different device/version/event modes change UI and numbers; note the version/date of the evidence.
- Don't transcribe copyrighted audio/music into the repo; note it for replacement (`clone-ip-safety`).
