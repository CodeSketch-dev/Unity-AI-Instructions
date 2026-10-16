# Scenario: render-parity-debugging

**Prompt:** Ported model looks flat compared with the reference.

**Expected:** Compares material, textures, property block, vertex colour space and lighting; fixes only the divergent path; before/after sheet.

**Must not:** Rebuilds materials blindly, substitutes shaders silently.
