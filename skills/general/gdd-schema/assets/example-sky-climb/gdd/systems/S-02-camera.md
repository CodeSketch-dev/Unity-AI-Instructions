---
id: S-02-camera
type: camera
title: Third person camera
priority: P0
fidelity: faithful
evidence: [CAP-003@00:30]
depends_on: [S-01-character]
recipe: freelook-third-person-camera
mode: third_person_orbit
distance_m: {default: 7, min: 4, max: 12}
fov: {default: 50}
features:
  - id: F-02.1
    name: Orbit with drag
    priority: P0
    acceptance:
      - "[play] dragging the right half orbits the camera without moving the character"
---
