# Layout audit: commands and thresholds

Run from the project root. Budgets are rubric items (see `staged-refactor-playbook/references/conformity-rubric.md`).

| Check | Command | Budget |
|---|---|---|
| Whole layout audit | `python -I <skill>/scripts/layout_audit.py --root .` | 0 FAIL |
| `_Game` top level | `ls Assets/_Game` | only the allowed buckets (Audios Configs Fonts Localization Materials Prefabs Resources Scenes Scripts Tests Textures) |
| Source art roots | `ls Assets \| grep -i art` | exactly `_Art` |
| Scripts buckets | `ls Assets/_Game/Scripts` | Core Data Editor Event Factory Logic Utilities |
| Prefabs in Resources | `find Assets -path '*Resources*' -name '*.prefab'` | none |
| Near-duplicate folder names | `ls Assets/_Game` compared case-insensitive and singular/plural | none |
| File == type | audit script N04 | 0 |
| One type per file | audit script N05 | 0 |
| Editor leaks | audit script N09 | 0 |
| Long files | `find Assets/_Game/Scripts -name '*.cs' \| xargs wc -l \| sort -n \| tail` | 0 above 400 without a documented exception |
| asmdefs | `find Assets/_Game -name '*.asmdef'` | only with real references; 2 test asmdefs |
| New folder ignored by git? | `git check-ignore -v Assets/_Game/Scripts/Logic/<Feature>/x.cs` | no output |
| Generated folders tracked? | `git ls-files Assets \| grep -iE 'graph\|cache\|generated~'` | none |

Loop for every new feature folder:
```
git check-ignore -v <new file path> && echo IGNORED-FIX-THE-RULE
```
Add a negation after the rule (`!Assets/_Game/.../Demo/`) and commit it with the reason.

Random-find test (maintainability): pick 10 features at random; each must be found by name in under a minute and have one entry class named after it.
