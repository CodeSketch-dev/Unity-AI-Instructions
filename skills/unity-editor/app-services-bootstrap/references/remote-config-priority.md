# Remote config priority

Order the reference resolves a value (first present wins):
1. studio server config delivered at session start (cached locally for the next launch)
2. Firebase-style remote config, once loaded
3. local config asset in `Resources` (a ScriptableObject mirror of every field)
4. field initializers in the config class (always valid defaults)

Rules
- Add fields only in one game-specific partial class with sane defaults; mirror them in the local asset.
- Fetch once at startup (minimum fetch interval about 1 s, timeout about 10 s) and raise one "loaded" event; listeners (minigame ordering, IAP price variants) subscribe to it.
- Never read a remote value that changes layout or ordering before the loaded event; design every gate to be safe with defaults on a cold start.
- A malformed JSON field is skipped, not fatal.
- A "test mode" that zeroes cooldowns exists in the reference; never call it in release.
- Ship risky features dark: a remote flag default-on with a bypass, or default-off, then enable remotely (the internet-required flag and the native close guard were both added this way).
- Config is read many times per frame by gates: keep fields plain, no allocation.
