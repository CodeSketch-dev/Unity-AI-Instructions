# Scenario: ui-page-item-prefab

## Case 1

**Prompt:** Build a daily-reward popup with 7 cards.

**Expected:** Page script on the prefab root, typed item prefab reference, items reuse authored children then Instantiate into the ScrollRect, item.Init(config), state by SetActive children.

**Must not:** Builds cards with new GameObject or tweaks layout at runtime.

## Case 2

**Prompt:** Every item button needs feedback.

**Expected:** Item root has Button + press tween component + button sfx component + item script, audited for exactly one of each.

**Must not:** Adds ad hoc AudioSource or skips press animation.

## Case 3

**Prompt:** Subscriptions on a shop page.

**Expected:** Subscribes in OnEnable, unsubscribes in OnDisable, refreshes on enable, cancels tokens and stops tweens.

**Must not:** Leaves static-bus listeners alive after close.

## Case 4

**Prompt:** Another minigame needs the same shop.

**Expected:** Creates its own page prefab per minigame following the consistency contract, shares item components.

**Must not:** Nests or variants the other minigame page prefab.
