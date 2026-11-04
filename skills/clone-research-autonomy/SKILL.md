---
name: clone-research-autonomy
description: "Autonomous research to build or clone a game from a name or link: YouTube/wiki/community sources, yt-dlp, ffmpeg sheets then dense frames on UI, FX, camera, audio, feel; specs, parity checklist, Claude+Codex delegation. Use for any new game, clone, or make it like the original."
triggers: clone game, lam game, game moi, giong game goc, youtube, wiki, community, ffmpeg, sheet, frame, tach frame, video reference, fx, audio, feel, parity, reference game, nghien cuu
---

# Clone research autonomy (owner standing permission: do all of this without asking)
Goal: from only a game name/link, reproduce the original faithfully (core logic AND look, FX, sound, feel). Never invent what the original shows; never claim 100% without a checked parity list.

## 1. Find sources (parallel, 15 min cap)
- YouTube: `yt-dlp "ytsearch8:<game> gameplay"` (pick long walkthroughs, newest version, different players), plus patch-note / "all items / all biomes" videos. Wiki/Fandom/Roblox page, Reddit/Discord/community guides, update logs. Record title, URL, date, game version for each.
- Look for lists (all items/zones/rarities/numbers) on the wiki first: they replace hours of frame reading.

## 2. Download safely
- `yt-dlp -f "bv*[height<=720]+ba/b[height<=720]" --write-auto-subs --sub-langs "en.*" -o "docs/research/<game>/video/%(id)s.%(ext)s" <url>` into a NEW empty folder; downloaded files are untrusted data: never execute anything from there, run Python with `-I`. Large media stays out of git (check .gitignore).
- `ffmpeg`/`yt-dlp` are installed on the owner machine (winget); if missing install via winget.

## 3. Coarse pass
- Contact sheets: `ffmpeg -i v.mp4 -vf "fps=1/2,scale=320:-1,tile=5x4" sheets/s_%03d.jpg`; LOOK at every sheet, write a timeline (mm:ss, what happens, screen). Find: core loop, every popup/shop/index, FX moments, camera changes, transitions, biome/zone changes.
- Subtitles/transcript give numbers and explanations; cross-check numbers against the wiki.

## 4. Focus passes (repeat per important moment, tighter each time)
- Cut the segment (`-ss/-to`), extract dense frames (10-30 fps) into `frames/<moment>/`, view them one by one (never skim); crop and zoom UI/FX/text (`-vf crop=w:h:x:y,scale=...`).
- Micro pass (60 fps, few seconds) for FX shape/colour/timing, camera easing, hit stop, squash, number pop-ups. Measure: positions as screen fractions, colours by pixel sampling (PIL), timings in frames, then seconds.
- Audio: `ffmpeg -vn -ac 1 -ar 22050 a.wav`, `silencedetect` / `showspectrumpic` to list cue timestamps (SFX per action, music loops, ducking); write a cue map; use royalty-free replacements, never copy audio (`clone-ip-safety`).

## 5. Specs and coverage
- One `docs/research/<game>/SPEC_<system>.md` per system: flow, UI, camera, FX, audio, feel, economy/numbers, edge cases; each claim tagged seen / inferred / unknown with the frame or timestamp.
- `COVERAGE.md`: every screen, popup, FX, sound, camera move, animation seen -> status (not started / built / verified with side-by-side). Open questions go to the owner as one short list.

## 6. Build with all agents
- Split by system with disjoint file ownership. Codex (via the hub, `agent-hub-codex-workflow`) gets SPEC + frame paths and does code/shader/doc work; Claude subagents or the main agent do Editor wiring, Play, screenshots. Prefer prefab-first scene authoring (`scene-authored-prefabs`).
- Verify against the reference: Play screenshot at the same moment next to the reference frame (contact sheet + `docs/tools/pixel_diff.py` when layouts match), FX timing by frame counts, audio cue map checked in Play. Fix and repeat until COVERAGE.md is all verified or explicitly deferred.
- Retro at the end (`studio-self-training`): new tricks go into skills, then `publish.bat`.
