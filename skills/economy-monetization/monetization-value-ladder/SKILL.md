---
name: monetization-value-ladder
description: "Price/reward design for free-to-play mobile games: two options gem + reward, 1-3 rewarded-video route that feels like the best deal, escalating cash sinks, IAP packs, honest-offer guardrails. Use when pricing items, designing shop cards, rewarded placements, gem/cash faucets or IAP products."
triggers: gia, reward, rewarded, gem, iap, monetize, monet, starter pack, shop, ecpm, quang cao, bay tam ly, neo gia, price anchor
---

# Monetisation value ladder

Goal: revenue from rewarded eCPM + IAP without breaking feel. Gems = premium currency (earned slowly, bought by IAP). Everything sellable has: gem price (anchor), a 1-3 rewarded-video route (the best-feeling deal), and, for packs, an IAP route.

Rules
- Two options per item, side by side: GEM at a MODERATE fair price (never inflated) and REWARD (1-3 videos); most players pick reward and that is fine. One IAP pack ~ one week of rewarded-video value (size packs by that equivalence). Reward route: <= 3 videos per item (common 1, mid 2, premium 3), visible progress "1/2" with icon-left chip, progress persists, value shown before the ad, granted after.
- Gem faucets deflated: free player ~25-40 gems/day; ads are the fast free route, IAP the instant one. Cash sinks scale with progress (escalating, proportional) so cash never inflates; "WATCH = +N cash" chip when the player is short.
- Pack ladder: bigger pack = more gems per unit, best-value tag; starter pack saves time, never gates content that videos could reach.
- Placements: opt-in, at natural moments, never mid-action/FTUE; log offer + claim with placement id (`ad_reward_offer/claim`), IAP `iap_start/iap_success`.
- Honesty: no fake discounts/countdowns/scarcity, truthful odds, parental gate before money, no guilt copy, owner supplies SKUs/ad ids.
- Verify with the economy simulator (pacing +-5 %) and per-placement funnel numbers; keep a project doc with the concrete table (project contract), never in this skill.

Related: `economy-progression-design`, `ads-popup-flow`, `monetization-integration`, `iap-catalog`, `ui-icon-text-everywhere`.
