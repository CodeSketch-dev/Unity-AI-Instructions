---
name: blender-rig-retarget-pet-pipeline
description: "Remake a mesh on a reference armature so original animation clips still play: read rig and actions, skin the new mesh to the same bone names, bake, verify. Use when replacing a rigged model but keeping its clips."
triggers: rig, retarget, armature, bones, skin weights, animation clips, pet, fbx, blender, bake, idle walk
---

# Rig retarget pipeline (new mesh, original clips)
1. Read the source armature and action list (names, frame ranges) with a headless Blender script; never copy the source mesh into the shipped project (`clone-ip-safety`).
2. Build the new mesh, parent it to an armature with identical bone names/hierarchy; auto-weights then fix wings, tails, serpent bodies by hand.
3. Bake the same actions (Idle plus Walk/Move/Fly, plus Attack/Sleep where the source has them) onto the new armature.
4. Export FBX, re-import and verify bone-name and clip parity plus deformation on several frames (`char-animator-reference-parity`).
5. A static mesh is never a deliverable.
