# Commit message format

## Good (model)
```
[v1.22]: Ads: gate native by tutorial and level

- Ads_NativeGate: no native before the tutorial is completed, or below level 20 (reason: overlap with the focus message)
- Ads_NativeFlow: close the native when its popup closes in the first 300 s; value comes from remote config
- Data_Settings: add NativeCloseSeconds default 300
```
Alternative for non-release work: `refactor(shop): split Shop_Page into page and item`, `fix(ads): retry init after consent failure`.

## Rules
1. Subject <= 72 chars, imperative, says WHAT; body says WHY and lists touched classes.
2. `[vX.Y]` is the version in progress (from the one version source); omit it on pure tooling/docs commits if using the conventional form.
3. Separate commits for: mass rename/move, dead code/asset removal, generated refresh, ignore-file edits, dependency/package changes, balance tweaks (`TWEAK:` prefix in the body).
4. Marker words: `ATTENTION:` for a risky change reviewers must read; `BREAKING:` for save-data or API changes (include the migration).
5. Never commit: `.`, `update`, `doing`, `wip`, `fix` alone; secrets; Library/Temp; large generated output.
6. Co-author or attribution lines follow the project's rule; keep them at the end.

## Anti-examples seen in a real history
`.` (73 commits), `update`, `doing`, `Build aab` (no version, no content), the same `[v1.5]` used in May and July.

## Enforcement
`scripts/commit-msg` rejects bad subjects locally; CI repeats the check for pull requests. Hooks are opt-in per clone (`core.hooksPath`), so also document the one-line install in onboarding.
