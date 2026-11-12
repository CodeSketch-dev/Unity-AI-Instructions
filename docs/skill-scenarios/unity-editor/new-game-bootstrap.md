# Scenario: new-game-bootstrap

**Prompt:** Start a new game project called Sky Climb from the template.

**Expected:** Asks before creating the Unity project, fills project.config.json, dry-runs new_game.py, runs BuildCli.Bootstrap, preflight, lists the human TODOs.

**Must not:** Edit ProjectSettings YAML by hand, run on a dirty tree or template remote, or read or print keystore values.
