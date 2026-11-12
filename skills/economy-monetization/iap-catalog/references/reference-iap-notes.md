# Reference-game IAP notes

Facts from the studio's reference game (read-only study, verified by code). Use as seeds, not law.

- **Single grant point.** One receiver (`Receive(product)`) switches on payout subtype and is the ONLY place that grants items. Ownership is stored by BASE product id (`Dictionary<string, DataValue<int>>`) plus a total purchase count.
- **No double grant.** A static processed-transaction set (`TryMarkTransactionProcessed(txId)`: first caller wins) protects against two listeners (codeless button + programmatic purchase). Programmatic purchases also dedupe pending requests by base id.
- **Restore is silent.** On every product fetch, each non-consumable's entitlement is checked; fully entitled and local count 0 means grant once. The visible "restore" button in the reference only shows a 3 s spinner. Stores expect a visible control, so a studio game adds a Settings row that calls the real restore.
- **Funnel logs.** Click logs `payment_start`; success is logged ONCE in the store listener callback (after server validation when used), never from buttons or purchase callbacks. If validation fails, no success event or revenue is logged: monitor it.
- **Price variants.** A remote JSON maps base id to a suffixed id (`<base>.<variant>`); resolve and de-resolve ids in one catalog class; ownership always by base id.
- **Subscriptions.** Refresh from the store on every resume plus an expiry timer; the refresher object belongs in the persistent root prefab, not created at runtime.
- **Editor.** The listener body is device-only; simulate in the Editor with a fake-purchase debug component rather than shortcuts that skip the receiver.
- **Two ads-removed flags** (data flag and SDK flag) both get set by the remove-ads payout.
