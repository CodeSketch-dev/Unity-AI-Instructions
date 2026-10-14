---
name: recipe-fake-leaderboard
description: "Local fake leaderboard and share: seeded daily bots, real player row, weekly rewards, bot friends, share card. Use when a GDD has rankings or social features in a local-only game."
---

# Recipe: fake leaderboard and share

- `Leaderboard_Asset { id, statSource, botCount, refresh }`. Bots are generated from a seed (day index plus board id): name pool, avatar from the skin list, score spread around the player's stage. The board is stable within a day and changes daily; bots tick up slowly in-session.
- The player row uses the real stat with a realistic rank; weekly reset pays rewards from `Data_Leaderboard.lastPaidWeek`.
- Label it "Rankings", not a claim of real players.
- Friends substitute: bot friends list with a daily gift (rewarded ad doubles it); native share sheet with the store link; "invite" quests are honor-system with a small reward.
- Share card: render result stats to a texture and share it.
- GDD supplies boards, stats, bot count, rewards.
