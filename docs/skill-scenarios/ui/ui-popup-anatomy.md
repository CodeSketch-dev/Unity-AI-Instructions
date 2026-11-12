# Scenario: ui-popup-anatomy

**Prompt:** Add a confirm-purchase popup.

**Expected:** Popup > Root > Scale > Board > Btn_Close tree, no Canvas, created via PopupManager.Create, Escape closes top, scale/fade modules, destroyed on close.

**Must not:** Instantiate into a Canvas or add per-screen Back handlers.
