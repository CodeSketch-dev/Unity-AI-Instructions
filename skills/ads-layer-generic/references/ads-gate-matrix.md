# Ads gate matrix (data-driven)

Lesson from the reference game's git history: ads gating was discovered piecemeal. Native ads were patched 25+ times (tutorial gate, event-scene gate, level gate, popup-close guard, SDK init order, a device-only close bug) and removed and re-added once. Specify the whole matrix up front, keep it as data, make every number remote-configurable from the first commit, and test it table-driven.

## 1. Matrix template (fill one row per context; "-" = no restriction)
| Format | Context (scene / state) | Tutorial done? | Min level | Popup open? | Since first install | Since last same ad | Since last native/inter | Remove-ads / VIP | Result |
|---|---|---|---|---|---|---|---|---|---|
| Interstitial | natural break (result, popup close) | yes | - | no | >= start delay | >= spacing | >= app-open spacing | blocked | allow |
| Interstitial | tutorial / first session | no | - | - | - | - | - | - | block |
| Rewarded | any | - | - | - | - | - | - | allowed (not removed) | allow if ready, else toast |
| Banner | home, gameplay, after scene load | - | - | - | >= start delay | - | - | blocked | show |
| App open | resume / cold start | yes | - | no | >= start delay | - | >= 30 s after interstitial | blocked | allow |
| Native (in-rect) | home | yes | - | popup shifts | >= start delay | >= native cooldown | - | blocked | show |
| Native | event or independent scene | per scene flag | - | - | - | - | - | blocked | per row |
| Native | popup closes | - | - | - | within guard window | - | - | - | hide native with popup |

The tutorial gate may also be satisfied by a progression level above a skip threshold; keep that threshold as a named constant and a remote value.

## 2. Config shape
One serializable config (local asset, overlaid by remote): start delays per format, spacings, native cooldown, native close guard seconds, per-placement `{ enable, startDelay, spacing, adsBreak }`, per-scene native allow flag, tutorial skip level, store-review hide flag. The policy class is pure C# (no provider types) so it can be unit-tested.

## 3. Table-driven EditMode test (excerpt)
```csharp
[TestCase(Fmt.Interstitial, "Result", true,  120,  90,  false, ExpectedResult = true)]
[TestCase(Fmt.Interstitial, "Result", false, 120,  90,  false, ExpectedResult = false)] // tutorial
[TestCase(Fmt.Interstitial, "Result", true,   30,  90,  false, ExpectedResult = false)] // start delay
[TestCase(Fmt.Interstitial, "Result", true,  120,  20,  false, ExpectedResult = false)] // spacing
[TestCase(Fmt.Interstitial, "Result", true,  120,  90,  true,  ExpectedResult = false)] // ads removed
[TestCase(Fmt.Rewarded,     "Home",   false,   0,   0,  true,  ExpectedResult = true)]  // rewarded survives remove-ads
public bool Gate(Fmt format, string context, bool tutorialDone, int sinceInstall, int sinceLast, bool adsRemoved)
{
    var state = new AdsState { TutorialDone = tutorialDone, SecondsSinceInstall = sinceInstall,
                               SecondsSinceLast = sinceLast, AdsRemoved = adsRemoved };
    return AdsPolicy.IsAllowed(format, context, state, AdsConfig.Defaults);
}
```
Add one test row per matrix row plus the boundary values (exactly equal to the delay). Run with `test-evidence-review` and report PASS/SKIP counts.

## 4. Real-device smoke checklist (cannot be replaced by the Editor mock)
1. Fresh install, airplane mode, then online: no ad before the start delay; banner appears after it.
2. Interstitial at a result: counted spacing, `onClosed` fires exactly once, the game resumes (no frozen timeScale).
3. Rewarded: complete, close early, no fill (toast), airplane mode.
4. Native: shows in its slot, shifts the popup, closes when the popup closes, closes when the loading bar finishes; HideNative actually hides the native view (an Editor-only mock hid a real bug).
5. Banner vs tutorial focus message and banner vs native overlap: reserved safe areas in prefabs.
6. Consent flow on first launch; deny it; ads still initialize.
7. Remove-ads purchase hides the banner immediately.
8. Low-end device: no ANR when native loads (main-thread rule).

## 5. Pitfalls
- Placement names are config keys and log strings: renaming an enum member silently drops its remote config.
- A skip-cooldown flag must still obey the first-install delay.
- Two ownership flags for ads removal (purchase and VIP): set both from the one purchase receiver.
- Never put a real SDK key in the repo or in a skill; each app owns its keys in ignored config.
