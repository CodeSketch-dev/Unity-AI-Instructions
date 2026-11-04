# Scenario: project-structure-layout

## Case 1

**Prompt:** Start a new game project: create the folder and script layout.

**Expected:** Creates Assets/_Game/Scripts/{Core,Data,Editor,Event,Factory,Logic,Utilities}, Logic/<Feature>/ and Logic/Minigame/<Name>/<XXX>_<Part>.cs, namespace Game, one type per file, no first-party asmdef, audits with the layout script.

**Must not:** Adds a runtime asmdef without references, per-game namespaces, a feature folder at the _Game root, or near-duplicate folders (Audio/Audios).

## Case 2

**Prompt:** A script file holds two MonoBehaviours and a prefab shows Missing Script.

**Expected:** Splits so file name == class name, one type per file, repairs the prefab reference through GUID-safe migration, re-counts missing scripts.

**Must not:** Renames the file only, or leaves the second class in the old file.

## Case 3

**Prompt:** Add editor-only code that uses UnityEditor.

**Expected:** Places it in an Editor folder (namespace Game.Editor) or guards with #if UNITY_EDITOR; no UnityEditor use in runtime files.

**Must not:** Puts UnityEditor calls in Logic/ without a guard or creates an editor asmdef without need.

## Case 4

**Prompt:** Where do tests go and how are they compiled?

**Expected:** Uses Tests/EditMode and Tests/PlayMode test asmdefs as the only allowed first-party asmdefs.

**Must not:** Says tests need no asmdef, or turns all code into asmdefs for test access.

## Case 5

**Prompt:** Add a second Quality level for low-end phones.

**Expected:** Keeps ONE Quality level and points to the runtime device tier policy.

**Must not:** Creates per-tier Quality levels or swaps the URP asset at runtime.
