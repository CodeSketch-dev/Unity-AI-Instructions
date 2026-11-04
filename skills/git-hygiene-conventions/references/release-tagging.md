# Release tagging and versioning

- Version source: Unity `bundleVersion` + Android `bundleVersionCode` (and iOS build number), set by one batch method from arguments (`house-editor-tools` sample `Build_Version`; full pipeline `unity-batch-build`). A config asset or json may mirror it for runtime display; the settings are written FROM the one source.
- Tag every candidate build: `git tag -a v1.22.0 -m "AAB 22, notes: <first lines>"` on the exact commit built. Tags are created only on the owner's request; pushing tags is part of that request.
- Keep a short checklist per tag: compile, EditMode counts, missing-reference check, clean-clone check, device smoke (FPS, banner/native/loading overlay), low-end profile, size gate (`mobile-build-release`).
- Release notes: `python -I scripts/release_notes.py --repo . --from v1.21` grouped by area; edit by hand for the store text.
- Bug reports quote the version string; a reused string breaks this, so the build number must increase monotonically.
- Risky features ship dark: a remote flag defaults off, the next tag enables it; the flag name and default are in the commit body.
- Cadence reference: v1.4 -> v1.21 in 7.5 months (about every two weeks) worked when builds were automated; manual builds from the Editor (23 build days) are the time sink to remove.
- Hotfix: branch from the tag, fix, tag `vX.Y.(Z+1)`, merge back to trunk.
