---
name: ui-feedback-toasts
description: Timing recipes for toasts, announcement banners, warning messages, count-up counters and attention loops. Use when a screen needs transient feedback (reward received, error, warning, currency change).
---

# UI feedback recipes

Values read from knife-tower code (report 07, VERIFIED); soft defaults, keep the feel consistent across a game.

| Item | Recipe |
|---|---|
| Count-up | on `DataValue.OnValueChanged` lerp the shown value 0.7 s, OutCubic, unscaled; compact K/M/B text; kill the tween on destroy; no Update |
| Pulse on receive | bar scale pulse 0.05 s OutQuart per flying coin |
| Announcement banner | 800x50 strip at y +260; fade in 0.3 OutSine, hold ~4 s, fade out 0.3; text pulse 1.1 over 0.15; message queue with a CancellationToken |
| Warning toast | fade in 0.25 OutBack, short blink, hold 2.5 s, fade out 0.35 InSine; ignore new calls while showing; clear on scene return |
| Toast text | static `Push(msg)`: scale 0.25, fade 0.35, move Y 0.4, hold 0.5, fade out 0.9 (Linear); single pooled instance |
| Attention loop | shake Z (freq ~24) then rest ~1.1 s, or scale yoyo InOutSine; primary CTA only; stop on disable |
| Fly-to currency | see `currency-spread-fx` (verify numbers there) |

Rules: texts through localization (`ui-localization`); cancel the previous message with a token before starting another (`async-cancellation`); never stack three toasts; spawn fly items in the overlay container; pool repeated items (`pool-everything`).
