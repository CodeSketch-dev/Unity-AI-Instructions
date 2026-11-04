# Not in the reference game: build as new work when needed

The reference study found none of these. They are Studio additions or Optional modules; implement behind a facade, remote-flagged, and fail open (never block play because a service is down).

## Force update / minimum version
Remote int `minSupportedVersion`; compare with the numeric build part of `Application.version` (keep a fixed `1.N` shape). Below the minimum: blocking popup with one "Update" button that opens the store page. Absent or unparsable config = no block. Separate from the "hide ads during store review" gate.

## Crash / error reporting
Crashlytics (or equivalent) behind a `CrashReporting` facade; set user and build keys; hook `Application.logMessageReceived` for exceptions only (not every log); consent aware. Verify with a forced non-fatal in a Development build and see it in the dashboard. Not active in Editor play.

## Local push (retention)
Check the installed SketchEngine `Notification` module first (define `SKETCHENGINE_NOTIFICATIONS`; the shipped component cancels scheduled items when the app regains focus). Schedule on pause (daily reward ready, timers done); ask the OS permission after a positive moment, not at launch.

## Explicit restore
A Settings row that calls the real store restore. The reference restores non-consumables silently on product fetch; its restore button is only a spinner. Stores expect a visible control that works.

## Settings legal rows
Privacy policy and terms URL, manage consent (when UMP applies), contact mailto, rate, version text.

## Offline earnings (idle genres only)
Last-active UTC stamp on pause, capped hours, welcome-back popup with claim by tap, optional rewarded multiplier; see `recipe-retention-timers`. The reference has none.

## Cloud save / server time (conditional)
Only if progress or timed rewards have real value. Cloud save: one blob per player, last-write-wins plus a manual conflict choice. Server time: one lightweight request at start; fall back to the device clock flagged "unverified". The reference uses the device clock everywhere, so moving the phone clock forward claims every daily reward.

## Share / invite (conditional)
Native share sheet through a plugin behind a facade; reward at most once per day.
