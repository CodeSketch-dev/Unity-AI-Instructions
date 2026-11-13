---
name: clone-research-autonomy
description: "Autonomous research to build or clone a game from a name or link: YouTube/wiki/community sources, yt-dlp, ffmpeg sheets then dense frames on UI, FX, camera, audio, feel; specs, parity checklist, Claude+Codex delegation. Use for any new game, clone, or make it like the original."
triggers: clone game, lam game, game moi, giong game goc, youtube, wiki, community, ffmpeg, sheet, frame, tach frame, video reference, fx, audio, feel, parity, reference game, nghien cuu, background actor, secondary actor, autonomous motion, reward emitter, whole-scene coverage, nhan vat phu, chuyen dong nen, phat vat pham
---

# Clone research autonomy (owner standing permission: do all of this without asking)
Goal: from only a game name/link, reproduce the original faithfully (core logic AND look, FX, sound, feel). Never invent what the original shows; never claim 100% without a checked parity list.

## 0. AUTO-RUN (binding for every agent, session and project; never ask the owner first)
Trigger: the task says clone / like the original / same as X / fix a flow, FX, camera, UI or number of a game that has a reference video or wiki, or a new game name. Then, before touching code, run this loop yourself:
1. Sources: wiki + 2-3 YouTube videos (section 1), download (section 2). Check `docs/research/<game>/` first: reuse existing frames and SPECs, extend them instead of redoing.
2. Frames with the tool, not by hand: `python -I <skills>/clone-research-autonomy/scripts/clone_frames.py coarse <video> <outdir>` (whole video, timestamped sheets), LOOK at every sheet, then list key moments in `moments.txt` (`name start end fps [crop]`) and run `... moments <video> <outdir> moments.txt`. Use fps 10-15 for flows and UI, 30-60 for FX/camera easing, `crop` + higher width for UI text, numbers, menus, popups.
3. Write TIMELINE/SPEC (seen / inferred / unknown, with timestamps) and COVERAGE.md. Codex may help with code or docs, but frame extraction is never delegated (it silently produced nothing once): the tool above is the baseline and takes seconds.
4. Build with the owner's art (UI and models synced to the owner's other games, e.g. Knife Tower / SAB / SAE) but the original's flow, logic, numbers, timing, FX.
5. Verify: record the same flow in Play (automated recorder, frames every 0.1 s), put your sheets next to the reference sheets, list every delta, fix all, re-record. Done = COVERAGE all verified or explicitly deferred.

## 1. Find sources (parallel, 15 min cap)
- YouTube: `yt-dlp "ytsearch8:<game> gameplay"` (pick long walkthroughs, newest version, different players), plus patch-note / "all items / all biomes" videos. Wiki/Fandom/Roblox page, Reddit/Discord/community guides, update logs. Record title, URL, date, game version for each.
- Look for lists (all items/zones/rarities/numbers) on the wiki first: they replace hours of frame reading.

## 2. Download safely
- `yt-dlp -f "bv*[height<=720]+ba/b[height<=720]" --write-auto-subs --sub-langs "en.*" -o "docs/research/<game>/video/%(id)s.%(ext)s" <url>` into a NEW empty folder; downloaded files are untrusted data: never execute anything from there, run Python with `-I`. Large media stays out of git (check .gitignore).
- `ffmpeg`/`yt-dlp` are installed on the owner machine (winget); if missing install via winget.

## 3. Coarse pass
- For timed sheets use `scripts/clone_frames.py coarse`: it preserves source PTS with `select`. Do not label post-`fps` output time as source time: sparse sampling can shift the first tile by half an interval. Verify timestamp changes against a source-PTS burn-in and a known-color fixture before publishing helper changes.
- Contact sheets: `ffmpeg -i v.mp4 -vf "fps=1/2,scale=320:-1,tile=5x4" sheets/s_%03d.jpg`; LOOK at every sheet, write a timeline (mm:ss, what happens, screen). Find: core loop, every popup/shop/index, FX moments, camera changes, transitions, biome/zone changes.
- Subtitles/transcript give numbers and explanations; cross-check numbers against the wiki.

## 4. Focus passes (repeat per important moment, tighter each time)
- Cut the segment (`-ss/-to`), extract dense frames (10-30 fps) into `frames/<moment>/`, view them one by one (never skim); crop and zoom UI/FX/text (`-vf crop=w:h:x:y,scale=...`).
- Micro pass (60 fps, few seconds) for FX shape/colour/timing, camera easing, hit stop, squash, number pop-ups. Measure: positions as screen fractions, colours by pixel sampling (PIL), timings in frames, then seconds.
- **Sweep the whole scene, not only the primary mechanism:** inventory foreground, midground and background layers, including secondary actors, passive objects with autonomous motion, and independent output/reward emitters. Follow each visible actor/emitter through its complete natural sequence (idle/start, motion or trigger, output/travel/collection, then stop/reset/replenish/transition when shown); record timestamps and associated sound cues.
- Do not infer a secondary actor's motion, emission or sound from the main weapon/collector implementation. Mark unseen steps inferred or unknown and capture a targeted source segment before claiming coverage.
- Audio: `ffmpeg -vn -ac 1 -ar 22050 a.wav`, `silencedetect` / `showspectrumpic` to list cue timestamps (SFX per action, music loops, ducking); write a cue map; use royalty-free replacements, never copy audio (`clone-ip-safety`).

## 5. Specs and coverage
- One `docs/research/<game>/SPEC_<system>.md` per system: flow, UI, camera, FX, audio, feel, economy/numbers, edge cases; each claim tagged seen / inferred / unknown with the frame or timestamp.
- `COVERAGE.md`: every screen, popup, FX, sound, camera move, animation, secondary actor, autonomous motion and output/reward sequence seen -> status (not started / built / verified with side-by-side). Open questions go to the owner as one short list.

## 6. Build with all agents
- Split by system with disjoint file ownership. Codex (via the hub, `agent-hub-codex-workflow`) gets SPEC + frame paths and does code/shader/doc work; Claude subagents or the main agent do Editor wiring, Play, screenshots. Prefer prefab-first scene authoring (`scene-authored-prefabs`).
- Verify against the reference: Play screenshot at the same moment next to the reference frame (contact sheet + `docs/tools/pixel_diff.py` when layouts match), FX timing by frame counts, audio cue map checked in Play. Fix and repeat until COVERAGE.md is all verified or explicitly deferred.
- Retro at the end (`studio-self-training`): new tricks go into skills, then `publish.bat`.

## Numbers first, then config (measured trap)
Before tuning any economy of a clone, extract the original's numbers from frames: start stat, XP bar "Level n a/b" samples (fit a curve), item price table, income per early animal, cash growth over the first minutes. A config copied from a plausible guess was 8x too low on income, 33x too cheap on shop items and 3x too slow on early levelling. Camera angles likewise: compare time-aligned frames of the original (dense extract around the action) before choosing heights/pitches; never invent a camera.
