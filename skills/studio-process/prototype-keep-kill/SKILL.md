---
name: prototype-keep-kill
description: "Timeboxed prototype process: one question, throwaway vs keep, greybox, instrumented playtest, written keep/kill criteria, rewrite on keep. Use when testing a new mechanic, minigame idea or vertical slice before committing production time."
triggers: prototype, spike, vertical slice, mvp, is it fun, greybox mechanic, keep or kill, timebox, throwaway, thu nghiem y tuong, ban mau, co vui khong, thu y tuong
---

# Prototype keep/kill

Source: third-party example (process), rewritten. Inspired by: gamedev-skills/awesome-gamedev-agent-skills skills/workflows/prototype-fast. Use before `recipe-add-minigame` or any new system whose fun is unproven.

## Brief (fill before coding)
- QUESTION: one binary thing to prove. Two questions mean two prototypes.
- CORE VERB: the single action repeated.
- THROWAWAY or KEEP-ROUGH: decide now; most are throwaway.
- TIMEBOX: 30-90 min per mechanic; stop when it ends.
- KEEP IF / KILL IF: observable signals, written first.

## Method
1. Greybox with primitives; stub economy, save, menus, audio. Only the core verb is real.
2. Instrument the thing being judged (on-screen numbers for speed, timing window, reward rate).
3. Prototype outside the shipping tree or branch (separate scene/folder, never referenced by production assemblies).
4. Playtest yourself, then one uncoached person; watch where they struggle.
5. Decide with the criteria, log the lesson in the feedback notes either way.

## Criteria examples
- KEEP: a fresh player performs the verb on purpose within about 30 s and repeats the loop unprompted.
- KILL: it is only fun after you explain it; fun needs systems far beyond the prototype; you are adding art to avoid admitting the verb is flat.
- RETUNE: one variable is clearly off (too slow, window too tight): change it and retest once.

## Rules
- A KEEP authorizes a rewrite in the production structure (prefabs, factories, data), not promotion of the spike. Follow `done-means-wired` when rebuilding.
- Do not polish art, menus or audio before the verdict.
- For mobile kids' games also ask: understandable without reading in 30 s?

Related: `spec-then-plan`, `game-clone-recon`, `recipe-add-minigame`, `perf-triage-ladder`.
