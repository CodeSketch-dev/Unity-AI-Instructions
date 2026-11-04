# Daily popup page (horizontal list) - reference structure

```
Daily_Login_Popup  (page script on ROOT) + Popup + CanvasGroup
  fields: [SerializeField] ScrollRect _scrollRect; [SerializeField] Daily_Login_Item _itemPrefab;
  Root > header (175 high) + horizontal ScrollRect of cards
Daily_Login_Item  431x617  (Button + press + sfx + item script)
  5 state visuals: normal, claimable, missed (black), claimed ... toggled by SetActive
  thumbnail 235x235, recover button 325x125
```
Code skeleton (see `page-item-sample.cs.txt`): reuse authored children, else `Instantiate(_itemPrefab, _scrollRect.content)`; `item.Initialize(this, config, i)`; refresh in `OnEnable`; a focus tween scrolls to today (0.5 s smoothstep) with a stored `Tween` handle stopped in `OnDisable`; cancel tokens in `OnDisable/OnDestroy`; debug `Update` input only under `#if UNITY_EDITOR`.
