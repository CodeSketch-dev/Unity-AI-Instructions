---
name: recipe-gacha-box
description: "Gacha box recipe: box asset with weighted rewards, price deducted before the open animation, single-instance popup, events. Use when a GDD sells random boxes."
---

# Recipe: gacha box

- `Gacha_Box_Asset { name, rewards[{item, weight}], price, currency, prefab }`, registered in `Factory_Gacha`.
- Open flow: check wallet, deduct, roll by weight, play the open animation to the rolled result, grant the item and show duplicates handling from the GDD.
- Popup is a single-instance (guard against double taps); the open button is disabled until the wallet covers the price.
- Events `Event_Gacha_Box_Open` and `_Open_End`; analytics from the taxonomy.
- The weights are the designer's; shown odds equal rolled weights. Grants go through the shared currency/item path with spread FX.
