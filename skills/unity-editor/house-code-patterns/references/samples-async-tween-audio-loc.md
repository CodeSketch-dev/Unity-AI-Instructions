# Samples: async, tween, audio, localization

## CancelToken (one per owner, cancel before replace)
```csharp
using Cysharp.Threading.Tasks;
using SketchEngine.Core.Async;
CancelToken _cancel;
void StaticBus_Event_AI_Allowed(Event_AI_Allowed e)
{
    _cancel?.Cancel();
    _cancel = new CancelToken();
    TaskSpawn(_cancel.Token).Forget();
}
async UniTask TaskSpawn(System.Threading.CancellationToken token)
{
    if (token.IsCancellationRequested) return;
    await UniTask.Delay(System.TimeSpan.FromSeconds(3f), cancellationToken: token);
}
void OnDisable() { _cancel?.Cancel(); _cancel = null; }
```
Async methods prefixed `Task`, `.Forget()` at the call site, token into every delay/yield, no `async void`, no `Task.Run` for Unity work.

## PrimeTween handle
```csharp
Tween _focusTween;
void StartFocus(float from, float to)
{
    StopFocus();
    _focusTween = Tween.Custom(this, from, to, 0.4f, (self, v) => self.OnFocusUpdate(v), Ease.OutQuad);
}
void StopFocus() { if (_focusTween.isAlive) _focusTween.Stop(); _focusTween = default; }
void OnDisable() => StopFocus();
```
Press scale is the `UIPressPrimeTween` component (down 0.9 over 0.1 s, OutQuad, unscaled time).

## Audio
```csharp
[SerializeField] AudioConfig _sfx;      // asset in Configs/Audio/Sfx
void Hit() => AudioManager.Play(_sfx);
```
Factory form: `public static AudioConfig SfxLevelUp => Instance._sfxLevelUp;`.

## Localization
Static label: add the localize component (key dropdown) on the TMP object; it applies in `Awake`, re-applies on locale change and unsubscribes in `OnDestroy`. Dynamic strings: `Localization_Factory.Get(key, args)` (returns the key when missing). Never hard-code UI strings.
