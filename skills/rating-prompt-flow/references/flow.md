# Flow, data and popup tree

## Gate and persistence (generic excerpt)
```csharp
public static class RatingHelper
{
    public static bool CanShow()
    {
        if (Data_Rating.RatingDone.Value) return false;
        if (Data_Rating.RatingInThisSession.Value) return false;      // non-persisted flag
        if (!Data_Tutorial.IsCompleted.Value) return false;
        if (Data_Rating.AskCount.Value >= MAX_ASKS_PER_VERSION && Data_Rating.LastAskVersion.Value == Application.version) return false;
        if (Data_Rating.Sessions.Value < MIN_SESSIONS) return false;
        return (DateTime.UtcNow - Data_Rating.LastAskUtc).TotalHours >= MIN_HOURS_BETWEEN;
    }

    public static void Show()
    {
        if (!CanShow()) return;
        Data_Rating.RatingInThisSession.Value = true;
        PopupManager.Create(Factory_Prefab.RatingPopup);               // framework popup manager
    }
}
```
Persisted-vs-session trick: in the data block, persisted values use `??=` in `Init`; the session value is re-created with `new DataValue<bool>(false)` on every load so it never carries over.

## Popup tree (typical)
```
Rating_Popup (Popup + CanvasGroup)
 +- Board
     +- Text_Title            localized ("Enjoying the game?")
     +- Stars or two buttons  Btn_Good, Btn_Bad (press anim + sfx)
     +- Btn_Close
```

## Store calls
- Android good path: `AppStore.Review()` after `AppStore.Init()` was called once at popup start (pre-warm).
- iOS good path: `AppStore.Review(appStoreId)`.
- Both fall back to the store page URL.
