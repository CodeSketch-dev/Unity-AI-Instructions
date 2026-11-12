# Scenario: pool-everything

**Prompt:** Add a hit spark effect when the enemy takes damage.

**Expected:** Prefab with PoolPrefabItem, Pool_Fx_HitSpark config in Configs/Pool, PoolPrefabGlobal.Get then position, self-release, unparent before release.

**Must not:** Instantiate/Destroy per hit or create another pool class.
