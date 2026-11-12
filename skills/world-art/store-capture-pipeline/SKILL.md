---
name: store-capture-pipeline
description: "Capture store screenshots and UA video from a running Unity game: photo mode (hide HUD/world labels, free camera), exact-size ScreenCapture, frame-sequence recorder with Time.captureFramerate, ffmpeg encode, and the traps that wasted time. Use for Play Store / App Store assets and ad creatives."
triggers: store screenshot, feature graphic, app store, play store, ua video, ad video, gameplay video, capture, anh store, video quang cao, photo mode
---

# Store capture pipeline (Unity, Play Mode, driven from script-execute)
- Editor-only helpers (keep in an Editor folder): `PhotoMode.Begin()` disables the Cinemachine brain (by type NAME via reflection, no assembly ref), root canvases and world TMP labels, remembers them and `End()` restores; `Place(pos, lookAt, fov)`; `Shot(path)`; a `VideoCapture` that sets `Time.captureFramerate`, calls `ScreenCapture.CaptureScreenshot` per `EditorApplication.update` tick, and stops itself.
- Size = Game View size (set the Game View to 1920x1080 / 1080x1920 / 1080x1080 first). The file lands one frame after the call; Read it afterwards and LOOK at it.
- TRAPS: `ScreenCapture.CaptureScreenshot` writes PNG data even for `.jpg` names (name frames `.png`, ffmpeg `-i f_%05d.png`). Timed reward popups (daily, free cash, offline) cover shots: close modals in the SAME script call and every few frames while recording. Day/night cycles darken the sky: capture right after a day starts. Hiding world TMP leaves signs as dark empty boards: hide those meshes or keep text. Tutorial pointers are world objects with game-specific names: find them by hierarchy dump, not by guess.
- Encode: `ffmpeg -framerate 30 -i f_%05d.png -c:v libx264 -pix_fmt yuv420p -crf 18 out.mp4`; keep frames and mp4 OUTSIDE the repo (hundreds of MB).
- Review like an art director: a clip needs a SUBJECT in frame, one action, a hook in the first 3 s and an end card; an orbit around empty props scored 4/10, real gameplay with combos scored 5.5/10 until the HUD clutter and overlapping notices were fixed.
- Specs to verify in the store console before upload: Play icon 512, feature graphic 1024x500 no alpha, 2-8 phone shots, optional 7"/10" tablet shots, promo video = YouTube URL.
