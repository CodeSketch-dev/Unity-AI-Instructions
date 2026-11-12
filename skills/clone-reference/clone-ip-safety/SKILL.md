---
name: clone-ip-safety
description: "Asset provenance and IP hygiene for clones: track asset origin, flag ripped/trademarked content, store-safe naming. Use when importing from a reference game, naming the game, or before a public build/store listing."
---

# Clone IP safety

The company's workflow reuses reference assets heavily during development; that is fine for prototyping and risky for shipping. The point of this skill is not to block work but to make the risk visible and cheap to fix before release. This is engineering hygiene, not legal advice; recommend a legal review before store submission.

## During development
1. Keep `docs/asset-provenance.md`: one row per asset group (path, source, status). Status values: `own`, `licensed` (license + proof link), `reference-temp` (taken from the reference game; must be replaced before release), `unknown`.
2. When you import or port something from the reference (see `asset-transfer-closure`), add or update its row right then. Reference-temp content stays in clearly named folders when practical so replacement is a swap, not a hunt.
3. Don't spread reference-only content into many places: prefer config/prefab indirection so a replacement touches one asset.

## Before any public/shared build
- Names, logos, icons, character likenesses, music and sound effects from the reference game or from Roblox itself are the highest risk: replace or license them.
- Roblox-specific branding (Robux, Roblox logo, "Roblox" in text) must not appear.
- Check third-party packages and asset-store items for license terms allowing mobile redistribution; keep license files.
- Fonts: confirm license for app embedding.

## Store listing
- Original title, icon and screenshots; no reference game's name, keywords or imagery in metadata.
- Don't imply affiliation with the reference game or Roblox.
- Kid-directed audiences bring extra policy requirements; see `monetization-integration`.

## Report
At each gate, summarize: counts by status, the top 10 replacement tasks, and anything unknown. Ask the human how to prioritize replacements; don't silently substitute art because the visual identity is a product decision.
