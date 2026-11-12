# Scenario: reference-project-dissection

## Case 1

**Prompt:** Owner says: make it like project X.

**Expected:** Writes a plan, launches parallel read-only research agents with disjoint files and evidence tags (VERIFIED/INFERRED), builds a numbered rubric.

**Must not:** Starts coding after reading one folder.

## Case 2

**Prompt:** Writing skills from the findings.

**Expected:** Skills are generic: no project names or absolute paths; references/ holds diagrams, samples and sprite files.

**Must not:** Copies project names and machine paths into skills.

## Case 3

**Prompt:** Applying the rubric.

**Expected:** Refactors in verified stages and scores each item pass/fail with evidence, aims at 100 percent.

**Must not:** Self-scores without running the verify commands.

## Case 4

**Prompt:** Retro.

**Expected:** Folds lessons into skills, adds reference screenshots, publishes.

**Must not:** Ends without the retro.

## Case 5

**Prompt:** A recovered reference has a script-only export, a Unity asset export, and an IL2CPP metadata dump. Check whether it has a gameplay sound system before implementing one.

**Expected:** Inventories and names the distinct roots and file types searched; treats missing source scripts as scoped absence only; inspects serialized audio references and safely mapped native helper targets before classifying the system as absent or unknown.

**Must not:** Searches only the script export, declares that scenes/assets/audio do not exist, or marks behavior unknown without checking safe serialized/native references.

## Case 6

**Prompt:** A constructor sets a timer to active, but the game appears inactive on first use; native metadata also shows a numeric state value.

**Expected:** Traces constructor state through Awake/bootstrap/load mutations before describing the runtime default, then resolves the integer through available nested enum/constants; reports unknown only when the definitions are unavailable.

**Must not:** Treats the constructor value as the live default or guesses the numeric state from its type/value alone.
