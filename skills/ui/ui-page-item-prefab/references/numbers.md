# Numbers (reference UI, 1920x1080, ScaleWithScreenSize, Expand, match 0)

| Token | Value |
|---|---|
| Popup open/close | 0.1 / 0.1 s on most; big dialogs 0.3 / 0.2; a few instant 0.02 |
| Popup scale tween | 0.3 -> 1, OutBack (or Linear), target = Board, not the stretch root |
| Dim | black alpha 0.94 (most); tap outside does NOT close |
| Press anim | scale 0.9, 0.1 s, OutQuad, unscaled |
| Attention pulse (primary CTA only) | 1.05, 0.75 s, InOutSine yoyo loop |
| Button sizes | 347x116, 275x102, 280x110, 325x125, 200x80; close 97x93 / 100x100 |
| Icon HUD button | hit area 167x162, plate 155x106, icon 111x103 |
| Tab | 222x82, tab column 285 wide |
| Header | 1920x175, back 103x107 |
| Boards | settings 800x650, small 528x435, rating 525x370, large ~1146x754 |
| Cards | shop item 266x267, daily 431x617, pack 428x595 |
| Dot | 40x41, top-right (-2..-10, -4..-9) |
| Font sizes | titles 72-90, headings 42-58, button text 36-58 auto, labels 28-38; autosize min 18 (10 for tight plates) |
Counts: 27 popup prefabs share the shell (background + scale animation); 33 of 33 popup sfx slots empty; 91 prefabs carry the press component.
Copy structure, not fractional values; the reference mixes inconsistent sprite names and manual sizes.
