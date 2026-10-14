# Scenario: factory-singleton-template

**Prompt:** Add a Factory for pet configs with a dictionary by id.

**Expected:** Creates Factory_Pet : ScriptableObjectSingleton (Serialized variant only if Odin dict needed), OnInitialize validation, asset under Resources/<Root>/ScriptableObjectSingletons with full-name filename, fields assigned via MCP.

**Must not:** Hand-write .asset YAML or leave the asset missing (null in builds).
