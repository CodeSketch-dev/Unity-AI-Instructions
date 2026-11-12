---
id: S-11-vfx
type: vfx
title: Effects
priority: P2
fidelity: free
evidence: []
effects:
  - {id: fx_checkpoint, trigger: checkpoint_reached, kind: particle, budget_particles: 40, pooled: true}
features:
  - id: F-11.1
    name: Checkpoint effect
    priority: P2
    acceptance:
      - "[inspect] effects are pooled and within the particle budget"
---
