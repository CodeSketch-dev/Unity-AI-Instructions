# Scenario: config-and-factory-authoring

**Prompt:** Add 10 new weapon entries with a registry lookup by id.

**Expected:** One SO per entry under Configs/<Feature>, factory array + dictionary in OnInitialize with duplicate/null errors, runs config_registry_audit.

**Must not:** Silently overwrite duplicate ids or hand-write assets.
