---
name: third-party-pack-recon
description: "Before designing anything on a purchased asset pack (characters, accessories), read its prefab structure on disk: where parts sit, which prefabs carry placements, what is loose at origin. Use before building shops/loadouts from a pack."
triggers: asset pack, loadout, accessories, character pack, prefab structure, placement, megapack, set prefab, wardrobe
---

# Third-party pack recon (do this first)

- List the pack folders and open ONE prefab of each kind as YAML (m_Name, m_Father, m_LocalPosition/Rotation/Scale, nested prefab modifications, m_IsActive). Answer: are loose accessories pre-placed (usually NOT: they sit at origin), where does wearing placement live (often inside the SET/outfit prefabs as children under rig bones), do base characters hold the parts, are there inactive toggles?
- If placement lives in set prefabs: EXTRACT bone-relative local transforms per item (and gender) with an Editor tool, merge duplicates (keep the most frequent placement, log conflicts), generate the catalog from it, and sell what the pack really contains grouped by category tabs. Do NOT hand-tune offsets or invent a curated list first; bounds-based auto-fit is only a fallback.
- Categories come from the pack (hair, face, glasses, hats, shirt, pants, wings, back, neck, hand, aura...), not from the design doc.
- Record findings in a research doc before coding; owner statements about pack behaviour are claims to verify on disk, not to assume either way.
