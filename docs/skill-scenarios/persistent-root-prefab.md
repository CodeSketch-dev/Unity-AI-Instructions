# Scenario: persistent-root-prefab

## Case 1

**Prompt:** Add a new manager the whole game needs (e.g. a daily-reward ticker).

**Expected:** Makes it its own prefab nested under the persistent root Manager child, scene-authored, with init order checked against boot-order.md.

**Must not:** Creates it with new GameObject/AddComponent at runtime or puts it only in one scene.

## Case 2

**Prompt:** Press Play directly in a gameplay scene and a duplicate root appears.

**Expected:** Explains the second copy self-destroys via the singleton Awake, guards code after base.Awake with Instance != this, places the root in every playable scene.

**Must not:** Deletes the root from the scene or removes the singleton guard.

## Case 3

**Prompt:** Build the root for a new project.

**Expected:** Runs the installer or installer-spec steps: EventSystem, Manager (pool, IAP), Canvas, Canvas_Popup, Transition with the sort orders from canvas-table.md; verifies in Play.

**Must not:** Builds canvases at runtime or invents sort orders.

## Case 4

**Prompt:** Popups render under the HUD.

**Expected:** Checks canvas sort orders and the popup canvas against the table, fixes in the prefab, re-verifies in Play.

**Must not:** Raises one popup order by hand or reparents at runtime.
