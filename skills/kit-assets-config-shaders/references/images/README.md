Provenance: generic sprites sampled from the Knife Tower style reference kit (catalog group p5_assets_kit). Art is for matching import settings and structure only; re-author the art for a new game. Paths below are relative to the reference project's Assets folder.


29 PNG files, all <= 132 KB (about 742 KB on disk). Source root: KT `Assets/` (read-only). All are Sprite (2D and UI) textures: textureType 8, spriteMode 1 (Single), PPU 100, alphaIsTransparency 1, unless noted. Border = `spriteBorder` (left, bottom, right, top) from the .meta. Use Image Type = Sliced where a border exists. The art is KT's own style; re-skin before shipping a different game.

| File | Source (under KT Assets/) | Size px | Border L,B,R,T | Use |
|---|---|---|---|---|
| Hand.png | _Game/Prefabs/Quest/Hand.png | 134x127 | none | tutorial / quest pointer hand |
| T_Arrow.png | _Art/2D/GUI/v1/Other/T_Arrow.png | 449x448 | none | big arrow (guide, conveyor) |
| Arrow.png | _Art/2D/GUI/v1/Settings/Arrow.png | 141x152 | none | small arrow / dropdown |
| bg_popup.png | _Art/2D/GUI/_Updated/v2/UI_shop-assets/bg_popup.png | 1517x715 | 44,42,45,55 | 9-slice popup board |
| bg_bar1.png | .../_Updated/v2/UI_shop-assets/bg_bar1.png | 22x812 | 10,14,10,14 | tall dark bar / list background |
| bg_bar2.png | .../_Updated/v2/UI_shop-assets/bg_bar2.png | 22x73 | 10,10,10,10 | currency / label plate |
| btn_on.png | .../_Updated/v2/UI_shop-assets/btn_on.png | 155x106 | 18,28,17,21 | tab / toggle ON |
| btn_off.png | .../_Updated/v2/UI_shop-assets/btn_off.png | 155x106 | 21,34,20,25 | tab / toggle OFF |
| btn_buy_cup.png | .../_Updated/v2/UI_shop-assets/btn_buy_cup.png | 250x94 | 11,24,11,14 | price button |
| btn_equipped.png | .../_Updated/v2/UI_shop-assets/btn_equipped.png | 250x94 | 15,24,14,18 | equipped-state button |
| Btn_Common.png | .../_Updated/v3/UI_Frame/Btn_Common.png | 136x140 | none | rarity item tile (Common). Siblings Uncommon..Divine exist in KT, not copied |
| QuestionMark.png | .../_Updated/v3/UI_Frame/QuestionMark.png | 43x92 | none | locked / unknown item mark |
| frame_common.png | .../_Updated/v5/frame_common.png | 341x630 | none | rarity card frame (Common). Others: uncommon, rare, epic, legendary, mysthic |
| frame_epic.png | .../_Updated/v5/frame_epic.png | 341x630 | none | rarity card frame (Epic) |
| frame_lock.png | .../_Updated/v5/frame_lock.png | 198x198 | none | locked slot |
| frame_plus.png | .../_Updated/v5/frame_plus.png | 198x198 | none | add / empty slot |
| bg_black.png | .../_Updated/v5/bg_black.png | 87x51 | 15,14,14,13 | dark rounded plate (badge / toast background) |
| level_bar.png | .../_Updated/v3/UI_Paint/level_bar.png | 546x83 | none | progress bar background |
| level_fill.png | .../_Updated/v3/UI_Paint/level_fill.png | 538x73 | none | progress fill (Image Filled) |
| green_bar.png | .../_Updated/v6/Jackpot/green_bar.png | 546x82 | none | progress bar BG (green) |
| green_fill.png | .../_Updated/v6/Jackpot/green_fill.png | 538x73 | none | fill (green) |
| red_bar.png | .../_Updated/v7/red_bar.png | 546x82 | 22,0,21,0 | progress bar BG (red) |
| red_fill.png | .../_Updated/v7/red_fill.png | 538x73 | none | fill (red) |
| ic_done.png | .../_Updated/v6/Jackpot/ic_done.png | 102x79 | none | claimed / done check |
| ic_wifi.png | .../_Updated/v3/UI/ic_wifi.png | 266x241 | none | no-internet popup icon |
| ic_cupbtn.png | .../_Updated/v3/UI/ic_cupbtn.png | 98x82 | none | meta-currency icon on a button |
| ic_sale.png | .../_Updated/v7/ic_sale.png | 148x143 | none | sale / offer badge |
| btn_close.png | .../_Updated/v6/Jackpot/btn_close.png | 97x93 | none | popup close button |
| T_Glow.png | _Art/3D/VFX/Texture/T_Glow.png | 256x256 | none | soft glow particle texture (textureType 0 Default, not a Sprite) |

Pitfalls: bg_bar1 (22x812) and bg_bar2 (22x73) are thin strips: keep Image Type Sliced, never Simple. Fill sprites are not sliced; drive them with Image.fillAmount (Filled, Horizontal) over the matching *_bar.
