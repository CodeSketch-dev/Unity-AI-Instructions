---
name: ui-sprite-audit
description: Use before importing ANY generated or edited UI sprite: run sprite_audit.py (outline uniformity/thickness, exact rounded rectangle, corner cap, size cap, clipping, magenta fringe) and reject on FAIL; a hook-style gate so bad Codex art never reaches the game.
triggers: sprite audit, kiem tra sprite, outline deu, bo goc, 9 slice, texture ui, button sprite, codex art, image gen, vien mong, rang cua
---
# UI sprite audit (run before import, every batch)
`python -I <skills>/ui-sprite-audit/sprite_audit.py FILE... [--max-long 512] [--min-outline-pct 6.5] [--kind button|board|icon]` -> PASS/FAIL per criterion, exit 1 on any FAIL.
- Any FAIL = REWORK: send the failing line (with the number) back to the generator; never import, never "fix by eye".
- It measures: size cap, clipping (canvas corners must be transparent), magenta fringe, outline thickness uniformity (p90-p10 <= 1 px) and minimum thickness, straight middle strips (<= 1 px wave), corner radius 20-36% of height (buttons), corner cap <= 36% of the short side, dominant colour (check it matches the file name: batches came back shuffled).
- Measured examples: analytic rounded-rect button 448x155 = outline 12 px spread 0.0, radius 25% -> PASS; a model-drawn 1024x355 button = outline 7 px = 2.3% of height -> FAIL (too thin).
- Pair with `ui-art-quality-gate` (criteria) and `codex-ui-sprite-brief` (how to ask). After import also dump the live Sprite (ppu, border) in Play.
