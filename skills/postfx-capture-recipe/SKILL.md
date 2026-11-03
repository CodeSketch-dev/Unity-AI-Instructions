---
name: postfx-capture-recipe
description: "Capture trustworthy Unity screenshots WITH post-processing: clone the Main Camera at runtime, disable its scripts, render to a RenderTexture, close auto-popups first. Use when judging environment/art quality or UI in Play; raw Scene View judgements are wrong."
triggers: screenshot, post processing, post fx, volume, bloom, scene view, capture, camera render, chup anh
---

# Post-FX screenshot recipe

- Judge art ONLY with the game's post-processing (Volume, grading, bloom). Scene View or a bare camera lies about saturation and contrast.
- Recipe (script-execute in Play): Instantiate(Camera.main.gameObject), remove AudioListeners, disable every MonoBehaviour except UniversalAdditionalCameraData, set farClip/fov, place + LookAt per shot, render to a RenderTexture(ARGB32, depth 24), ReadPixels, save the PNG in the scratchpad, destroy the clone and temporaries. Take several angles (overview, eye level, each landmark) and read them as a harsh art director: grade 0-10 and list defects.
- Auto popups (daily login, offline, welcome back) open on Play start: close them with the HUD close-all call (reflection) BEFORE any UI screenshot or audit; never leave a modal open while measuring.
- Entering Play while agents edit scripts causes recompiles: wait for IsCompiling false before capture; MCP calls fail with retries during a domain reload.
- The Game View screenshot tool shows the real HUD at the configured resolution; use it for UI, the clone-camera recipe for world shots.
